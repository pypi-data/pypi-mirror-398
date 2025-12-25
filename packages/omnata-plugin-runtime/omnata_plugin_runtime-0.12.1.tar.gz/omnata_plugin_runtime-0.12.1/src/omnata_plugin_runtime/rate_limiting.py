"""
Contains functionality for limiting http requests made by Omnata plugins
"""
from __future__ import annotations

import datetime
import re
import threading
from email.utils import parsedate_to_datetime
from logging import getLogger
from typing import Any, List, Literal, Optional, Dict, Tuple
import requests
import time
import logging
from pydantic import Field, model_validator, PrivateAttr, field_serializer
from pydantic_core import to_jsonable_python
from typing_extensions import Self
from .configuration import SubscriptableBaseModel
from .logging import logger, tracer
import pytz
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TimeUnitType = Literal["second", "minute", "hour", "day"]

HttpMethodType = Literal[
    "GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"
]


class HttpRequestMatcher(SubscriptableBaseModel):
    """
    A class used to match an HTTP request
    """

    http_methods: List[HttpMethodType]
    url_regex: str

    @classmethod
    def match_all(cls):
        """
        A HttpRequestMatcher which will match all requests.
        """
        return cls(
            http_methods=[
                "GET",
                "HEAD",
                "POST",
                "PUT",
                "DELETE",
                "CONNECT",
                "OPTIONS",
                "TRACE",
                "PATCH",
            ],
            url_regex=".*",
        )


class ApiLimits(SubscriptableBaseModel):
    """
    Encapsulates the constraints imposed by an app's APIs
    """

    endpoint_category: str = Field(
        "All endpoints",
        description='the name of the API category (e.g. "Data loading endpoints")',
    )
    request_matchers: List[HttpRequestMatcher] = Field(
        [HttpRequestMatcher.match_all()],
        description="a list of request matchers. If None is provided, all requests will be matched",
    )
    request_rates: List[RequestRateLimit] = Field(
        None,
        description="imposes time delays between requests to stay under a defined rate limit",
    )

    def request_matches(self, method: HttpMethodType, url: str):
        """
        Given the request matchers that exist, determines whether the provided HTTP method and url is a match
        """
        for request_matcher in self.request_matchers:
            if method in request_matcher.http_methods and re.search(
                request_matcher.url_regex, url
            ):
                return True
        return False

    @classmethod
    def apply_overrides(
        cls, default_api_limits: List[ApiLimits], overridden_values: List[ApiLimits]
    ) -> List[ApiLimits]:
        """
        Takes a list of default api limits, and replaces them with any overridden values
        """
        if overridden_values is None or len(overridden_values) == 0:
            return default_api_limits
        overrides_keyed = {l.endpoint_category: l.request_rates for l in overridden_values}
        for api_limit in default_api_limits:
            if api_limit.endpoint_category in overrides_keyed.keys():
                api_limit.request_rates = overrides_keyed[api_limit.endpoint_category]
        return default_api_limits

    @classmethod
    def request_match(
        cls, all_api_limits: List[ApiLimits], method: HttpMethodType, url: str
    ) -> List[ApiLimits]:
        """
        Given a set of defined API limits, return all those that match the request
        """
        return [api_limit for api_limit in all_api_limits if api_limit.request_matches(method, url)]

    def calculate_wait(self, rate_limit_state: RateLimitState) -> datetime.datetime:
        """
        Based on the configured wait limits, given a sorted list of previous requests (newest to oldest),
        determine when the next request is allowed to occur.
        Each rate limit is a number of requests over a time window.
        Examples:
        If the rate limit is 5 requests every 10 seconds, we:
         - determine the timestamp of the 5th most recent request
         - add 10 seconds to that timestamp
        The resulting timestamp is when the next request can be made (if it's in the past, it can be done immediately)
        If multiple rate limits exist, the maximum timestamp is used (i.e. the most restrictive rate limit applies)
        """
        logger.debug(
            f"calculating wait time, given previous requests as {rate_limit_state.previous_request_timestamps}"
        )
        if self.request_rates is None:
            return datetime.datetime.now(datetime.timezone.utc)
        longest_wait = datetime.datetime.now(datetime.timezone.utc)
        if (
            rate_limit_state.wait_until is not None
            and rate_limit_state.wait_until > longest_wait
        ):
            longest_wait = rate_limit_state.wait_until
        for request_rate in self.request_rates:
            if rate_limit_state.previous_request_timestamps is not None and len(rate_limit_state.previous_request_timestamps) > 0:
                previous_request_timestamps = rate_limit_state.get_relevant_history(request_rate)
                request_index = request_rate.request_count - 1
                if request_index > len(previous_request_timestamps) - 1:
                    continue # we have not yet made enough requests to hit this rate limit
                request_index = len(previous_request_timestamps) - 1
                timestamp_at_horizon = previous_request_timestamps[request_index]
                now = datetime.datetime.now().astimezone(datetime.timezone.utc)
                seconds_since_horizon = (timestamp_at_horizon - now).total_seconds()
                next_allowed_request = timestamp_at_horizon + datetime.timedelta(
                    seconds=request_rate.number_of_seconds()
                )
                if next_allowed_request > longest_wait:
                    longest_wait = next_allowed_request

        return longest_wait

def datetime_to_epoch_milliseconds(dt: datetime.datetime) -> int:
    return int(dt.astimezone(datetime.timezone.utc).timestamp() * 1000)

def epoch_milliseconds_to_datetime(epoch: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(epoch / 1000, tz=datetime.timezone.utc)

def datetimes_as_ints_encoder(obj):
    if isinstance(obj, datetime.datetime):
        return datetime_to_epoch_milliseconds(obj)
    return to_jsonable_python(obj)


class RateLimitState(SubscriptableBaseModel):
    """
    Encapsulates the rate limiting state of an endpoint category for a particular connection (as opposed to configuration)
    Importantly, we are very strict on all timestamps being timezone aware and UTC.
    Accuracy is critical for these calculations, so we raise errors early to ensure that we're not making mistakes.
    """

    wait_until: Optional[datetime.datetime] = Field(
        None,
        description="Providing a value here means that no requests should occur until a specific moment in the future",
    )
    previous_request_timestamps: Optional[List[datetime.datetime]] = Field(
        [],
        description="A list of timestamps where previous requests have been made, used to calculate the next request time",
    )
    # can't set this as a class variable because it's not serializable
    # TODO: probably shouldn't mix models with functionality like this
    _request_timestamps_lock: Optional[threading.Lock] = None

    @field_serializer('wait_until',when_used='always')
    def serialize_wait_until(self, value:Optional[datetime.datetime]) -> Optional[int]:
        # if a datetime is provided, convert it to epoch milliseconds
        if value is not None:
            return datetime_to_epoch_milliseconds(value)

    @field_serializer('previous_request_timestamps',when_used='always')
    def serialize_previous_request_timestamps(self, value:List[datetime.datetime]) -> List[int]:
        # if a list of datetimes is provided, convert them to epoch milliseconds
        return [datetime_to_epoch_milliseconds(ts) if ts else None for ts in value]


    # Combined root validator
    @model_validator(mode='after')
    def validate_datetime_fields(self) -> Self:
        # Handling wait_until
        wait_until = self.wait_until
        if isinstance(wait_until, int):
            self.wait_until = epoch_milliseconds_to_datetime(wait_until)
        elif wait_until and isinstance(wait_until, datetime.datetime):
            if wait_until.tzinfo is None:
                raise ValueError("wait_until must be timezone aware")
            elif wait_until.tzinfo != datetime.timezone.utc:
                raise ValueError("wait_until must be timezone aware and UTC")

        # Handling previous_request_timestamps
        timestamps = self.previous_request_timestamps or []
        if timestamps and isinstance(timestamps[0], int):
            self.previous_request_timestamps = [epoch_milliseconds_to_datetime(epoch) for epoch in timestamps]
        elif timestamps and isinstance(timestamps[0], datetime.datetime):
            if timestamps[0].tzinfo is None:
                raise ValueError("previous_request_timestamps must be timezone aware")
            elif timestamps[0].tzinfo != datetime.timezone.utc:
                raise ValueError("previous_request_timestamps must be timezone aware and UTC")
        
        return self

    def merge(self,other:RateLimitState):
        """
        Merges the other rate limit state into this one
        """
        if other.wait_until is not None and (self.wait_until is None or other.wait_until > self.wait_until):
            self.wait_until = other.wait_until
        if other.previous_request_timestamps is not None and len(other.previous_request_timestamps) > 0:
            self.previous_request_timestamps.extend(other.previous_request_timestamps)
            self.previous_request_timestamps.sort(reverse=True) # they should be sorted newest to oldest
    
    @classmethod
    def collapse(cls,state:Dict[int,Dict[str,Dict[str,RateLimitState]]],selected_sync_id:int,selected_branch_name:str) -> Tuple[Dict[str,RateLimitState],Dict[str,RateLimitState]]:
        """
        Given a dictionary of rate limit states, collapses them into a single state for all endpoints, and a single state for the selected sync_id and branch_name
        """
        result_all: Dict[str,RateLimitState] = {}
        result_this_branch: Dict[str,RateLimitState] = {}
        for sync_id in state.keys():
            for branch_name in state[sync_id].keys():
                if selected_sync_id == int(sync_id) and selected_branch_name == branch_name:
                    result_this_branch = state[sync_id][branch_name]
                for endpoint_category in state[sync_id][branch_name].keys():
                    if endpoint_category not in result_all:
                        result_all[endpoint_category] = RateLimitState()
                    result_all[endpoint_category].merge(state[sync_id][branch_name][endpoint_category])
        return (result_all,result_this_branch)

    def register_http_request(self):
        """
        Registers a request as having just occurred, for rate limiting purposes.
        You only need to use this if your HTTP requests are not automatically being
        registered, which happens if http.client.HTTPConnection is not being used.
        """
        if self._request_timestamps_lock is None:
            self._request_timestamps_lock = threading.Lock()
        with self._request_timestamps_lock:
            append_time = datetime.datetime.now(datetime.timezone.utc)
            if self.previous_request_timestamps is None:
                self.previous_request_timestamps = []
            self.previous_request_timestamps.insert(0, append_time)

    def prune_history(self, request_rates: List[RequestRateLimit] = None):
        """
        When we store the request history, it doesn't make sense to go back indefinitely.
        We only need the requests which fall within the longest rate limiting window

        """
        if request_rates is None:
            return
        
        longest_window_seconds = max(
            [rate.number_of_seconds() for rate in [request_rate for request_rate in request_rates]]
        )
        irrelevance_horizon = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=longest_window_seconds
        )
        self.previous_request_timestamps = [
            ts for ts in self.previous_request_timestamps if ts > irrelevance_horizon
        ]

    def get_relevant_history(self, request_rate: RequestRateLimit = None):
        """
        Returns the previous requests which are relevant to a specific rate limiting window.
        First, we prune out timestamps which are older than the time window.
        We also only need to keep timestamps up until the request count for the rate limit.
        For example:
        - Rate limit is 10 requests per 10 seconds
        - If (somehow, for the sake of argument) there were 20 requests in the last 10 seconds, 
        we only need to keep the most recent 10 to base our calculation on
        """
        if request_rate is None:
            return self.previous_request_timestamps
        longest_window_seconds = request_rate.number_of_seconds()
        irrelevance_horizon = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=longest_window_seconds
        )
        
        pruned = [ts for ts in self.previous_request_timestamps if ts > irrelevance_horizon]
        if len(pruned) > request_rate.request_count:
            return pruned[:request_rate.request_count]
        else:
            return pruned


class RequestRateLimit(SubscriptableBaseModel):
    """
    Request rate limits
        Defined as a request count, time unit and number of units e.g. (1,"second",5) = 1 request per 5 seconds, or (100, "minute", 15) = 100 requests per 15 minutes
    """

    request_count: int
    time_unit: TimeUnitType
    unit_count: int

    def number_of_seconds(self):
        """
        Converts the time_unit and unit_count to a number of seconds.
        E.g. 5 minutes = 300
        2 hours = 7200
        """
        if self.time_unit == "second":
            return self.unit_count
        elif self.time_unit == "minute":
            return self.unit_count * 60
        elif self.time_unit == "hour":
            return self.unit_count * 3600
        elif self.time_unit == "day":
            return self.unit_count * 86400
        else:
            raise ValueError(f"Unknown time unit: {self.time_unit}")

    def to_description(self) -> str:
        """Returns a readable description of this limit.
        For example:
        "1 request per minute"
        "5 requests per 2 seconds"

        Returns:
            str: the description as described above
        """
        return (
            str(self.request_count)
            + " "
            + "request"
            + ("s" if self.request_count > 1 else "")
            + " per "
            + (
                self.time_unit
                if self.unit_count == 1
                else f"{self.unit_count} {self.time_unit}s"
            )
        )


class RetryLaterException(Exception):
    """
    Exception raised when the app has notified that rate limits are exceeded.
    Throwing this during record apply imposes a temporary extra API constraint that
    we need to wait until a future date before more requests are made.

    """

    def __init__(self, future_datetime: datetime.datetime):
        self.future_datetime = future_datetime
        message = "Remote system wants us to retry later"
        self.message = message
        super().__init__(self.message)

class RetryWithLogging(Retry):
    """
        Adding extra logs before making a retry request     
    """
    def __init__(self, *args: Any, **kwargs: Any) -> Any:
        self.thread_cancellation_token:Optional[threading.Event] = None
        return super().__init__(*args, **kwargs)
    
    def new(self, **kw):
        new_retry = super().new(**kw)
        new_retry.thread_cancellation_token = self.thread_cancellation_token
        return new_retry
    
    def sleep_for_retry(self, response=None):
        retry_after = self.get_retry_after(response)
        if retry_after:
            logger.info(f"Retrying after {retry_after} seconds due to Retry-After header")
            with tracer.start_as_current_span("http_retry_wait"):
                if self.thread_cancellation_token is None:
                    time.sleep(retry_after)
                else:
                    if self.thread_cancellation_token.wait(retry_after):
                        raise InterruptedWhileWaitingException(message="The sync was interrupted while waiting for rate limiting to expire")
            return True
        return False

    def _sleep_backoff(self):
        backoff = self.get_backoff_time()
        if backoff <= 0:
            return
        logger.info(f"Retrying after {backoff} seconds due to backoff time")
        if self.thread_cancellation_token is None:
            time.sleep(backoff)
        else:
            if self.thread_cancellation_token.wait(backoff):
                raise InterruptedWhileWaitingException(message="The sync was interrupted while waiting for rate limiting to expire")

class LongRequestLoggingAdapter(HTTPAdapter):
    """
    An adapter which wraps HTTPAdapter, and logs a warning if a request takes longer than a specified threshold
    """
    def __init__(self, 
                 threshold_ms:int, 
                 log_level=logging.WARNING,
                 **kwargs):
        super().__init__(**kwargs)
        self.threshold_ms = threshold_ms
        self.logger = logging.getLogger(__name__)
        self.log_level = log_level

    def send(self, request, *args, **kwargs):
        start_time = time.time()
        response = super().send(request, *args, **kwargs)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        if elapsed_time > self.threshold_ms:
            self.logger.log(self.log_level, f"Request exceeded response time threshold of {self.threshold_ms}ms, taking {elapsed_time:.2f}ms to respond. URL: {request.url}")
        return response


class RateLimitedSession(requests.Session):
    """
    Creates a requests session that will automatically handle rate limiting.
    It will retry requests that return a 429 status code, and will wait until the rate limit is reset.
    The thread_cancellation_token is observed when waiting, as well as the overall run deadline.
    In case this is used across threads, the retry count will be tracked per request URL (minus query parameters). It will be cleared when the request is successful.
    """
    def __init__(self,
                 run_deadline:datetime.datetime,
                 thread_cancellation_token:threading.Event,
                 max_retries=5,
                 backoff_factor=1,
                 statuses_to_include:List[int] = [429],
                 respect_retry_after_header:bool = True,
                 response_time_warning_threshold_ms:Optional[int] = None):
        super().__init__()
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retries:Dict[str,int] = {}
        self._retries_lock = threading.Lock()
        self.run_deadline = run_deadline
        self.thread_cancellation_token = thread_cancellation_token
        self.statuses_to_include = statuses_to_include

        retry_strategy = RetryWithLogging(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=statuses_to_include,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            respect_retry_after_header=respect_retry_after_header
        )
        retry_strategy.thread_cancellation_token = thread_cancellation_token
        if response_time_warning_threshold_ms is not None:
            adapter = LongRequestLoggingAdapter(max_retries=retry_strategy, threshold_ms=response_time_warning_threshold_ms)
        else:
            adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("https://", adapter)
        self.mount("http://", adapter)
    
    def set_retries(self, url:str, retries:int):
        # ensure that the query parameters are not included in the key
        url = re.sub(r'\?.*$', '', url)
        with self._retries_lock:
            self.retries[url] = retries
    
    def get_retries(self, url:str):
        # ensure that the query parameters are not included in the key
        url = re.sub(r'\?.*$', '', url)
        with self._retries_lock:
            return self.retries.get(url,0)
    
    def increment_retries(self, url:str) -> int:
        # ensure that the query parameters are not included in the key
        url = re.sub(r'\?.*$', '', url)
        with self._retries_lock:
            self.retries[url] = self.retries.get(url,0) + 1
            return self.retries[url]

    def request(self, method, url, **kwargs):
        while True:
            response = super().request(method, url, **kwargs)
            # TODO: this is probably all redundant as the Retry object should handle this at a lower level (urllib3)
            if response.status_code in self.statuses_to_include:
                if 'Retry-After' in response.headers:
                    retry_after = response.headers['Retry-After']
                    if retry_after.isdigit():
                        wait_time = int(retry_after)
                    else:
                        # Retry-After can be a date in the format specified in https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After
                        # e.g. Fri, 31 Dec 1999 23:59:59 GMT
                        # we'll parse it using the standard datetime parser
                        retry_datetime = datetime.datetime.strptime(retry_after, "%a, %d %b %Y %H:%M:%S %Z")
                        retry_datetime = retry_datetime.replace(tzinfo=pytz.UTC)
                        current_datetime = datetime.datetime.now(pytz.UTC)
                        wait_time = (retry_datetime - current_datetime).total_seconds()
                    # first check that the wait time is not longer than the run deadline
                    if datetime.datetime.now(pytz.UTC) + datetime.timedelta(seconds=wait_time) > self.run_deadline:
                        raise InterruptedWhileWaitingException(message=f"The rate limiting wait time ({wait_time} seconds) would exceed the run deadline")
                    logger.info(f"Waiting for {wait_time} seconds before retrying {method} request to {url}")
                    # if wait() returns true, it means that the thread was cancelled
                    with tracer.start_as_current_span("http_retry_wait"):
                        if self.thread_cancellation_token.wait(wait_time):
                            raise InterruptedWhileWaitingException(message="The sync was interrupted while waiting for rate limiting to expire")
                else:
                    current_url_retries = self.increment_retries(url)
                    if current_url_retries >= self.max_retries:
                        raise requests.exceptions.RetryError(f"Maximum retries reached: {self.max_retries}")
                    backoff_time = self.backoff_factor * (2 ** (current_url_retries - 1))
                    if datetime.datetime.now(pytz.UTC) + datetime.timedelta(seconds=backoff_time) > self.run_deadline:
                        raise InterruptedWhileWaitingException(message=f"The rate limiting backoff time ({backoff_time} seconds) would exceed the run deadline")
                    logger.info(f"Waiting for {backoff_time} seconds before retrying {method} request to {url}")
                    with tracer.start_as_current_span("http_retry_wait"):
                        if self.thread_cancellation_token.wait(backoff_time):
                            raise InterruptedWhileWaitingException(message="The sync was interrupted while waiting for rate limiting backoff")
            else:
                self.set_retries(url,0)  # Reset retries if the request is successful
                return response


class InterruptedWhileWaitingException(Exception):
    """
    Indicates that while waiting for rate limiting to expire, the sync was interrupted
    """
    def __init__(self, message:str = "The sync was interrupted while waiting"):
        self.message = message
        super().__init__(self.message)

def too_many_requests_hook(
    fallback_future_datetime: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    + datetime.timedelta(hours=24),
):
    """
    A Requests hook which raises a RetryLaterException if an HTTP 429 response is returned.
    Examines the Retry-After header (https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After)
    to determine the appropriate future datetime to retry.
    If that isn't available, it falls back to fallback_future_datetime.

    """

    def hook(resp: requests.Response, *args, **kwargs):
        """
        The actual hook implementation
        """
        if resp.status_code == 429:
            if "Retry-After" in resp.headers:
                retry_after: str = resp.headers["Retry-After"]
                if retry_after.isnumeric():
                    raise RetryLaterException(
                        future_datetime=datetime.datetime.now(datetime.timezone.utc)
                        + datetime.timedelta(seconds=int(retry_after))
                    )
                retry_date = parsedate_to_datetime(retry_after)
                raise RetryLaterException(future_datetime=retry_date)
            raise RetryLaterException(future_datetime=fallback_future_datetime)

    return hook


ApiLimits.model_rebuild()
