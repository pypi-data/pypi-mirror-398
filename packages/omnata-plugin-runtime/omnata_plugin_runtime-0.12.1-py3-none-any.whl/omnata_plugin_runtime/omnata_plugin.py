# pylint: disable=protected-access
"""
Omnata Plugin Runtime.
Includes data container classes and defines the contract for a plugin.
"""
from __future__ import annotations
from inspect import signature
import sys
from types import FunctionType
from typing import Union
from typing_extensions import Self
if tuple(sys.version_info[:2]) >= (3, 9):
    # Python 3.9 and above
    from typing import Annotated  # pylint: disable=ungrouped-imports
else:
    # Python 3.8 and below
    from typing_extensions import Annotated
from dataclasses import dataclass
import zipfile
import datetime
import http
import json
import queue
import threading
import time
import hashlib
import requests
import pkgutil
import inspect
import importlib
import sys
import os
from abc import ABC, abstractmethod
from decimal import Decimal
from functools import partial, wraps, reduce
from logging import getLogger
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Type, cast

import jinja2
import pandas
from pydantic_core import to_jsonable_python
from pydantic import Field, TypeAdapter, ValidationError, create_model, model_validator, BaseModel
from dateutil.parser import parse
from jinja2 import Environment
from snowflake.connector.pandas_tools import write_pandas
from snowflake.connector.version import VERSION
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
from tenacity import Retrying, stop_after_attempt, wait_fixed, retry_if_exception_message

from .logging import OmnataPluginLogHandler, logger, tracer, meter
stream_duration_gauge = meter.create_gauge(
    name="omnata.sync_run.stream_duration",
    description="The duration of stream processing",
    unit="s",
)
from opentelemetry import context
import math
import numpy as np

from .api import (
    PluginMessage,
    PluginMessageAbandonedStreams,
    PluginMessageCancelledStreams,
    PluginMessageCurrentActivity,
    PluginMessageStreamProgressUpdate,
    PluginMessageStreamState,
    PluginMessageRateLimitState,
    handle_proc_result,
)
from .configuration import (
    STANDARD_OUTBOUND_SYNC_ACTIONS,
    ConnectionConfigurationParameters,
    InboundSyncConfigurationParameters,
    OutboundSyncAction,
    OutboundSyncConfigurationParameters,
    OutboundSyncStrategy,
    StoredConfigurationValue,
    StoredMappingValue,
    StoredStreamConfiguration,
    StreamConfiguration,
    SubscriptableBaseModel,
    SyncConfigurationParameters,
    get_secrets,
    ConnectivityOption,
    OutboundTargetType,
    OutboundRecordTransformationParameters
)
from .forms import (
    ConnectionMethod,
    InboundSyncConfigurationForm,
    OutboundSyncConfigurationForm,
)
from .rate_limiting import (
    ApiLimits,
    HttpMethodType,
    InterruptedWhileWaitingException,
    RateLimitState,
    RateLimitedSession
)
from .json_schema import (
    FullyQualifiedTable
)

SortDirectionType = Literal["asc", "desc"]


class PluginManifest(SubscriptableBaseModel):
    """
    Constructs a Plugin Manifest, which identifies the application, describes how it can work, and defines any runtime code dependancies.
        :param str plugin_id: A short, string identifier for the application, a combination of lowercase alphanumeric and underscores, e.g. "google_sheets"
        :param str plugin_name: A descriptive name for the application, e.g. "Google Sheets"
        :param str developer_id: A short, string identifier for the developer, a combination of lowercase alphanumeric and underscores, e.g. "acme_corp"
        :param str developer_name: A descriptive name for the developer, e.g. "Acme Corp"
        :param str docs_url: The URL where plugin documentation can be found, e.g. "https://docs.omnata.com"
        :param bool supports_inbound: A flag to indicate whether or not the plugin supports inbound sync. Support for inbound sync behaviours (full/incremental) is defined per inbound stream.
        :param List[OutboundSyncStrategy] supported_outbound_strategies: A list of sync strategies that the plugin can support, e.g. create,upsert.
        :param List[ConnectivityOption] supported_connectivity_options: A list of connectivity options that the plugin can support, e.g. direct,ngrok,privatelink
        :param str timestamp_tz_format: The format to use when converting TIMESTAMP_TZ values to strings in the transformed record.
        :param str timestamp_ntz_format: The format to use when converting TIMESTAMP_NTZ values to strings in the transformed record.
        :param str timestamp_ltz_format: The format to use when converting TIMESTAMP_LTZ values to strings in the transformed record.
        For each of the above three formats, you can include "{{precision}}" to substitute the precision of the timestamp, if that matters.
        For example, "YYYY-MM-DDTHH24:MI:SS.FF{{precision}}TZHTZM" would be a valid format string.
        :param str date_format: The format to use when converting DATE values to strings in the transformed record.
    """

    plugin_id: str
    plugin_name: str
    developer_id: str
    developer_name: str
    docs_url: str
    supports_inbound: bool
    supported_outbound_strategies: List[OutboundSyncStrategy] = Field(
        title="A list of sync strategies that the plugin can support. If outbound_target_types are specified, theses strategies are allocated there. Otherwise, they apply globally"
    )
    supported_connectivity_options: List[ConnectivityOption] = Field(
        default_factory=lambda: [ConnectivityOption.DIRECT]
    )
    outbound_target_types: Optional[List[OutboundTargetType]] = Field(
        default=None,
        title="An optional list of target types that the plugin can support."
    )
    outbound_target_transformation_parameters: OutboundRecordTransformationParameters = Field(
        default_factory=lambda: OutboundRecordTransformationParameters(),
        title="The parameters for transforming records for various Snowflake data types"
    )

class SnowflakeFunctionParameter(BaseModel):
    """
    Represents a parameter for a Snowflake UDF or UDTF
    """
    name: str
    description: str
    data_type: str
    default_value_clause: Optional[str] = None

    def __str__(self):
        if self.default_value_clause:
            return f"{self.name} {self.data_type} default {self.default_value_clause}"
        return f"{self.name} {self.data_type}"

class SnowflakeUDTFResultColumn(BaseModel):
    """
    Represents a result column for a Snowflake UDTF
    """
    name: str
    data_type: str
    def __str__(self):
        return f"{self.name} {self.data_type}"

class UDTFDefinition(BaseModel):
    """
    The information needed by the plugin uploader to put a Python UDTF definition into the setup script.
    Do not use this class directly in plugins, instead use the omnata_udtf decorator.
    """
    name: str = Field(..., title="The name of the UDTF")
    language: Literal['python','java'] = Field(..., title="The language of the UDF")
    runtime_version: str = Field(..., title="The runtime version of the UDF (language dependent)")
    description: str = Field(..., title="A description of the UDTF")
    params: List[SnowflakeFunctionParameter] = Field(..., title="The parameters of the UDTF")
    result_columns: List[SnowflakeUDTFResultColumn] = Field(..., title="The result columns of the UDTF")
    handler: str = Field(..., title="The handler class/function for the UDTF")
    expose_to_consumer: bool = Field(..., title="Whether the UDTF should be exposed to consumers")
    imports: Optional[List[str]] = Field(None, title="A list of imports required by the UDF")
    packages: Optional[List[str]] = Field(None, title="A list of packages required by the UDTF")

    def __str__(self):
        param_str = ', '.join([str(param) for param in self.params])
        table_result_columns = ', '.join([f"{col.name} {col.data_type}" for col in self.result_columns])
        packages_str = ', '.join([f"'{p}'" for p in self.packages])
        imports_str = ', '.join([f"'{i}'" for i in self.imports])
        return f"""CREATE OR REPLACE FUNCTION UDFS.{self.name}({param_str})
RETURNS TABLE({table_result_columns})
LANGUAGE {self.language.upper()}
RUNTIME_VERSION={self.runtime_version}
COMMENT = $${self.description}$$
PACKAGES = ({packages_str})
IMPORTS = ({imports_str})
HANDLER='{self.handler}';
"""

class UDFDefinition(BaseModel):
    """
    The information needed by the plugin uploader to put a Python UDF definition into the setup script.
    Do not use this class directly in plugins, instead use the omnata_udf decorator.
    """
    name: str = Field(..., title="The name of the UDF")
    language: Literal['python','java'] = Field(..., title="The language of the UDF")
    runtime_version: str = Field(..., title="The runtime version of the UDF (language dependent)")
    description: str = Field(..., title="A description of the UDF")
    params: List[SnowflakeFunctionParameter] = Field(..., title="The parameters of the UDF")
    result_data_type: str = Field(..., title="The data type returned by the UDF")
    handler: str = Field(..., title="The handler class/function for the UDF")
    expose_to_consumer: bool = Field(..., title="Whether the UDF should be exposed to consumers")
    imports: Optional[List[str]] = Field(None, title="A list of imports required by the UDF")
    packages: Optional[List[str]] = Field(None, title="A list of packages required by the UDF")

    def __str__(self):
        param_str = ', '.join([str(param) for param in self.params])
        packages_str = ', '.join([f"'{p}'" for p in self.packages])
        imports_str = ', '.join([f"'{i}'" for i in self.imports])
        return f"""CREATE OR REPLACE FUNCTION UDFS.{self.name}({param_str})
RETURNS {self.result_data_type}
LANGUAGE {self.language.upper()}
RUNTIME_VERSION={self.runtime_version}
COMMENT = $${self.description}$$
PACKAGES = ({packages_str})
IMPORTS = ({imports_str})
HANDLER='{self.handler}';
"""

class PluginInfo(BaseModel):
    """
    Manifest plus other derived information about a plugin which is determined during upload.
    :param str manifest: The manifest from the plugin's code
    :param List[str] anaconda_packages: A list of anaconda packages required by the plugin
    :param List[str] bundled_packages: A list of bundled packages required by the plugin
    :param str icon_source: The base64 encoded icon for the plugin
    :param str plugin_class_name: The name of the plugin class
    :param bool has_custom_validator: Whether or not the plugin has a custom validator
    :param str plugin_runtime_version: The version of the Omnata plugin runtime that the current version of the plugin was built against
    :param str tier: The tier of the plugin. 
        Setting this to 'byo' means that the plugin is internally developed or a free community plugin. The sync engine does not bill for the first plugin of this type, nor are billing events created for it.
        Setting this to 'partner' means that the plugin was developed and distributed by a partner. 
        All other values only carry meaning for Omnata plugins, to indicate which iconography to apply within the application.
    :param str package_source: Whether the plugin is packaged as a function or a stage
    :param List[UDFDefinition] consumer_udfs: A list of UDFs that the plugin exposes to consumers
    :param List[UDTFDefinition] consumer_udtfs: A list of UDTFs that the plugin exposes to consumers
    """

    manifest: PluginManifest
    anaconda_packages: List[str]
    bundled_packages: List[str]
    icon_source: Optional[str] = None
    plugin_class_name: str
    has_custom_validator: bool
    plugin_runtime_version: str
    plugin_devkit_version: str = 'unknown'
    tier: str
    package_source: Literal["function", "stage"]
    consumer_udfs: List[UDFDefinition] = Field(default_factory=list)
    consumer_udtfs: List[UDTFDefinition] = Field(default_factory=list)


def jinja_filter(func):
    """
    This annotation designates a function as a jinja filter.
    Adding it will put the function into the jinja globals so that it can be used in templates.
    """
    func.is_jinja_filter = True
    return func

@dataclass
class StateResult:
    """
    Represents the current cursor state of a stream. This simple wrapper just helps us identify what type of
    object is in the apply_results list.
    """
    new_state: Any

@dataclass
class RecordsToUploadResult:
    """
    Represents the records to upload for a stream. This simple wrapper just helps us identify what type of
    object is in the apply_results list.
    """
    records: pandas.DataFrame

@dataclass
class CriteriaDeleteResult:
    """
    Represents the result of processing criteria deletes for a stream. This simple wrapper just helps us identify what type of
    object is in the apply_results list.
    """
    criteria_deletes: pandas.DataFrame

class SyncRequest(ABC):
    """
    Functionality common to inbound and outbound syncs requests.

    Both inbound and outbound syncs have records to apply back to Snowflake (outbound have load results, inbound have records).
    So there's common functionality for feeding them in, as well as logging, other housekeeping tasks, and rate limiting.
    """

    def __init__(
        self,
        run_id: int,
        session: Session,
        source_app_name: str,
        results_schema_name: str,
        results_table_name: str,
        plugin_instance: OmnataPlugin,
        api_limits: List[ApiLimits],
        # this is a dictionary of rate limit states, keyed by endpoint category, across all syncs and branches for this connection
        # this is used for calculating waits, and is refreshed periodically from the engine
        rate_limit_state_all: Dict[str, RateLimitState],
        # this is a dictionary of rate limit states, keyed by endpoint category, for this sync and branch
        # this is used when updating the rate limit state
        rate_limit_state_this_sync_and_branch: Dict[str, RateLimitState],
        run_deadline: datetime.datetime,
        development_mode: bool = False,
        test_replay_mode: bool = False,
        sync_id: Optional[int] = None,
        branch_name: Optional[str] = None
    ):
        """
        Constructs a SyncRequest.

        :param int run_id: The ID number for the run, used to report back status to the engine
        :param any session: The snowpark session object, only used internally
        :param OmnataPlugin plugin_instance: The instance of the Omnata Plugin this request is for
        :param ApiLimits api_limits: Constraints to observe when performing HTTP requests
        :param bool development_mode: In development mode, apply_results_queue does not load into Snowflake, instead they are cached locally and can be retrieved via get_queued_results
        :return: nothing
        """
        logger.info(f"Initiating SyncRequest for sync run {run_id}, run deadline: {run_deadline}")
        self.deadline_reached:bool = False
        self._run_deadline = run_deadline
        self.plugin_instance = plugin_instance
        self._source_app_name = source_app_name
        self._results_schema_name = results_schema_name
        self._results_table_name = results_table_name
        self._full_results_table_name = (
            f"{source_app_name}.{results_schema_name}.{results_table_name}"
        )
        if self.plugin_instance is not None:
            self.plugin_instance._sync_request = self
        self._session: Session = session
        self._run_id = run_id
        self._sync_id = sync_id
        self._branch_name = branch_name
        self.api_limits = api_limits
        self.rate_limit_state_all = rate_limit_state_all
        self.rate_limit_state_this_sync_and_branch = rate_limit_state_this_sync_and_branch
        self._apply_results = None  # this will be re-initialised by subclasses
        # these deal with applying the results, not sure they belong here
        self._apply_results_lock = threading.Lock()
        # Snowflake connector appears to not be thread safe
        # # File \"/var/task/snowflake/snowpark/table.py\", line 221, in _get_update_result\n
        #     return UpdateResult(int(rows[0][0]), int(rows[0][1]))\nIndexError: list index out of range"
        self._snowflake_query_lock = threading.Lock()
        self._loadbatch_id = 0
        self._loadbatch_id_lock = threading.Lock()
        self.development_mode = development_mode
        self.test_replay_mode = test_replay_mode
        # This is used internally by the testing framework, when we're loading records in a behave test
        self._prebaked_record_state: Optional[pandas.DataFrame] = None
        # create a stop requestor to cease thread activity
        self._thread_cancellation_token = threading.Event()
        self._thread_exception_thrown = None
        self._apply_results_task = None
        self._cancel_checking_task = None
        self._rate_limit_update_task = None
        self._last_stream_progress_update = None
        self._last_states_update = None
        # store the opentelemetry context so that it can be attached inside threads
        self.opentelemetry_context = context.get_current()

        threading.excepthook = self.thread_exception_hook
        if self.development_mode is False:
            # start another worker thread to handle uploads of results every 10 seconds
            # we don't join on this thread, instead we cancel it once the workers have finished
            if self._apply_results_task is None:
                self._apply_results_task = threading.Thread(
                    target=self.__apply_results_worker,
                    args=(self._thread_cancellation_token,),
                )
                self._apply_results_task.start()
            # also spin up a thread to monitor for run cancellation
            if self._cancel_checking_task is None:
                self._cancel_checking_task = threading.Thread(
                    target=self.__cancel_checking_worker,
                    args=(self._thread_cancellation_token,),
                )
                self._cancel_checking_task.start()
            # and a thread for updating the rate limit state
            if self._rate_limit_update_task is None:
                self._rate_limit_update_task = threading.Thread(
                    target=self.__rate_limit_update_worker,
                    args=(self._thread_cancellation_token,),
                )
                self._rate_limit_update_task.start()
    
    # create an exception handler for the threads
    def thread_exception_hook(self,args):
        self._thread_exception_thrown = args
        logger.error("Thread exception", exc_info=True)
        self._thread_cancellation_token.set()  # this will tell the other threads to stop working
        logger.debug(
            f"thread_cancellation_token: {self._thread_cancellation_token.is_set()}"
        )

    def get_ratelimit_retrying_http_session(self,
                                            max_retries: int = 5,
                                            backoff_factor: int = 1,
                                            statuses_to_include: List[int] = [429],
                                            response_time_warning_threshold_ms:Optional[int] = None
):
        """
        Returns a requests.Session object which can respond to 429 responses by waiting and retrying.
        Takes into account the run deadline and cancellation status.
        This is an alternative which can be used when the target API does not publish specific rate limits, and instead just asks you to respond to 429s as they are sent.
        """
        if self.test_replay_mode:
            # when in test replay mode, we want to make the same requests but without any waiting
            return RateLimitedSession(
                run_deadline=self._run_deadline,
                thread_cancellation_token=self._thread_cancellation_token,
                max_retries=max_retries,
                backoff_factor=0,
                statuses_to_include=statuses_to_include,
                respect_retry_after_header=False,
                response_time_warning_threshold_ms=response_time_warning_threshold_ms
            )
        return RateLimitedSession(
            run_deadline=self._run_deadline,
            thread_cancellation_token=self._thread_cancellation_token,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            statuses_to_include=statuses_to_include,
            response_time_warning_threshold_ms=response_time_warning_threshold_ms
        )
    

    def __apply_results_worker(self, cancellation_token:threading.Event):
        """
        Designed to be run in a thread, this method polls the results every 20 seconds and sends them back to Snowflake.
        """
        context.attach(self.opentelemetry_context)
        while not cancellation_token.is_set():
            logger.debug("apply results worker checking for results")
            self.apply_results_queue()
            cancellation_token.wait(20)
        logger.info("apply results worker exiting")
    
    def __rate_limit_update_worker(self, cancellation_token:threading.Event):
        """
        Designed to be run in a thread, this method reports back the rate limit state to Snowflake every minute.
        It also gives us the latest rate limit state from Snowflake, so that activity on other syncs/branches can
        impact rate limiting on this one.
        """
        context.attach(self.opentelemetry_context)
        while not cancellation_token.is_set():
            try:
                self.apply_rate_limit_state()
            except Exception as e:
                logger.error(f"Error updating rate limit state: {e}")
            cancellation_token.wait(60)
        logger.info("rate limit update worker exiting")

    def __cancel_checking_worker(self, cancellation_token:threading.Event):
        context.attach(self.opentelemetry_context)
        """
        Designed to be run in a thread, this method checks to see if the sync run has been cancelled
        or if the deadline has been reached.
        Previously this was being done in the managed_inbound_processing and managed_outbound_processing
        workers, but that meant it's not being checked when the plugin doesn't use those decorators.
        """
        while not cancellation_token.is_set():
            logger.debug("cancel checking worker checking for cancellation")
            if (datetime.datetime.now(datetime.timezone.utc) > self._run_deadline):  # pylint: disable=protected-access
                # if we've reached the deadline for the run, end it
                self.deadline_reached = True
                self.apply_deadline_reached()  # pylint: disable=protected-access
                return
            is_cancelled:bool = False
            with self._snowflake_query_lock:
                try:
                    # this is not ideal, but "Bind variable in stored procedure is not supported yet"
                    query_result = self._session.sql(
                        f"call {self._source_app_name}.API.PLUGIN_CANCELLATION_CHECK({self._run_id})"
                    ).collect()
                    cancellation_result = handle_proc_result(query_result)
                    is_cancelled = cancellation_result["is_cancelled"]
                except Exception as e:
                    logger.error(f"Error checking cancellation: {e}")
            if is_cancelled:
                self.apply_cancellation()
            cancellation_token.wait(20)
        logger.info("cancel checking worker exiting")

    @abstractmethod
    def apply_results_queue(self):
        """
        Abstract method to apply the queued results. Inbound and Outbound syncs will each implement their own results
        processing logic
        """
        logger.error(
            "apply_results_queue called on SyncRequest base class, this should never occur"
        )
    
    def apply_rate_limit_state(self):
        """
        Updates the rate limit state in the engine, and refreshes the rate limit state for this sync and branch
        """
        # prune the history first. Strictly speaking, we should not prune here since there could be other syncs with longer
        # rate limiting windows than this one, but it's fairly unlikely users would override defaults to that extent
        if self.rate_limit_state_this_sync_and_branch is not None and len(self.rate_limit_state_this_sync_and_branch) > 0:
            for endpoint_category in self.rate_limit_state_this_sync_and_branch:
                api_limits_for_category = [x for x in self.api_limits if x.endpoint_category == endpoint_category]
                if len(api_limits_for_category) > 0:
                    self.rate_limit_state_this_sync_and_branch[endpoint_category].prune_history(api_limits_for_category[0].request_rates)
            logger.debug(f"Updating rate limit state for sync {self._run_id}")
            update_rate_limit_result = self._plugin_message(
                PluginMessageRateLimitState(rate_limit_state=self.rate_limit_state_this_sync_and_branch)
            )
            if update_rate_limit_result is not None:
                sync_id:int = update_rate_limit_result["sync_id"]
                sync_branch_name:str = update_rate_limit_result["sync_branch_name"]
                latest_state = TypeAdapter(Dict[int,Dict[str,Dict[str,RateLimitState]]]).validate_python(update_rate_limit_result["latest_state"])
                (rate_limit_state_all, rate_limit_state_this_branch) = RateLimitState.collapse(latest_state,sync_id, sync_branch_name)
                self.rate_limit_state_all = rate_limit_state_all
                self.rate_limit_state_this_sync_and_branch = rate_limit_state_this_branch
        else:
            logger.debug("No rate limit state to update")

    @abstractmethod
    def apply_cancellation(self):
        """
        Abstract method to handle run cancellation.
        """

    @abstractmethod
    def apply_deadline_reached(self):
        """
        Abstract method to handle a run deadline being reached
        """

    def register_http_request(self, endpoint_category: str):
        """
        Registers a request as having just occurred, for rate limiting purposes.
        You only need to use this if your HTTP requests are not automatically being
        registered, which happens if http.client.HTTPConnection is not being used.
        """
        if endpoint_category in self.rate_limit_state_this_sync_and_branch:
            # we register it in both dictionaries, because one is used for calculating waits, and the other is used for updating the rate limit state centrally
            # TODO: this could be a lot more efficient if we only provided and received the requests past a certain date, instead of all of them
            self.rate_limit_state_this_sync_and_branch[endpoint_category].register_http_request()
            self.rate_limit_state_all[endpoint_category].register_http_request()

    def wait_for_rate_limiting(self, api_limit: ApiLimits) -> bool:
        """
        Waits for rate limits to pass before returning. Uses the api_limits and the history of
        request timestamps to determine how long to wait.

        :return: true if wait for rate limits was successful, otherwise false (thread was interrupted)
        :raises: DeadlineReachedException if rate limiting is going to require us to wait past the run deadline
        """
        if api_limit is None:
            return True
        wait_until = api_limit.calculate_wait(
            self.rate_limit_state_all[api_limit.endpoint_category]
        )
        if wait_until > self._run_deadline:
            logger.info(
                f"calculated wait_until date was {wait_until}, which is greater than {self._run_deadline}. Raise DeadlineReachedException"
            )
            # if the rate limiting is going to require us to wait past the run deadline, we bail out now
            raise DeadlineReachedException()
        time_now = datetime.datetime.now(datetime.timezone.utc)
        logger.debug(
            f"calculated wait until date was {wait_until}, comparing to {time_now}"
        )

        while wait_until > time_now:
            seconds_to_sleep = (wait_until - time_now).total_seconds()
            if self._thread_cancellation_token.wait(seconds_to_sleep):
                return False
            wait_until = api_limit.calculate_wait(
                self.rate_limit_state_all[api_limit.endpoint_category]
            )
            time_now = datetime.datetime.now(datetime.timezone.utc)
        return True

    def wait(self, seconds: float) -> bool:
        """
        Waits for a given number of seconds, provided the current sync run isn't cancelled in the meantime.
        Returns True if no cancellation occurred, otherwise False.
        If False is returned, the plugin should exit immediately.
        """
        return not self._thread_cancellation_token.wait(seconds)

    def update_activity(self, current_activity: str) -> Dict:
        """
        Provides an update to the user on what's happening inside the sync run. It should
        be used before commencing a potential long-running phase, like polling and waiting or
        calling an API (keep in mind, rate limiting may delay even a fast API).
        Keep this to a very consise string, like 'Fetching records from API'.
        Avoid lengthy diagnostic messages, anything like this should be logged the normal way.
        """
        logger.debug(f"Activity update: {current_activity}")
        return self._plugin_message(
            PluginMessageCurrentActivity(current_activity=current_activity)
        )

    def _plugin_message(self, message: PluginMessage, ignore_errors:bool = True) -> Dict:
        """
        Sends a message back to the plugin. This is used to send back the results of a sync run.
        """
        logger.debug(f"Sending plugin message: {message}")
        with self._snowflake_query_lock:
            try:
                # this is not ideal, but "Bind variable in stored procedure is not supported yet"
                return handle_proc_result(
                    self._session.sql(
                        f"""call {self._source_app_name}.API.PLUGIN_MESSAGE(
                                  {self._run_id},
                                  PARSE_JSON($${json.dumps(to_jsonable_python(message))}$$))"""
                    ).collect()
                )
            except Exception as e:
                if ignore_errors:
                    logger.error(
                        f"Error sending plugin message: {e}", exc_info=True, stack_info=True
                    )
                    return None
                else:
                    raise e


class HttpRateLimiting:
    """
    A custom context manager which applies rate limiting automatically.
    Not thread safe but shouldn't need to be, since it'll be used once spanning all HTTP activity
    """

    def __init__(
        self, sync_request: SyncRequest, parameters: SyncConfigurationParameters
    ):
        self.sync_request = sync_request
        self.original_putrequest = None
        self.parameters = parameters

    def __enter__(self):
        """
        Used to manage the outbound http requests made by Omnata Plugins.
        It does this by patching http.client.HTTPConnection.putrequest
        """
        self_outer = self
        self.original_putrequest = http.client.HTTPConnection.putrequest  # type: ignore

        def new_putrequest(
            self,
            method: HttpMethodType,
            url: str,
            skip_host: bool = False,
            skip_accept_encoding: bool = False,
        ):
            # first, we do any waiting that we need to do (possibly none)
            api_limit_matches = ApiLimits.request_match(
                self_outer.sync_request.api_limits, method, url
            )
            for matched_api_limit in api_limit_matches:
                if not self_outer.sync_request.wait_for_rate_limiting(
                    matched_api_limit
                ):
                    logger.info("Interrupted while waiting for rate limiting")
                    raise InterruptedWhileWaitingException()
                # and also register this current request in its limit category
                self_outer.sync_request.register_http_request(
                    matched_api_limit.endpoint_category
                )
            assert self_outer.original_putrequest is not None
            return self_outer.original_putrequest(
                self, method, url, skip_host, skip_accept_encoding
            )

        http.client.HTTPConnection.putrequest = new_putrequest  # type: ignore

    def __exit__(self, exc_type, exc_value, traceback):
        http.client.HTTPConnection.putrequest = self.original_putrequest  # type: ignore

def wrap_result_value(x):
    # Check for NaN (float or numpy.nan)
    if x is None:
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    if isinstance(x, str):
        return json.dumps({"value": x})
    try:
        # Try to detect pandas NaN (which is float('nan'))
        if isinstance(x, np.floating) and np.isnan(x):
            return None
    except ImportError:
        return None
    return json.dumps(x)

class OutboundSyncRequest(SyncRequest):
    """
    A request to sync data outbound (from Snowflake to an app)
    """

    def __init__(
        self,
        run_id: int,
        session: Session,
        source_app_name: str,
        records_schema_name: str,
        records_table_name: str,
        results_schema_name: str,
        results_table_name: str,
        plugin_instance: OmnataPlugin,
        api_limits: List[ApiLimits],
        rate_limit_state_all: Dict[str, RateLimitState],
        rate_limit_state_this_sync_and_branch: Dict[str, RateLimitState],
        run_deadline: datetime.datetime,
        development_mode: bool = False,
        test_replay_mode: bool = False,
        sync_id: Optional[int] = None,
        branch_name: Optional[str] = None
    ):
        """
        Constructs an OutboundSyncRequest.

        :param int run_id: The ID number for the run, only used to report back on status
        :param any session: The snowpark session object, only used internally
        :param OmnataPlugin plugin_instance: The instance of the Omnata Plugin this request is for
        :param ApiLimits api_limits: Constraints to observe when performing HTTP requests
        :param bool development_mode: In development mode, apply_results_queue does not load into Snowflake, instead they are cached locally and can be retrieved via get_queued_results
        :param bool test_replay_mode: When enabled, it is safe to assume that HTTP requests are hitting a re-recorded log, so there is no need to wait in between polling
        :return: nothing
        """
        SyncRequest.__init__(
            self,
            run_id=run_id,
            session=session,
            source_app_name=source_app_name,
            results_schema_name=results_schema_name,
            results_table_name=results_table_name,
            plugin_instance=plugin_instance,
            api_limits=api_limits,
            rate_limit_state_all=rate_limit_state_all,
            rate_limit_state_this_sync_and_branch=rate_limit_state_this_sync_and_branch,
            run_deadline=run_deadline,
            development_mode=development_mode,
            test_replay_mode=test_replay_mode,
            sync_id=sync_id,
            branch_name=branch_name
        )
        self._full_records_table_name = (
            f"{source_app_name}.{records_schema_name}.{records_table_name}"
        )
        self._apply_results: List[pandas.DataFrame] = []

    def _get_next_loadbatch_id(self):
        with self._loadbatch_id_lock:
            self._loadbatch_id = self._loadbatch_id + 1
            return self._loadbatch_id

    def apply_results_queue(self):
        """
        Merges all of the queued results and applies them
        """
        logger.debug("OutboundSyncRequest apply_results_queue")
        if self._apply_results is not None:
            with self._apply_results_lock:
                self._apply_results = [
                    x for x in self._apply_results if x is not None and len(x) > 0
                ]  # remove any None/empty dataframes
                if len(self._apply_results) > 0:
                    logger.debug(
                        f"Applying {len(self._apply_results)} batches of queued results"
                    )
                    # upload all cached apply results
                    all_dfs = pandas.concat(self._apply_results)
                    self._apply_results_dataframe(all_dfs)
                    self._apply_results.clear()
                else:
                    logger.debug("No queued results to apply")

    def apply_cancellation(self):
        """
        Handles a cancellation of an outbound sync.
        1. Signals an interruption to the load process for the other threads
        2. Applies remaining queued results
        3. Marks remaining active records as delayed
        """
        # set the token so that the other threads stop
        logger.info("Applying cancellation for OutboundSyncRequest")
        self._thread_cancellation_token.set()
        self.apply_results_queue()

    def apply_deadline_reached(self):
        """
        Handles the reaching of a deadline for an outbound sync.
        The behaviour is the same as for a cancellation, since the record state looks the same
        """
        logger.info("Apply deadline reached for OutboundSyncRequest")
        self.apply_cancellation()

    def enqueue_results(self, results: pandas.DataFrame):
        """
        Adds some results to the queue for applying asynchronously
        """
        logger.debug(f"Enqueueing {len(results)} results for upload")
        for required_column in ["IDENTIFIER", "RESULT", "SUCCESS"]:
            if required_column not in results.columns:
                raise ValueError(
                    f"{required_column} column was not included in results"
                )
        with self._apply_results_lock:
            self._apply_results.append(results)

    def get_queued_results(self):
        """
        Returns results queued during processing
        """
        if len(self._apply_results) == 0:
            raise ValueError(
                "get_queued_results was called, but no results have been queued"
            )
        concat_results = pandas.concat(self._apply_results)
        return concat_results

    def _preprocess_results_dataframe(self, results_df: pandas.DataFrame):
        """
        Validates and pre-processes outbound sync results dataframe.
        The result is a dataframe contain all (and only):
        'IDENTIFIER' string
        'APP_IDENTIFIER' string
        'APPLY_STATE' string
        'APPLY_STATE_DATETIME' datetime (UTC)
        'LOADBATCH_ID' int
        'RESULT' object
        """
        results_df.set_index("IDENTIFIER", inplace=True, drop=False)
        results_df["APPLY_STATE_DATETIME"] = str(datetime.datetime.now().astimezone())
        if results_df is not None:
            logger.debug(
                f"Applying a queued results dataframe of {len(results_df)} records"
            )
            # change the success flag to an appropriate APPLY STATUS
            results_df.loc[results_df["SUCCESS"] == True, "APPLY_STATE"] = "SUCCESS"
            results_df.loc[
                results_df["SUCCESS"] == False, "APPLY_STATE"
            ] = "DESTINATION_FAILURE"
            results_df = results_df.drop("SUCCESS", axis=1)
            # if results weren't added by enqueue_results, we'll add the status datetime column now
            if "APPLY_STATE_DATETIME" not in results_df.columns:
                results_df["APPLY_STATE_DATETIME"] = str(
                    datetime.datetime.now().astimezone()
                )
            if "APP_IDENTIFIER" not in results_df:
                results_df["APP_IDENTIFIER"] = None
            if "LOADBATCH_ID" not in results_df:
                results_df["LOADBATCH_ID"] = self._get_next_loadbatch_id()
            # we dump the result data to a json string to make uploading to Snowflake less error prone, but only if it's not None
            results_df["RESULT"] = results_df["RESULT"].apply(wrap_result_value)
        # trim out the columns we don't need to return
        return results_df[
            results_df.columns.intersection(
                [
                    "IDENTIFIER",
                    "APP_IDENTIFIER",
                    "APPLY_STATE",
                    "APPLY_STATE_DATETIME",
                    "LOADBATCH_ID",
                    "RESULT",
                ]
            )
        ]

    def _apply_results_dataframe(self, results_df: pandas.DataFrame):
        """
        Applies results for an outbound sync. This involves merging back onto the record state table
        """
        logger.debug("applying results to table")
        # use a random table name with a random string to avoid collisions
        with self._snowflake_query_lock:
            with tracer.start_as_current_span("apply_results"):
                for attempt in Retrying(stop=stop_after_attempt(30),wait=wait_fixed(2),reraise=True,retry=retry_if_exception_message(match=".*(is being|was) committed.*")):
                    with attempt:
                        success, nchunks, nrows, _ = write_pandas(
                            conn=self._session._conn._cursor.connection,  # pylint: disable=protected-access
                            df=self._preprocess_results_dataframe(results_df),
                            quote_identifiers=False,
                            table_name=self._full_results_table_name,
                            auto_create_table=False
                        )
                        if not success:
                            raise ValueError(
                                f"Failed to write results to table {self._full_results_table_name}"
                            )
                        logger.debug(
                            f"Wrote {nrows} rows and {nchunks} chunks to table {self._full_results_table_name}"
                        )

    def __dataframe_wrapper(
        self, data_frame: pandas.DataFrame, render_jinja: bool = True
    ) -> pandas.DataFrame:
        """
        Takes care of some common stuff we need to do for each dataframe for outbound syncs.
        Parses the JSON in the transformed record column (Snowflake passes it as a string).
        Also when the mapper is a jinja template, renders it.
        """
        logger.debug(
            f"Dataframe wrapper pre-processing {len(data_frame)} records"
        )
        if len(data_frame) > 0:
            try:
                data_frame["TRANSFORMED_RECORD"] = data_frame[
                    "TRANSFORMED_RECORD"
                ].apply(json.loads)
                # we also perform json.loads on TRANSFORMED_RECORD_PREVIOUS, but only if it's not null
                data_frame["TRANSFORMED_RECORD_PREVIOUS"] = data_frame[
                    "TRANSFORMED_RECORD_PREVIOUS"
                ].apply(
                    lambda x: json.loads(x) if x is not None else None
                )
            except TypeError as type_error:
                logger.error(
                    "Error parsing transformed record output as JSON", exc_info=True
                )
                if (
                    "the JSON object must be str, bytes or bytearray, not NoneType"
                    in str(type_error)
                ):
                    raise ValueError(
                        "null was returned from the record transformer, an object must always be returned"
                    ) from type_error
            if (
                render_jinja
                and "jinja_template" in data_frame.iloc[0]["TRANSFORMED_RECORD"]
            ):
                logger.debug("Rendering jinja template")
                env = Environment()
                # examine the plugin instance for jinja_filter decorated methods
                if self.plugin_instance is not None:
                    for name in dir(self.plugin_instance):
                        member = getattr(self.plugin_instance, name)
                        if callable(member) and hasattr(member, "is_jinja_filter"):
                            logger.debug(f"Adding jinja filter to environment: {name}")
                            env.filters[name] = member

                def do_jinja_render(jinja_env, row_value):
                    logger.debug(f"do_jinja_render: {row_value}")
                    jinja_template = jinja_env.from_string(row_value["jinja_template"])
                    try:
                        rendered_result = jinja_template.render(
                            {"row": row_value["source_record"]}
                        )
                        logger.debug(
                            f"Individual jinja rendering result: {rendered_result}"
                        )
                        return rendered_result
                    except TypeError as type_error:
                        # re-throw as a template error so that we can handle it nicely
                        logger.error("Error during jinja render", exc_info=True)
                        raise jinja2.TemplateError(str(type_error)) from type_error

                # bit iffy about using apply since historically it's not guaranteed only-once, apparently tries to be clever with vectorizing
                data_frame["TRANSFORMED_RECORD"] = data_frame.apply(
                    lambda row: do_jinja_render(env, row["TRANSFORMED_RECORD"]), axis=1
                )
                # if it breaks things in future, switch to iterrows() and at[]
        return data_frame

    def get_records(
        self,
        sync_actions: Optional[List[OutboundSyncAction]] = None,
        batched: bool = False,
        render_jinja: bool = True,
        sort_column: Optional[str] = None,
        sort_direction: SortDirectionType = "desc",
    ) -> pandas.DataFrame | Iterable[pandas.DataFrame]:
        """
        Retrieves a dataframe of records to create,update or delete in the app.
        :param List[OutboundSyncAction] sync_action: Which sync actions to included (includes all standard actions by default)
        :param bool batched: If set to true, requests an iterator for a batch of dataframes. This is needed if a large data size (multiple GBs or more) is expected, so that the whole dataset isn't held in memory at one time.
        :param bool render_jinja: If set to true and a jinja template is used, renders it automatically.
        :param str sort_column: Applies a sort order to the dataframe.
        :param SortDirectionType sort_direction: The sort direction, 'asc' or 'desc'
        :type SortDirectionType: Literal['asc','desc']
        :return: A pandas dataframe if batched is False (the default), otherwise an iterator of pandas dataframes
        :rtype: pandas.DataFrame or iterator
        """
        if sync_actions is None:
            sync_actions = [
                action() for action in list(STANDARD_OUTBOUND_SYNC_ACTIONS.values())
            ]
        # ignore null sync actions
        sync_action_names: List[str] = [s.action_name for s in sync_actions if s]
        # only used by testing framework when running a behave test
        if self._prebaked_record_state is not None:
            logger.info("returning prebaked record state")
            dataframe = self._prebaked_record_state[
                self._prebaked_record_state["SYNC_ACTION"].isin(sync_action_names)
            ]  # pylint: disable=unsubscriptable-object
            if len(dataframe) == 0 or not batched:
                # no need to do the whole FixedSizeGenerator thing for 0 records
                return self.__dataframe_wrapper(dataframe, render_jinja)
            # we use map to create an iterable wrapper around the pandas batches which are also iterable
            # we use an intermediate partial to allow us to pass the extra parameter
            mapfunc = partial(self.__dataframe_wrapper, render_jinja=render_jinja)
            return map(mapfunc, [dataframe])
        with self._snowflake_query_lock:
            dataframe = (
                self._session.table(self._full_records_table_name)
                .filter((col("SYNC_ACTION").in_(sync_action_names)))  # type: ignore
                .select(
                    col("IDENTIFIER"),col("APP_IDENTIFIER"),col("RESULT"), col("SYNC_ACTION"), col("TRANSFORMED_RECORD"), col("TRANSFORMED_RECORD_PREVIOUS")
                )
            )
        # apply sorting
        if sort_column is not None:
            sort_col = col(sort_column)
            sorted_col = sort_col.desc() if sort_direction == "desc" else sort_col.asc()
            dataframe = dataframe.sort(sorted_col)
        if batched:
            # we use map to create an iterable wrapper around the pandas batches which are also iterable
            # we use an intermediate partial to allow us to pass the extra parameter
            mapfunc = partial(self.__dataframe_wrapper, render_jinja=render_jinja)
            return map(mapfunc, dataframe.to_pandas_batches())
            # return map(self.__dataframe_wrapper,dataframe.to_pandas_batches(),render_jinja)
        return self.__dataframe_wrapper(dataframe.to_pandas(), render_jinja)


class InboundSyncRequest(SyncRequest):
    """
    Encapsulates a request to retrieve records from an application.
    """

    def __init__(
        self,
        run_id: int,
        session: Session,
        source_app_name: str,
        results_schema_name: str,
        results_table_name: str,
        plugin_instance: OmnataPlugin,
        api_limits: List[ApiLimits],
        rate_limit_state_all: Dict[str, RateLimitState],
        rate_limit_state_this_sync_and_branch: Dict[str, RateLimitState],
        run_deadline: datetime.datetime,
        streams: List[StoredStreamConfiguration],
        omnata_log_handler:OmnataPluginLogHandler,
        development_mode: bool = False,
        test_replay_mode: bool = False,
        sync_id: Optional[int] = None,
        branch_name: Optional[str] = None
    ):
        """
        Constructs a record apply request.

        :param int sync_id: The ID number for the sync, only used internally
        :param int sync_slug: The slug for the sync, only used internally
        :param int sync_branch_id: The ID number for the sync branch (optional), only used internally
        :param int sync_branch_name: The name of the branch (main or otherwise), only used internally
        :param int run_id: The ID number for the run, only used internally
        :param any session: The snowpark session object, only used internally
        :param OmnataPlugin plugin_instance: The instance of the Omnata Plugin this request is for
        :param ApiLimits api_limits: Constraints to observe when performing HTTP requests
        :param bool development_mode: In development mode, apply_results_queue does not load into Snowflake, instead they are cached locally and can be retrieved via get_queued_results
        :param StoredStreamConfiguration streams: The configuration for each stream to fetch
        :param bool test_replay_mode: When enabled, it is safe to assume that HTTP requests are hitting a re-recorded log, so there is no need to wait in between polling
        :return: nothing
        """
        self.streams = streams
        self._streams_dict: Dict[str, StoredStreamConfiguration] = {
            s.stream_name: s for s in streams
        }
        self._stream_record_counts: Dict[str, int] = {
            stream_name: 0 for stream_name in self._streams_dict.keys()
        }
        
        # These are similar to the results, but represent requests to delete records by some criteria
        self._temp_tables = {}
        self._temp_table_lock = threading.Lock()
        self._results_exist: Dict[
            str, bool
        ] = {}  # track whether or not results exist for stream
        self._total_records_estimate: Optional[Dict[str,int]] = {}
        self._stream_change_counts: Dict[str, int] = {
            stream_name: 0 for stream_name in self._streams_dict.keys()
        }
        self._completed_streams: List[str] = []
        self.streams_requiring_view_refresh: List[str] = []
        self._omnata_log_handler = omnata_log_handler
        SyncRequest.__init__(
            self,
            run_id=run_id,
            session=session,
            source_app_name=source_app_name,
            results_schema_name=results_schema_name,
            results_table_name=results_table_name,
            plugin_instance=plugin_instance,
            api_limits=api_limits,
            rate_limit_state_all=rate_limit_state_all,
            rate_limit_state_this_sync_and_branch=rate_limit_state_this_sync_and_branch,
            run_deadline=run_deadline,
            development_mode=development_mode,
            test_replay_mode=test_replay_mode,
            sync_id=sync_id,
            branch_name=branch_name
        )
        # The results table name is also used to derive several other table/stage names
        results_table = FullyQualifiedTable(
            database_name= self._source_app_name,
            schema_name= self._results_schema_name,
            table_name= self._results_table_name
        )
        self._criteria_deletes_table_name = results_table.get_fully_qualified_criteria_deletes_table_name()
        self.state_register_table_name = results_table.get_fully_qualified_state_register_table_name()
        # this is keyed on stream name, each containing a list of dataframes and state updates mixed
        self._apply_results: Dict[str, List[RecordsToUploadResult | StateResult | CriteriaDeleteResult]] = {}
        # track the start times of each stream, so we can calculate durations. The int is a epoch (time.time()) value
        self._stream_start_times: Dict[str, int] = {}

    def apply_results_queue(self):
        """
        Merges all of the queued results and applies them, including state updates.
        """
        logger.debug("InboundSyncRequest apply_results_queue")
        if self._apply_results is not None:
            with self._apply_results_lock:
                records_to_upload:List[pandas.DataFrame] = []
                criteria_deletes_to_upload:List[pandas.DataFrame] = []
                stream_states_for_upload:Dict[str, Dict[str, Any]] = {}
                for stream_name, stream_results in self._apply_results.items():
                    # the stream results contains an ordered sequence of dataframes and state updates (append only)
                    # we only want to apply the dataframes up until the most recent state update
                    # so first, we iterate backwards to find the last state update
                    last_state_index = -1
                    for i in range(len(stream_results) - 1, -1, -1):
                        if isinstance(stream_results[i], StateResult):
                            last_state_index = i
                            stream_states_for_upload[stream_name] = stream_results[i].new_state
                            break
                    # if there are no state updates, we can't do anything with this stream
                    if last_state_index == -1:
                        logger.debug(
                            f"No state updates for stream {stream_name}, skipping"
                        )
                        continue
                    assert isinstance(stream_states_for_upload[stream_name], dict), "Latest state must be a dictionary"
                    # now we can take the record dataframes up to the last state update
                    results_subset = stream_results[:last_state_index]
                    non_empty_record_dfs:List[pandas.DataFrame] = [
                        x.records for x in results_subset 
                        if x is not None and isinstance(x, RecordsToUploadResult) and len(x.records) > 0
                    ]
                    # get the total length of all the dataframes
                    total_length = sum([len(x) for x in non_empty_record_dfs])
                    # add the count of this batch to the total for this stream
                    self._stream_record_counts[
                        stream_name
                    ] = self._stream_record_counts[stream_name] + total_length
                    records_to_upload.extend(non_empty_record_dfs)
                    # also handle any criteria deletes
                    criteria_deletes_to_upload.extend([
                        x.criteria_deletes for x in results_subset
                        if x is not None and isinstance(x, CriteriaDeleteResult) and len(x.criteria_deletes) > 0
                    ])
                    # now remove everything up to the last state update
                    # we do this so that we don't apply the same state update multiple times
                    # keep everything after the last state update
                    self._apply_results[stream_name] = stream_results[
                        last_state_index + 1 :
                    ]
                
                if len(records_to_upload) > 0 or len(criteria_deletes_to_upload) > 0:
                    if len(records_to_upload) > 0:
                        logger.debug(
                            f"Applying {len(records_to_upload)} batches of queued results"
                        )
                        # upload all cached apply results
                        records_to_upload_combined = pandas.concat(records_to_upload)
                        self._apply_results_dataframe(list(stream_states_for_upload.keys()), records_to_upload_combined)
                        # now that the results have been updated, we need to insert records into the state register table
                        # we do this by inserting the latest state for each stream
                    if len(criteria_deletes_to_upload) > 0:
                        logger.debug(
                            f"Applying {len(criteria_deletes_to_upload)} batches of queued criteria deletes"
                        )
                        # upload all cached apply results
                        all_criteria_deletes = pandas.concat(criteria_deletes_to_upload)
                        self._apply_criteria_deletes_dataframe(all_criteria_deletes)
                    
                    query_id = self._get_query_id_for_now()
                    self._directly_insert_to_state_register(
                        stream_states_for_upload, query_id=query_id
                    )
        

        # update the inbound stream record counts, so we can see progress
        # we do this last, because marking a stream as completed will cause the sync engine to process it
        # so we need to make sure all the results are applied first
        self.apply_progress_updates()
    
    def _directly_insert_to_state_register(
            self, stream_states_for_upload: Dict[str, Dict[str, Any]],
            query_id: Optional[str] = None
    ) -> str:
        binding_values = []
        select_clauses = []
        
        with self._snowflake_query_lock:
            if query_id is None:
                query_id = self._get_query_id_for_now()
            for stream_name, latest_state in stream_states_for_upload.items():
                binding_values.extend([stream_name, query_id, json.dumps(latest_state)])
                select_clauses.append(
                    f"select ?, ?, PARSE_JSON(?)"
                )
            final_query = f"""INSERT INTO {self.state_register_table_name} (STREAM_NAME, QUERY_ID, STATE_VALUE)
                {' union all '.join(select_clauses)}"""
            self._session.sql(final_query, binding_values).collect()
            streams_included = list(stream_states_for_upload.keys())
            logger.debug(f"Inserted state for streams: {streams_included} with query ID {query_id}")
    
    def apply_progress_updates(self, ignore_errors:bool = True):
        """
        Sends a message to the plugin with the current progress of the sync run, if it has changed since last time.
        """
        with self._apply_results_lock:
            new_progress_update = PluginMessageStreamProgressUpdate(
                    stream_total_counts=self._stream_record_counts,
                    # records could have been marked as completed, but still have results to apply
                    completed_streams=[s for s in self._completed_streams 
                        if s not in self._apply_results 
                            or self._apply_results[s] is None
                            or len(self._apply_results[s]) == 0],
                    stream_errors=self._omnata_log_handler.stream_global_errors,
                    total_records_estimate=self._total_records_estimate
                )
        if self._last_stream_progress_update is None or new_progress_update != self._last_stream_progress_update:
            result = self._plugin_message(
                message=new_progress_update,
                ignore_errors=ignore_errors
            )
            if result is None:
                return False
            self._last_stream_progress_update = new_progress_update
        completed_streams_awaiting_results_upload = [
            s for s in self._completed_streams if s in self._apply_results and self._apply_results[s] is not None
        ]
        if len(completed_streams_awaiting_results_upload) > 0:
            logger.debug(
                f"Streams marked as completed but awaiting upload: {', '.join(completed_streams_awaiting_results_upload)}"
            )
        return True

    def apply_cancellation(self):
        """
        Signals an interruption to the load process for the other threads.
        Also updates the Sync Run to include which streams were cancelled.
        """
        # set the token so that the other threads stop
        self._thread_cancellation_token.set()
        # any stream which didn't complete at this point is considered cancelled
        cancelled_streams = [
            stream.stream_name
            for stream in self.streams
            if stream.stream_name not in self._completed_streams
        ]
        self._plugin_message(
            message=PluginMessageCancelledStreams(cancelled_streams=cancelled_streams)
        )

    def apply_deadline_reached(self):
        """
        Signals an interruption to the load process for the other threads.
        Also updates the Sync Run to include which streams were abandoned.
        """
        # set the token so that the other threads stop
        self._thread_cancellation_token.set()
        # any stream which didn't complete at this point is considered abandoned
        abandoned_streams = [
            stream.stream_name
            for stream in self.streams
            if stream.stream_name not in self._completed_streams
        ]
        self._plugin_message(
            message=PluginMessageAbandonedStreams(abandoned_streams=abandoned_streams)
        )

    def enqueue_results(self, stream_name: str, results: List[Dict], new_state: Any, is_delete:Union[bool,List[bool]] = False):
        """
        Adds some results to the queue for applying asynchronously.
        stream_name: str, the name of the stream
        results: List[Dict], the results to enqueue
        new_state: Any, the new state which applies to the stream, given the new results
        is_delete: Union[bool,List[bool]], whether the results are deletes or not
        is_delete can be a single value, which means all results are the same, or a list of booleans, which means each result is different
        For records where is_delete is True, you can provide the current record value if it is known, or just the identifier
        """
        logger.info(f"Enqueueing {len(results)} results for upload")
        if stream_name is None or len(stream_name) == 0:
            raise ValueError("Stream name cannot be empty")
        with self._apply_results_lock:
            existing_results: List[RecordsToUploadResult | StateResult | CriteriaDeleteResult] = []
            if stream_name in self._apply_results:
                existing_results = self._apply_results[stream_name]
            existing_results.append(RecordsToUploadResult(
                records=self._preprocess_results_list(stream_name, results, is_delete)
            ))
            if new_state is not None:
                existing_results.append(
                    StateResult(new_state=new_state)
                )  # append the new state at the end
            self._apply_results[stream_name] = existing_results
        if self.development_mode is False:
            # note: we want to do it for all values in self._apply_results, not just the new one
            self._apply_results_if_size_exceeded()
    
    def _apply_results_if_size_exceeded(self,):
        # so first we need to get the list of lists from the dictionary values and flatten it
        # then we can sum the memory usage of each dataframe
        # if the total exceeds 200MB, we apply the results immediately
        all_df_lists:List[List[RecordsToUploadResult | StateResult | CriteriaDeleteResult]] = list(self._apply_results.values())
        # flatten
        all_dfs:List[pandas.DataFrame] = []
        for sublist in all_df_lists:
            for x in sublist:
                if isinstance(x, RecordsToUploadResult):
                    all_dfs.append(x.records)
                if isinstance(x, CriteriaDeleteResult):
                    all_dfs.append(x.criteria_deletes)
        combined_length = sum([len(x) for x in all_dfs])
        # first, don't bother if the count is less than 10000, since it's unlikely to be even close
        if combined_length > 10000:
            if sum([x.memory_usage(index=True).sum() for x in all_dfs]) > 200000000:
                logger.debug(f"Applying results queue immediately due to combined dataframe size")
                self.apply_results_queue()
    
    def delete_by_criteria(self, stream_name: str, criteria: Dict[str, Any]):
        """
        Submits some critera (field→value dict) which will cause matching records to be marked as deleted at the end of the run. 
        This feature was created primarily for array fields that become child streams.
        The parent record is updated, which means there is a set of new children, but we need to delete the previously sync'd records and we don't know their identifiers.

        The criteria is applied before the new records for the current run are applied. In other words, it will not delete any records from the current run.

        For a record to be deleted, it must match fields with all the criteria supplied. At least one field value must be provided.
        """
        if len(criteria) == 0:
            raise ValueError("At least one field value must be provided for deletion criteria")
        if stream_name not in self._streams_dict:
            raise ValueError(
                f"Cannot delete records for stream {stream_name} as its configuration doesn't exist"
            )
        # append the new criteria to the self._criteria_deletes_table_name table
        # this table has two columns:
        # STREAM_NAME: string
        # DELETE_CRITERIA: object
        with self._apply_results_lock:
            logger.debug(
                f"Enqueuing {len(criteria)} delete criteria for stream {stream_name} for upload"
            )
            existing_results: List[RecordsToUploadResult | StateResult | CriteriaDeleteResult] = []
            if stream_name in self._apply_results:
                existing_results = self._apply_results[stream_name]
            existing_results.append(
                CriteriaDeleteResult(
                    criteria_deletes=pandas.DataFrame([{"STREAM_NAME":stream_name,"DELETE_CRITERIA": criteria}])))
            self._apply_results[stream_name] = existing_results
        if self.development_mode is False:
            self._apply_results_if_size_exceeded()
    
    def mark_stream_started(self, stream_name: str):
        """
        Marks a stream as started, this is called automatically per stream when using @managed_inbound_processing.
        """
        logger.debug(f"Marking stream {stream_name} as started locally")
        self._stream_start_times[stream_name] = time.time()

    def mark_stream_complete(self, stream_name: str):
        """
        Marks a stream as completed, this is called automatically per stream when using @managed_inbound_processing.
        If @managed_inbound_processing is not used, call this whenever a stream has finished recieving records.
        """
        logger.debug(f"Marking stream {stream_name} as completed locally")
        if stream_name in self._stream_start_times:
            start_time = self._stream_start_times[stream_name]
            duration = time.time() - start_time
            stream_duration_gauge.set(
                amount=duration,
                attributes={
                    "stream_name": stream_name,
                    "sync_run_id": str(self._run_id),
                    "sync_id": str(self._sync_id),
                    "branch_name": str(self._branch_name) if self._branch_name is not None else 'main',
                    "sync_direction": "inbound",
                    "plugin_id": self.plugin_instance.get_manifest().plugin_id,
                },
            )
        with self._apply_results_lock:
            self._completed_streams.append(stream_name)
            # dedup just in case it's called twice
            self._completed_streams = list(set(self._completed_streams))
    
    def set_stream_record_count(self, stream_name: str, count: int):
        """
        Sets the record count for a stream, used to provide progress updates.
        """
        self._stream_record_counts[stream_name] = count
    
    def set_stream_total_records_estimate(self, stream_name: str, count: int):
        """
        Sets the total record count for a stream, used to provide progress updates.
        This should be a best estimate of the number of changes which will be fetched from the source.
        In other words, as results are enqueued they should build toward reaching this number as the sync progresses.
        This does not have to be exact, it's just to give the user some feedback while the sync is running.
        Totals will always be replaced by the actual count when the stream is completed.
        """
        self._total_records_estimate[stream_name] = count

    def _enqueue_state(self, stream_name: str, new_state: Any):
        """
        Enqueues some new stream state to be stored. This method should not be called directly,
        instead you should store state using the new_state parameter in the enqueue_results
        method to ensure it's applied along with the associated new records.
        """
        self.enqueue_state(
            stream_name=stream_name,
            new_state=new_state,
            query_id=None  # query_id will be generated automatically if not provided
        )
    
    def enqueue_state(self, stream_name: str, new_state: Any, query_id: Optional[str] = None):
        """
        Enqueues some new stream state to be stored. This method should be called whenever the state of a stream changes.
        
        If there have been records enqueued here for this stream, it is assumed that the state is related to those records.
        In this case, the state will be applied after the records are applied.
        If there are no records enqueued for this stream, the state will be applied immediately as it is assumed that the results
        were directly inserted, and therefore we need to capture the current query ID before more results are inserted.
        """
        with self._apply_results_lock:
            if stream_name in self._apply_results:
                if len(self._apply_results[stream_name]) > 0:
                    self._apply_results[stream_name].append(new_state)
                    return
        
        self._directly_insert_to_state_register(
            {
                stream_name: new_state
            }, query_id=query_id
        )
        

    def _get_query_id_for_now(self):
        """
        Gets a Snowflake query ID right now. Note that this does not require a Snowflake lock, the caller 
        should ensure that this is called in a thread-safe manner.
        """
        job=self._session.sql("select 1").collect_nowait()
        job.result()
        return job.query_id

    def get_queued_results(self, stream_name: str):
        """
        Returns results queued during processing
        """
        if (
            stream_name not in self._apply_results
            or len(self._apply_results[stream_name]) == 0
        ):
            raise ValueError(
                "get_queued_results was called, but no results have been queued"
            )
        concat_results = pandas.concat(self._apply_results[stream_name])
        return [c for c in concat_results if c is not None and isinstance(c, pandas.DataFrame) and len(c) > 0]

    def _convert_by_json_schema(
        self, stream_name: str, data: Dict, json_schema: Dict
    ) -> Dict:
        """
        Apply opportunistic normalization before loading into Snowflake
        """
        try:
            datetime_properties = [
                k
                for k, v in json_schema["properties"].items()
                if "format" in v and v["format"] == "date-time"
            ]
            for datetime_property in datetime_properties:
                try:
                    if datetime_property in data and data[datetime_property] is not None:
                        contains_forward_slash = "/" in data[datetime_property]
                        data[datetime_property] = parse(
                            data[datetime_property],
                            dayfirst=contains_forward_slash # no self respecting API should be using US date formats
                        ).isoformat()
                except Exception as exception2:
                    logger.debug(
                        f"Failure to convert inbound data property {datetime_property} on stream {stream_name}: {str(exception2)}"
                    )
        except Exception as exception:
            logger.debug(f"Failure to convert inbound data: {str(exception)}")
        return data

    def _preprocess_results_list(self, stream_name: str, results: List[Dict],is_delete:Union[bool,List[bool]]) -> pandas.DataFrame:
        """
        Creates a dataframe from the enqueued list, ready to upload.
        The result is a dataframe contain all (and only):
        'APP_IDENTIFIER' string
        'STREAM_NAME' string
        'RETRIEVE_DATE' datetime (UTC)
        'RECORD_DATA' object,
        'IS_DELETED' boolean
        """
        # for required_column in ['RECORD_DATA']:
        #    if required_column not in results_df.columns:
        #        raise ValueError(f'{required_column} column was not included in results')
        if stream_name not in self._streams_dict:
            raise ValueError(
                f"Cannot preprocess results for stream {stream_name} as its configuration doesn't exist"
            )
        logger.debug(f"preprocessing for stream: {self._streams_dict[stream_name]}")
        if len(results) > 0:
            if isinstance(is_delete, list):
                if len(results) != len(is_delete):
                    raise ValueError(f"results and is_delete lists must be the same length")
            # We need to remove any values (included nesting) which are empty dicts. This is to prevent the arrow error: 
            # Cannot write struct type '<field_name>' with no child field to Parquet. Consider adding a dummy child field.
            results = [remove_empty_dict_values(result) for result in results]
            stream_obj: StreamConfiguration = self._streams_dict[stream_name].stream
            results_df = pandas.DataFrame.from_dict(
                [
                    {
                        "RECORD_DATA": self._convert_by_json_schema(
                            stream_name, data, stream_obj.json_schema  # type: ignore
                        )
                    }
                    for data in results
                ]
            )
            primary_key_field = None
            records = results_df.to_dict("records")
            # this extra bit of source_defined_primary_key logic is just to catch the situation where the plugin accidentally
            # provides an empty list as the source defined primary key (SFMC plugin did this for a while, so some customers have [] here).
            # This should be caught upstream during configuration, but we'll check here too.
            # Note that source defined primary keys override any user choice.
            primary_key_correctly_defined_by_source = False
            if stream_obj.source_defined_primary_key is not None:
                if isinstance(stream_obj.source_defined_primary_key,list):
                    if len(stream_obj.source_defined_primary_key)>0:
                        primary_key_correctly_defined_by_source = True
                else:
                    primary_key_correctly_defined_by_source = True
            
            if primary_key_correctly_defined_by_source:
                primary_key_field = stream_obj.source_defined_primary_key
            elif self._streams_dict[stream_name].primary_key_field is not None:
                primary_key_field = self._streams_dict[stream_name].primary_key_field
            else:
                # originally, we did not require primary keys for inbound syncs if they were doing the replace option
                # when we brought in delete flagging, we began to mandate that primary keys are defined
                raise ValueError(f"Stream {stream_name} does not have a primary key field defined")
            if isinstance(primary_key_field,list) and len(primary_key_field) == 1:
                # don't hash it if it's just a single value
                primary_key_field = primary_key_field[0]
            if isinstance(primary_key_field,list):
                primary_key_fields = cast(List[str],primary_key_field)
                primary_key_fields = sorted(primary_key_fields)
                # handle the sitation where the primary key is a list of fields
                # first, check that all records contain all of the primary key fields
                if not all(
                    all(
                        field in record["RECORD_DATA"]
                        for field in primary_key_fields
                    )
                    for record in records
                ):
                    raise ValueError(
                        f"Primary key fields '{primary_key_fields}' were not present in all records for stream {stream_name}"
                    )
                # hash all of the primary key fields
                results_df["APP_IDENTIFIER"] = results_df["RECORD_DATA"].apply(lambda x: self.get_hash([str(x[field]) for field in primary_key_fields]))
            else:
                # the primary key field could contain a nested field, so we need to check for that
                # we need to check that each record in the results contains the primary key field
                if not all(
                    primary_key_field in record["RECORD_DATA"]
                    for record in records
                ):
                    if "." in primary_key_field:
                        primary_key_field = primary_key_field.split(".")

                        if not all(
                            get_nested_value(record["RECORD_DATA"], primary_key_field)
                            for record in records
                        ):
                            raise ValueError(
                                f"Primary key field '{primary_key_field}' was not present in all records for stream {stream_name}"
                            )
                    else:
                        raise ValueError(
                            f"Primary key field '{primary_key_field}' was not present in all records for stream {stream_name}"
                        )
                results_df["APP_IDENTIFIER"] = results_df["RECORD_DATA"].apply(lambda x: get_nested_value(dict(x),primary_key_field))
            # ensure APP_IDENTIFIER is a string
            results_df["APP_IDENTIFIER"] = results_df["APP_IDENTIFIER"].apply(str)
            # the timestamps in Snowflake are TIMESTAMP_LTZ, so we upload in string format to ensure the
            # timezone information is present.
            results_df["RETRIEVE_DATE"] = str(datetime.datetime.now().astimezone())
            # create the IS_DELETED column from the is_delete list
            results_df["IS_DELETED"] = is_delete
            # for each record, if IS_DELETED is true and RECORD_DATA only contains a single key, we assume that's the identifier
            # in this case, we nullify the RECORD_DATA column to indicate that the delete operation does not contain the full record
            for index, row in results_df.iterrows():
                if row["IS_DELETED"] and len(row["RECORD_DATA"]) == 1:
                    results_df.at[index, "RECORD_DATA"] = None
            # we dump the record data to a json string to make uploading to Snowflake less error prone, but only if it's not None
            results_df["RECORD_DATA"] = results_df["RECORD_DATA"].apply(
                lambda x: json.dumps(x) if x is not None else None
            )
            results_df["STREAM_NAME"] = stream_name
        else:
            results_df = pandas.DataFrame(
                [],
                columns=[
                    "APP_IDENTIFIER",
                    "STREAM_NAME",
                    "RECORD_DATA",
                    "RETRIEVE_DATE",
                    "IS_DELETED"
                ],
            )
        # trim out the columns we don't need to return
        return results_df[
            results_df.columns.intersection(
                ["APP_IDENTIFIER", "STREAM_NAME", "RECORD_DATA", "RETRIEVE_DATE", "IS_DELETED"]
            )
        ]
    
    def get_hash(self, keys:List[str]) -> str:
        """
        Creates a hash from a list of keys. 
        The function will join the keys with an underscore and then create a 
        SHA256 hash from the string. The function will return the hash as a string.
        """
        key_string = "_".join(keys)
        hash_object = hashlib.sha256(key_string.encode())
        return hash_object.hexdigest()

    def _apply_results_dataframe(self, stream_names: List[str], results_df: pandas.DataFrame):
        """
        Applies results for an inbound sync. The results are staged into a temporary
        table in Snowflake, so that we can make an atomic commit at the end.
        Returns a query ID that can be used for checkpointing after the copy into command has run.
        """
        if len(results_df) > 0:
            with self._snowflake_query_lock:
                with tracer.start_as_current_span("apply_results"):
                    for attempt in Retrying(stop=stop_after_attempt(30),wait=wait_fixed(2),reraise=True,retry=retry_if_exception_message(match=".*(is being|was) committed.*")):
                        with attempt:
                            logger.debug(
                                f"Applying {len(results_df)} results to {self._full_results_table_name}"
                            )
                            # try setting parquet engine here, since the engine parameter does not seem to make it through to the write_pandas function
                            success, nchunks, nrows, _ = write_pandas(
                                conn=self._session._conn._cursor.connection,  # pylint: disable=protected-access
                                df=results_df,
                                table_name=self._full_results_table_name,
                                quote_identifiers=False,  # already done in get_temp_table_name
                                # schema='INBOUND_RAW', # it seems to be ok to provide schema in the table name
                                table_type="transient"
                            )
                            if not success:
                                raise ValueError(
                                    f"Failed to write results to table {self._full_results_table_name}"
                                )
                            logger.debug(
                                f"Wrote {nrows} rows and {nchunks} chunks to table {self._full_results_table_name}"
                            )
                            # temp tables aren't allowed
                            # snowflake_df = self._session.create_dataframe(results_df)
                            # snowflake_df.write.save_as_table(table_name=temp_table,
                            #                                mode='append',
                            #                                column_order='index',
                            #                                #create_temp_table=True
                            #                                )
                            for stream_name in stream_names:
                                self._results_exist[stream_name] = True
        else:
            logger.debug("Results dataframe is empty, not applying")

    def _apply_criteria_deletes_dataframe(self, results_df: pandas.DataFrame):
        """
        Applies results for an inbound sync. The results are staged into a temporary
        table in Snowflake, so that we can make an atomic commit at the end.
        """
        if len(results_df) > 0:
            with self._snowflake_query_lock:
                for attempt in Retrying(stop=stop_after_attempt(30),wait=wait_fixed(2),reraise=True,retry=retry_if_exception_message(match=".*(is being|was) committed.*")):
                    with attempt:
                        logger.debug(
                            f"Applying {len(results_df)} criteria deletes to {self._criteria_deletes_table_name}"
                        )
                        # try setting parquet engine here, since the engine parameter does not seem to make it through to the write_pandas function
                        success, nchunks, nrows, _ = write_pandas(
                            conn=self._session._conn._cursor.connection,  # pylint: disable=protected-access
                            df=results_df,
                            table_name=self._criteria_deletes_table_name,
                            quote_identifiers=False,  # already done in get_temp_table_name
                            table_type="transient"
                        )
                        if not success:
                            raise ValueError(
                                f"Failed to write results to table {self._criteria_deletes_table_name}"
                            )
                        logger.debug(
                            f"Wrote {nrows} rows and {nchunks} chunks to table {self._criteria_deletes_table_name}"
                        )
                        return
        else:
            logger.debug("Results dataframe is empty, not applying")


class ConnectResponse(SubscriptableBaseModel):
    """
    Encapsulates the response to a connection request. This is used to pass back any additional
    information that may be discovered during connection that's relevant to the plugin (e.g. Account Identifiers).
    You can also specifies any additional network addresses that are needed to connect to the app, that might not
    have been known until the connection was made.
    """

    connection_parameters: Dict[str,StoredConfigurationValue] = {}
    connection_secrets: Dict[str,StoredConfigurationValue] = {}
    network_addresses: List[str] = []


class SnowflakeBillingEvent(BaseModel):
    """
    The inputs to Snowflake's SYSTEM$CREATE_BILLING_EVENT function.
    See https://docs.snowflake.com/en/sql-reference/functions/system_create_billing_event
    """

    billing_class: str
    base_charge: Decimal
    timestamp: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)
    sub_class: Optional[str] = None
    start_timestamp: Optional[datetime.datetime] = None
    objects: List[str] = []
    additional_info: Dict[str, Any] = {}

    @model_validator(mode='after')
    def validate_datetime_fields(self) -> Self:
        # Handling timestamps, we want to be strict on supplying a timezone
        timestamp = self.timestamp
        if timestamp is not None and isinstance(timestamp, datetime.datetime):
            if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
                raise ValueError("timestamp must be timezone aware")
        
        start_timestamp = self.start_timestamp
        if start_timestamp is not None and isinstance(start_timestamp, datetime.datetime):
            if start_timestamp.tzinfo is None or start_timestamp.tzinfo.utcoffset(start_timestamp) is None:
                raise ValueError("start_timestamp must be timezone aware")
        return self

class DailyBillingEventRequest(BaseModel):
    """
    Represents a request to provide billing events for that day.
    These will occur at midnight, and cover the previous 24 hours.
    Provides enough information for the plugin to create billing events for the day.
    """

    billing_schedule: Literal["DAILY"] = "DAILY"
    billable_connections_inbound: int = 0
    billable_connections_outbound: int = 0
    ngrok_connections_inbound: int = 0
    ngrok_connections_outbound: int = 0
    # below is deprecated
    has_active_inbound: bool = False
    has_active_outbound: bool = False

class MonthlyBillingEventRequest(BaseModel):
    """
    Represents a request to provide billing events for that month.
    These will occur at midnight on the first of each month, and cover the whole previous month.
    Currently, these exist to provide a way to bill for the number of active ngrok connections
    and associated data overages.
    """

    billing_schedule: Literal["MONTHLY"] = "MONTHLY"
    distinct_active_ngrok_connections: int = 0
    ngrok_data_usage_bytes: int = 0
    # below is deprecated
    has_active_inbound: bool = False
    has_active_outbound: bool = False
    # had to add these because the old version of the standard billing events assumed a daily billing event
    # TODO: deprecate all of these once the plugins are all on 0.3.26 or higher
    billable_connections_inbound: int = 0
    billable_connections_outbound: int = 0


BillingEventRequest = Annotated[Union[DailyBillingEventRequest,MonthlyBillingEventRequest],Field(discriminator='billing_schedule')]


class OmnataPlugin(ABC):
    """
    Class which defines the contract for an Omnata Push Plugin
    """

    def __init__(self):
        """
        Plugin constructors must never take parameters
        """
        self._sync_request: Optional[SyncRequest] = None
        # the current parameters are available here for the benefit of jinja filters,
        # so that they don't get in the way of the other function arguments
        self._configuration_parameters: Optional[SyncConfigurationParameters] = None
        # the Snowpark session shouldn't need to be used, ordinarily
        self._session: Optional[Session] = None
        self.disable_background_workers = False
        """
        disable_background_workers prevents the Python background workers from starting, which
        take care of various status updates and loading enqueued results.
        Only set this to True if you plan to do all of this yourself (e.g. in a Java stored proc)
        """
        # store the opentelemetry context so that it can be attached inside threads
        self.opentelemetry_context = context.get_current()
    

    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        """
        Returns a manifest object to describe the plugin and its capabilities
        """
        raise NotImplementedError(
            "Your plugin class must implement the get_manifest method"
        )

    @abstractmethod
    def connection_form(self,connectivity_option:ConnectivityOption) -> List[ConnectionMethod]:
        """
        Returns a form definition so that user input can be collected, in order to connect to an app

        :return A list of ConnectionMethods, each of which offer a way of authenticating to the app and describing what information must be captured
        :rtype List[ConnectionMethod]
        """
        raise NotImplementedError(
            "Your plugin class must implement the connection_form method"
        )

    @abstractmethod
    def network_addresses(
        self, parameters: ConnectionConfigurationParameters
    ) -> List[str]:
        """
        Returns a list of network addresses that are required to connect to the app.
        This will be called after the connection form is completed, so that collected information can be used to build the list.
        Note that at this point, no external access is possible.

        :param ConnectionConfigurationParameters parameters the parameters of the connection, configured so far.
        :return A list of domains that will be added to a network rule to permit outbound access from Snowflake
        for the authentication step. Note that for OAuth Authorization flows, it is not necessary to provide the
        initial URL that the user agent is directed to.
        :rtype List[str]
        """
        raise NotImplementedError(
            "Your plugin class must implement the network_addresses method"
        )

    def outbound_configuration_form(
        self, parameters: OutboundSyncConfigurationParameters
    ) -> OutboundSyncConfigurationForm:
        """
        Returns a form definition so that user input can be collected. This function may be called repeatedly with new parameter values
        when dependant fields are used

        :param OutboundSyncConfigurationParameters parameters the parameters of the sync, configured so far.
        :return A OutboundSyncConfigurationForm, which describes what information must be collected to configure the sync
        :rtype OutboundSyncConfigurationForm
        """
        raise NotImplementedError(
            "Your plugin class must implement the outbound_configuration_form method"
        )

    def inbound_configuration_form(
        self, parameters: InboundSyncConfigurationParameters
    ) -> InboundSyncConfigurationForm:
        """
        Returns a form definition so that user input can be collected. This function may be called repeatedly with new parameter values
        when dependant fields are used

        :param InboundSyncConfigurationParameters parameters the parameters of the sync, configured so far.
        :return A InboundSyncConfigurationForm, which describes what information must be collected to configure the sync
        :rtype InboundSyncConfigurationForm
        """
        raise NotImplementedError(
            "Your plugin class must implement the inbound_configuration_form method"
        )

    def outbound_tuning_parameters(
        self, parameters: OutboundSyncConfigurationParameters
    ) -> OutboundSyncConfigurationForm:
        """
        Returns the form definition for declaring outbound tuning parameters.

        The returned form should consist of static fields with default values that represent the
        plugin's recommended runtime behaviour. This form is optional and is only rendered when a
        user opts to override those defaults at sync runtime, so it must be safe to fall back to the
        provided defaults when no tuning parameters are configured.

        :param OutboundSyncConfigurationParameters parameters the current outbound configuration
        :return: An OutboundSyncConfigurationForm describing the available tuning parameters
        :rtype: OutboundSyncConfigurationForm
        """
        return OutboundSyncConfigurationForm(fields=[])

    def inbound_tuning_parameters(
        self, parameters: InboundSyncConfigurationParameters
    ) -> InboundSyncConfigurationForm:
        """
        Returns the form definition for declaring inbound tuning parameters.

        The returned form should consist of static fields with default values that represent the
        plugin's recommended runtime behaviour. This form is optional and is only rendered when a
        user opts to override those defaults at sync runtime, so it must be safe to fall back to the
        provided defaults when no tuning parameters are configured.

        :param InboundSyncConfigurationParameters parameters the current inbound configuration
        :return: An InboundSyncConfigurationForm describing the available tuning parameters
        :rtype: InboundSyncConfigurationForm
        """
        return InboundSyncConfigurationForm(fields=[])
    
    def inbound_stream_list(
        self, parameters: InboundSyncConfigurationParameters
    ) -> List[StreamConfiguration]:
        """
        Returns a list of streams which can be sync'd from the app. This function is called after the form returned by inbound_configuration_form
        has been completed, so that collected information can be used to build the list.

        :param InboundSyncConfigurationParameters parameters the parameters of the sync
        :return A list of streams which can be sync'd from the app. This may vary based on the parameters provided.
        :rtype List[StreamConfiguration]
        """
        raise NotImplementedError(
            "Your plugin class must implement the inbound_stream_list method"
        )

    @abstractmethod
    def connect(self, parameters: ConnectionConfigurationParameters) -> ConnectResponse:
        """
        Connects to an app, validating that the information provided by the user was correct.
        For OAuth connection methods, this will be called after the OAuth flow has completed, so the
        access token will be available in the parameters.

        :param PluginConfigurationParameters parameters the parameters of the sync, as configured by the user
        :return A ConnectResponse, which may provide further information about the app instance for storing
        :rtype ConnectResponse
        :raises ValueError: if issues were encountered during connection
        """
        raise NotImplementedError("Your plugin class must implement the connect method")

    def sync_outbound(
        self,
        parameters: OutboundSyncConfigurationParameters,
        outbound_sync_request: OutboundSyncRequest,
    ):
        """
        Applies a set of changed records to an app. This function is called whenever a run occurs and changed records
        are found.
        To return results, invoke outbound_sync_request.enqueue_results() during the load process.

        :param PluginConfigurationParameters parameters the parameters of the sync, as configured by the user
        :param OutboundSyncRequest outbound_sync_request an object describing what has changed
        :return None
        :raises ValueError: if issues were encountered during connection
        """
        raise NotImplementedError(
            "Your plugin class must implement the sync_outbound method"
        )

    def outbound_record_validator(
        self,
        sync_parameters: Dict[str, StoredConfigurationValue],
        field_mappings: StoredMappingValue,
        transformed_record: Dict[str, Any],
        source_types: Dict[str, str],
    ) -> Optional[Dict[str, str]]:
        """
        Performs validation on a transformed record, returning errors by field name (from the transformed record) if the record is invalid, or None if the record is valid
        Parameters:
            sync_parameters: the configured sync parameters, this will be the same for all records
            field_mappings: the configured field mappings, this will be the same for all records.
                If this is an instance of StoredFieldMappings, there may be target system metadata used for validation (e.g. an ID field that must conform to a specific format)
            transformed_record: the transformed record, which is either a source column value, literal value or expression, mapped to a target field name
            source_types: a dictionary of field names to the original SQL type of the source column/literal/expression (before conversion to variant), as returned by SYSTEM$TYPEOF.
                Leveraging this information may be simpler than trying to parse the transformed values to determine if the original type is compatible
        """

    def sync_inbound(
        self,
        parameters: InboundSyncConfigurationParameters,
        inbound_sync_request: InboundSyncRequest,
    ):
        """
        Retrieves the next set of records from an application.
        The inbound_sync_request contains the list of streams to be synchronized.
        To return results, invoke inbound_sync_request.enqueue_results() during the load process.

        :param PluginConfigurationParameters parameters the parameters of the sync, as configured by the user
        :param InboundSyncRequest inbound_sync_request an object describing what needs to be sync'd
        :return None
        :raises ValueError: if issues were encountered during connection
        """
        raise NotImplementedError(
            "Your plugin class must implement the sync_inbound method"
        )

    def api_limits(self, parameters: ConnectionConfigurationParameters) -> List[ApiLimits]:
        """
        Defines the API limits in place for the app's API
        """
        return []

    def create_billing_events(self, request: BillingEventRequest) -> List[SnowflakeBillingEvent]:
        """
        Creates billing events for the day, these will be submitted to the Snowflake event billing API.
        Note that the Snowflake API is strictly rate limited, so only a very small number of events
        should be returned.
        """
        return []
    
    def omnata_standard_billing_events(self, request: BillingEventRequest,
                                             initial_charge:Decimal,
                                             additional_charge:Decimal) -> List[SnowflakeBillingEvent]:
        """
        Omnata's typical marketplace billing model (as at March 2024), is to bill the first daily event
        per connection direction with the DAILY_ACTIVE_INITIAL class, and all subsequent connection
        directions with the DAILY_ACTIVE_ADDITIONAL class.
        """
        sent_initial = False
        events: List[SnowflakeBillingEvent] = []
        if request.billing_schedule == "DAILY":
            for i in range(request.billable_connections_inbound + request.billable_connections_outbound):
                if sent_initial is False:
                    events.append(
                        SnowflakeBillingEvent(
                            billing_class="DAILY_ACTIVE_INITIAL",
                            billing_subclass="",
                            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
                            base_charge=initial_charge,
                        )
                    )
                    sent_initial = True
                else:
                    if additional_charge is not None and additional_charge > 0:
                        events.append(
                            SnowflakeBillingEvent(
                                billing_class="DAILY_ACTIVE_ADDITIONAL",
                                billing_subclass="",
                                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
                                base_charge=additional_charge,
                            )
                        )
            if request.ngrok_connections_inbound + request.ngrok_connections_outbound > 0:
                events.append(
                    SnowflakeBillingEvent(
                        billing_class="DAILY_ACTIVE_NGROK",
                        billing_subclass="",
                        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
                        base_charge=Decimal("3.00"),
                    )
                )
        return events

    def additional_loggers(self) -> List[str]:
        """
        Ordinarily, your plugin code will log to a logger named 'omnata_plugin' and these
        messages will automatically be stored in Snowflake and associated with the current
        sync run, so that they appear in the UI's logs.
        However, if you leverage third party python libraries, it may be useful to capture
        log messages from those as well. Overriding this method and returning the names of
        any additional loggers, will cause them to be captured as well.
        For example, if the source code of a third party libary includes:
        logging.getLogger(name='our_api_wrapper'), then returning ['our_api_wrapper']
        will capture its log messages.
        The capture level of third party loggers will be whatever is configured for the sync.
        """
        return []


class FixedSizeGenerator:
    """
    A thread-safe class which wraps the pandas batches generator provided by Snowflake,
    but provides batches of a fixed size.
    """

    def __init__(self, generator, batch_size):
        self.generator = generator
        # handle dataframe as well as a dataframe generator, just to be more flexible
        if self.generator.__class__.__name__ == "DataFrame":
            logger.debug(
                f"Wrapping a dataframe of length {len(self.generator)} in a map so it acts as a generator"
            )
            self.generator = map(lambda x: x, [self.generator])
        self.leftovers = None
        self.batch_size = batch_size
        self.thread_lock = threading.Lock()

    def __next__(self):
        with self.thread_lock:
            logger.debug(f"FixedSizeGenerator initial leftovers: {len(self.leftovers) if self.leftovers is not None else 0}")
            records_df = self.leftovers
            self.leftovers = None
            try:
                # build up a dataframe until we reach the batch size
                while records_df is None or len(records_df) < self.batch_size:
                    current_count = 0 if records_df is None else len(records_df)
                    logger.debug(
                        f"fetching another dataframe from the generator, got {current_count} out of a desired {self.batch_size}"
                    )
                    next_df = next(self.generator)
                    if next_df is not None and next_df.__class__.__name__ not in (
                        "DataFrame"
                    ):
                        logger.error(
                            f"Dataframe generator provided an unexpected object, type {next_df.__class__.__name__}"
                        )
                        raise ValueError(
                            f"Dataframe generator provided an unexpected object, type {next_df.__class__.__name__}"
                        )
                    if next_df is None and records_df is None:
                        logger.debug(
                            "Original and next dataframes were None, returning None"
                        )
                        return None
                    records_df = pandas.concat([records_df, next_df])
                    logger.debug(
                        f"after concatenation, dataframe has {len(records_df)} records"
                    )
            except StopIteration:
                logger.debug("FixedSizeGenerator consumed the last pandas batch")

            if records_df is None:
                logger.debug("No records left, returning None")
                return None
            elif records_df is not None and len(records_df) > self.batch_size:
                logger.debug(
                    f"putting {len(records_df[self.batch_size:])} records back ({len(records_df)} > {self.batch_size})"
                )
                self.leftovers = records_df[self.batch_size :].reset_index(drop=True)
                records_df = records_df[0 : self.batch_size].reset_index(drop=True)
            else:
                current_count = 0 if records_df is None else len(records_df)
                logger.debug(
                    f"{current_count} records does not exceed batch size, not putting any back"
                )
            return records_df

    def __iter__(self):
        """Returns the Iterator object"""
        return self


def __managed_outbound_processing_worker(
    plugin_class_obj: OmnataPlugin,
    method: Callable,
    worker_index: int,
    dataframe_generator: FixedSizeGenerator,
    cancellation_token: threading.Event,
    method_args,
    method_kwargs,
):
    """
    A worker thread for the managed_outbound_processing annotation.
    Consumes a fixed sized set of records by passing them to the wrapped function,
    while adhering to the defined API constraints.
    """
    context.attach(plugin_class_obj.opentelemetry_context)
    logger.debug(
        f"worker {worker_index} processing. Cancelled: {cancellation_token.is_set()}"
    )
    while not cancellation_token.is_set():
        # Get our generator object out of the queue
        assert (
            plugin_class_obj._sync_request is not None
        )  # pylint: disable=protected-access
        records_df = next(dataframe_generator)
        #logger.info(f"records returned from dataframe generator: {records_df}")
        if records_df is None:
            logger.debug(f"worker {worker_index} has no records left to process")
            return
        elif len(records_df) == 0:
            logger.debug(f"worker {worker_index} has 0 records left to process")
            return

        logger.debug(
            f"worker {worker_index} fetched {len(records_df)} records for processing"
        )
        # threads block while waiting for their allocation of records, it's possible there's been
        # a cancellation in the meantime
        if cancellation_token.is_set():
            logger.info(
                f"worker {worker_index} exiting before applying records, due to cancellation"
            )
            return
        logger.debug(f"worker {worker_index} processing {len(records_df)} records")
        # restore the first argument, was originally the dataframe/generator but now it's the appropriately sized dataframe
        try:
            results_df = method(
                plugin_class_obj, *(records_df, *method_args), **method_kwargs
            )
        except InterruptedWhileWaitingException:
            # If an outbound run is cancelled while waiting for rate limiting, this should mean that
            # the cancellation is handled elsewhere, so we don't need to do anything special here other than stop waiting
            logger.info(
                f"worker {worker_index} interrupted while waiting for rate limiting, exiting"
            )
            return
        logger.debug(
            f"worker {worker_index} received {len(results_df)} results, enqueueing"
        )

        # we want to write the results of the batch back to Snowflake, so we
        # enqueue them and they'll be picked up by the apply_results worker
        outbound_sync_request = cast(
            OutboundSyncRequest, plugin_class_obj._sync_request
        )  # pylint: disable=protected-access
        outbound_sync_request.enqueue_results(
            results_df
        )  # pylint: disable=protected-access
        logger.debug(
            f"worker {worker_index} enqueueing results"
        )


def managed_outbound_processing(concurrency: int, batch_size: int):
    """
    This is a decorator which can be added to a method on an OmnataPlugin class.
    It expects to be invoked with either a DataFrame or a DataFrame generator, and
    the method will receive a DataFrame of the correct size based on the batch_size parameter.

    The decorator itself must be used as a function call with tuning parameters like so:
    @managed_outbound_processing(concurrency=5, batch_size=100)
    def my_function(param1,param2)

    Threaded workers will be used to invoke in parallel, according to the concurrency constraints.

    The decorated method is expected to return a DataFrame with the outcome of each record that was provided.
    """

    def actual_decorator(method):
        @wraps(method)
        def _impl(self: OmnataPlugin, *method_args, **method_kwargs):
            logger.info(f"managed_outbound_processing invoked with {len(method_args)} positional arguments and {len(method_kwargs)} named arguments ({','.join(method_kwargs.keys())})")
            if self._sync_request is None:  # pylint: disable=protected-access
                raise ValueError(
                    "To use the managed_outbound_processing decorator, you must attach a sync request to the plugin instance (via the _sync_request property)"
                )
            logger.info(f"Batch size: {batch_size}. Concurrency: {concurrency}")

            dataframe_arg = None
            if 'dataframe' in method_kwargs:
                dataframe_arg = method_kwargs['dataframe']
                del method_kwargs['dataframe']
                if dataframe_arg.__class__.__name__ != "DataFrame":
                    raise ValueError(
                        f"The 'dataframe' named argument to the @managed_outbound_processing must be a DataFrame. Instead, a {dataframe_arg.__class__.__name__} was provided."
                    )
                
            elif 'dataframe_generator' in method_kwargs:
                dataframe_arg = method_kwargs['dataframe_generator']
                del method_kwargs['dataframe_generator']
                if not hasattr(dataframe_arg, "__next__"):
                    raise ValueError(
                        f"The 'dataframe_generator' named argument to the @managed_outbound_processing must be an iterator function. Instead, a {dataframe_arg.__class__.__name__} was provided."
                    )
            # if the dataframe was provided as the first argument, we'll use that
            if dataframe_arg is None and len(method_args) > 0:
                dataframe_arg = method_args[0]
                if dataframe_arg.__class__.__name__ != "DataFrame" and not hasattr(dataframe_arg, "__next__"):
                    raise ValueError(
                        f"The first argument to a @managed_outbound_processing method must be a DataFrame or DataFrame generator (from outbound_sync_request.get_records). Instead, a {dataframe_arg.__class__.__name__} was provided. Alternatively, you can provide these via the 'dataframe' or 'dataframe_generator' named arguments."
                    )
                method_args = method_args[1:]

            # put the record iterator on the queue, ready for the first task to read it
            fixed_size_generator = FixedSizeGenerator(dataframe_arg, batch_size=batch_size)
            tasks:List[threading.Thread] = []
            logger.debug(f"Creating {concurrency} worker(s) for applying records")
            # just in case
            threading.excepthook = self._sync_request.thread_exception_hook
            for i in range(concurrency):
                # the dataframe/generator was put on the queue, so we remove it from the method args
                task = threading.Thread(
                    target=__managed_outbound_processing_worker,
                    name=f"managed_outbound_processing_worker_{i}",
                    args=(
                        self,
                        method,
                        i,
                        fixed_size_generator,
                        self._sync_request._thread_cancellation_token,
                        method_args,
                        method_kwargs,
                    ),
                )
                tasks.append(task)
                task.start()

            # wait for workers to finish
            while tasks:
                for task in tasks[:]: # shallow copy so we can remove items from the list while iterating
                    if not task.is_alive():
                        task.join()  # Ensure the thread is fully finished
                        tasks.remove(task)
                        logger.info(f"Thread {task.name} has completed processing")
                time.sleep(1)  # Avoid busy waiting
            logger.info("All workers completed processing")

            # it's possible that some records weren't applied, since they are processed asynchronously on a timer
            #if self._sync_request.development_mode is False:
            #    self._sync_request.apply_results_queue()

            # these checks are done in the sync method of plugin_entrypoints
            # we don't want to do them here anymore, because there could be multiple calls to different @managed_outbound_processing
            # methods, so we don't want the apply results task to end until after the sync completes
            #self._sync_request._thread_cancellation_token.set()
            ## the thread cancellation should be detected by the apply results tasks, so it finishes gracefully
            #if (
            #    self._sync_request.development_mode is False
            #    and self._sync_request._apply_results_task is not None
            #):
            #    self._sync_request._apply_results_task.join()
            if self._sync_request._thread_exception_thrown:
                logger.info("Raising thread exception")
                raise self._sync_request._thread_exception_thrown.exc_value
            else:
                logger.info("No thread exception thrown")

            logger.info("Main managed_outbound_processing thread completing")
            return

        return _impl

    return actual_decorator


def __managed_inbound_processing_worker(
    plugin_class_obj: Type[OmnataPlugin],
    method: Callable,
    worker_index: int,
    streams_queue: queue.Queue,
    cancellation_token: threading.Event,
    method_args,
    method_kwargs,
):
    """
    A worker thread for the managed_inbound_processing annotation.
    Passes single streams at a time to the wrapped function, adhering to concurrency constraints.
    """
    context.attach(plugin_class_obj.opentelemetry_context)
    while not cancellation_token.is_set():
        # Get our generator object out of the queue
        logger.debug(
            f"worker {worker_index} processing. Cancelled: {cancellation_token.is_set()}. Method args: {len(method_args)}. Method kwargs: {len(method_kwargs.keys())} ({','.join(method_kwargs.keys())})"
        )
        try:
            stream: StoredStreamConfiguration = streams_queue.get_nowait()
            logger.debug(f"stream returned from queue: {stream}")
            sync_request: InboundSyncRequest = cast(
                InboundSyncRequest, plugin_class_obj._sync_request
            )  # pylint: disable=protected-access
            if stream.stream_name not in sync_request._stream_start_times:
                sync_request.mark_stream_started(stream.stream_name)
            # restore the first argument, was originally the dataframe/generator but now it's the appropriately sized dataframe
            try:
                with tracer.start_as_current_span("managed_inbound_processing") as managed_inbound_processing_span:
                    logger.debug(f"worker {worker_index} processing stream {stream.stream_name}, invoking plugin class method {method.__name__}")
                    managed_inbound_processing_span.set_attribute("omnata.sync.stream_name", stream.stream_name)
                    result = method(plugin_class_obj, *(stream, *method_args), **method_kwargs)
                    logger.debug(f"worker {worker_index} completed processing stream {stream.stream_name}")
                    if result is not None and result is False:
                        logger.info(f"worker {worker_index} requested that {stream.stream_name} be not marked as complete")
                    else:
                        logger.info(f"worker {worker_index} marking stream {stream.stream_name} as complete")
                        sync_request.mark_stream_complete(stream.stream_name)
            except InterruptedWhileWaitingException:
                # If an inbound run is cancelled while waiting for rate limiting, this should mean that
                # the cancellation is handled elsewhere, so we don't need to do anything special here other than stop waiting
                logger.info(f"worker {worker_index} interrupted while waiting, exiting")
                return
            except Exception as e:
                # logging this to the omnata_plugin logger in this way, 
                # will cause it to automatically fail the appropriate stream
                omnata_plugin_logger = getLogger("omnata_plugin")
                try:
                    omnata_plugin_logger.error(f"Error syncing stream {stream.stream_name}: {str(e)}", 
                                exc_info=True, 
                                extra={'stream_name':stream.stream_name})
                except Exception as e2:
                    # sometimes we get "Object of type MaxRetryError is not JSON serializable" or similar
                    # so we need to handle that gracefully and just log it without the contents
                    omnata_plugin_logger.error(f"{type(e).__name__} syncing stream {stream.stream_name}", 
                                exc_info=True, 
                                extra={'stream_name':stream.stream_name})
        except queue.Empty:
            logger.debug("streams queue is empty")
            return


def managed_inbound_processing(concurrency: int):
    """
    This is a decorator which can be added to a method on an OmnataPlugin class.
    It expects to be invoked with a list of StoredStreamConfiguration objects as the
    first parameter.
    The method will receive a single StoredStreamConfiguration object at a time as its
    first parameter, and is expected to publish its results via
    inbound_sync_request.enqueue_results() during the load process.

    The decorator itself must be used as a function call with a tuning parameter like so:
    @managed_inbound_processing(concurrency=5)
    def my_function(param1,param2)

    Based on the concurrency constraints, it will create threaded workers to retrieve
    the streams in parallel.
    """

    def actual_decorator(method):
        @wraps(method)
        def _impl(self:OmnataPlugin, *method_args, **method_kwargs):
            if self._sync_request is None:
                raise ValueError(
                    "To use the managed_inbound_processing decorator, you must attach an apply request to the plugin instance (via the _sync_request property)"
                )
            logger.debug(f"managed_inbound_processing invoked with {len(method_args)} positional arguments and {len(method_kwargs)} named arguments ({','.join(method_kwargs.keys())})")
            if self._sync_request.development_mode is True:
                concurrency_to_use = 1 # disable concurrency when running in development mode, it interferes with pyvcr
            else:
                concurrency_to_use = concurrency
            stream_list_arg: List[StoredStreamConfiguration] = None
            if 'streams' in method_kwargs:
                stream_list_arg = cast(List[StoredStreamConfiguration],method_kwargs['streams'])
                del method_kwargs['streams']
            if stream_list_arg is None and len(method_args) > 0:
                stream_list_arg = cast(List[StoredStreamConfiguration],method_args[0])
                if stream_list_arg.__class__.__name__ != "list":
                    raise ValueError(
                        f"The first argument to a @managed_inbound_processing method must be a list of StoredStreamConfigurations if the 'streams' named argument is not provided. Instead, a {stream_list_arg.__class__.__name__} was provided."
                    )
                method_args = method_args[1:]
            if stream_list_arg is None:
                raise ValueError("You must provide a list of StoredStreamConfiguration objects to the method, either as the first argument or as a named argument 'streams'")

            streams_list = stream_list_arg
            # create a queue full of all the streams to process
            streams_queue = queue.Queue()
            for stream in streams_list:
                streams_queue.put(stream)

            tasks:List[threading.Thread] = []
            logger.info(f"Creating {concurrency_to_use} worker(s) for retrieving records")
            # if concurrency is set to 1, we don't need to use threads at all
            if concurrency_to_use == 1:
                __managed_inbound_processing_worker(
                    self,
                    method,
                    0,
                    streams_queue,
                    self._sync_request._thread_cancellation_token,
                    method_args,
                    method_kwargs,
                )
            else:
                for i in range(concurrency_to_use):
                    # the dataframe/generator was put on the queue, so we remove it from the method args
                    task = threading.Thread(
                        target=__managed_inbound_processing_worker,
                        name=f"managed_inbound_processing_worker_{i}",
                        args=(
                            self,
                            method,
                            i,
                            streams_queue,
                            self._sync_request._thread_cancellation_token,
                            method_args,
                            method_kwargs,
                        ),
                    )
                    tasks.append(task)
                    task.start()

                # wait for workers to finish
                while tasks:
                    for task in tasks[:]: # shallow copy so we can remove items from the list while iterating
                        if not task.is_alive():
                            task.join()  # Ensure the thread is fully finished
                            tasks.remove(task)
                            logger.info(f"Thread {task.name} has completed processing")
                    time.sleep(1)  # Avoid busy waiting
                logger.info("All workers completed processing")

                # it's possible that some records weren't applied, since they are processed asynchronously on a timer
                #if self._sync_request.development_mode is False:
                #    self._sync_request.apply_results_queue()
                #self._sync_request._thread_cancellation_token.set()
                ## the thread cancellation should be detected by the apply results tasks, so it finishes gracefully
                #if (
                #    self._sync_request.development_mode is False
                #    and self._sync_request._apply_results_task is not None
                #):
                #    self._sync_request._apply_results_task.join()
                if self._sync_request._thread_exception_thrown:
                    logger.info("Raising thread exception")
                    raise self._sync_request._thread_exception_thrown.exc_value
                else:
                    logger.info("No thread exception thrown")
            logger.info("Main managed_inbound_processing thread completing")
            return

        return _impl

    return actual_decorator


class DeadlineReachedException(Exception):
    """
    Indicates that a sync needed to be abandoned due to reaching a deadline, or needing to wait past a future
    deadline.
    """
    def __init__(self):
        message = "Sync deadline reached"
        self.message = message
        super().__init__(self.message)

def remove_empty_dict_values(data: Dict) -> Dict:
    """
    Recursively removes any empty dicts from the data
    """
    if isinstance(data, dict):
        return {
            k: remove_empty_dict_values(v)
            for k, v in data.items()
            if v != {}
        }
    return data

def get_nested_value(nested_dict:Dict, keys:List[str]):
    """
    Gets a value from a nested dictionary, using a list of keys to traverse the structure.
    """
    # if a single primary key string is provided instead of a list, handle it gracefully
    if isinstance(keys, str):
        keys = [keys]
    return reduce(lambda d, key: d.get(key) if isinstance(d, dict) else None, keys, nested_dict)


def omnata_udtf(
        name:str,
        description: str,
        params: List[SnowflakeFunctionParameter],
        result_columns: List[SnowflakeUDTFResultColumn],
        expose_to_consumer: bool):
    """
    A decorator for a class which should create a UDTF in the UDFS schema of the native app
    """
    def class_decorator(cls):
        # Get the original 'process' method from the class
        if not hasattr(cls, 'process'):
            raise ValueError("The class must have a 'process' method.")
        original_process = getattr(cls, 'process')
        sig = signature(original_process)
        function_params = sig.parameters
        if len(function_params) < 1:
            raise ValueError("The 'process' function must have at least one parameter.")
        
        first_param_name = list(function_params.keys())[0]
        if first_param_name != 'self':
            raise ValueError(f"The first argument for the 'process' function should be 'self', instead it was '{first_param_name}'.")

        cls._is_omnata_udtf = True
        cls._omnata_udtf_name = name
        cls._omnata_udtf_description = description
        cls._omnata_udtf_params = params
        cls._omnata_udtf_result_columns = result_columns
        cls._omnata_udtf_expose_to_consumer = expose_to_consumer

        if not expose_to_consumer:
            # If not exposing to the consumer, there are no further requirements
            return cls
        
        if len(function_params) < 2:
            raise ValueError("When exposing the udtf to consumers, the 'process' function must have the self parameter, plus at least the mandatory 'connection_parameters' parameter.")
        second_param_name = list(function_params.keys())[1]
        if second_param_name != 'connection_parameters':
            raise ValueError(f"The second argument should be 'connection_parameters', instead it was {second_param_name}.")
        if function_params[second_param_name].annotation != ConnectionConfigurationParameters:
            raise ValueError(f"The second argument must be a ConnectionConfigurationParameters, instead it was a {function_params[second_param_name].annotation}.")

        if params[0].name.upper() != 'CONNECTION_PARAMETERS':
            params_new = [SnowflakeFunctionParameter(
                                    name='CONNECTION_PARAMETERS',
                                    data_type='OBJECT',
                                    description='The connection object, obtained from calling PLUGIN.PLUGIN_CONNECTION.')] + params
            cls._omnata_udtf_params = params_new
        else:
            cls._omnata_udtf_params = params
        if len(cls._omnata_udtf_params) != len(function_params) -1:
            raise ValueError(f"You must document all the parameters of the 'process' function in the @omnata_udtf decorator in the same order ('connection_parameters' will be included automatically).")

        @wraps(original_process)
        def wrapped_process(self, connection_parameter_arg, *args, **kwargs):
            if connection_parameter_arg is None:
                raise ValueError("Connection not found")           
            
            # convert the connection parameters dictionary to a ConnectionConfigurationParameters object which includes the real secrets
            if 'other_secrets_name' in connection_parameter_arg:
                # this is the new way, where the sync engine only passes the name of the secret
                oauth_secrets_name = None
                if 'oauth_secret_name' in connection_parameter_arg:
                    oauth_secrets_name = connection_parameter_arg['oauth_secret_name']
                    del connection_parameter_arg['oauth_secret_name']
                result = get_secrets(oauth_secrets_name,connection_parameter_arg['other_secrets_name'])
                connection_parameter_arg['connection_secrets'] = result
                del connection_parameter_arg['other_secrets_name']
            
            parameters = ConnectionConfigurationParameters.model_validate(connection_parameter_arg)

            # Pass the validated arguments to the function
            return original_process(self, parameters, *args, **kwargs)
        # Replace the original 'process' method with the wrapped version
        setattr(cls, 'process', wrapped_process)
        return cls
    
    return class_decorator

def find_udtf_classes(path:str = '.',top_level_modules:Optional[List[str]] = None) -> List[UDTFDefinition]:
    """
    Finds all classes in the specified directory which have the 'omnata_udtf' decorator applied
    """
    # Get the directory's absolute path
    current_dir = os.path.abspath(path)

    # List to hold the classes that match the attribute
    matching_classes = []

    # Iterate over all modules in the current directory
    for importer, module_name, ispkg in pkgutil.walk_packages(path=[current_dir]):
        # Import the module
        if top_level_modules is not None:
            if len([x for x in top_level_modules if module_name.startswith(x)]) == 0:
                continue
        module = importlib.import_module(module_name)

        # Iterate over all members of the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if the class has the specified attribute
            if hasattr(obj, '_is_omnata_udtf'):
                matching_classes.append(UDTFDefinition(
                    name=obj._omnata_udtf_name,
                    language='python',
                    runtime_version='3.10',
                    imports=['/app.zip'],
                    description=obj._omnata_udtf_description,
                    params=obj._omnata_udtf_params,
                    result_columns=obj._omnata_udtf_result_columns,
                    expose_to_consumer=obj._omnata_udtf_expose_to_consumer,
                    handler=obj.__module__+'.'+obj.__name__
                ))
        # java doesn't use the python decorator, so we need to check for the class directly
        for name, obj in inspect.getmembers(module):
            # Check if the class has the specified attribute
            if isinstance(obj, UDTFDefinition) and cast(UDTFDefinition,obj).language == 'java':
                udtf_obj = cast(UDTFDefinition,obj)
                if udtf_obj.language == 'java':
                    # because the decorator wasn't used, we need to check if we need to add the connection_parameters parameter
                    if udtf_obj.expose_to_consumer:
                        if len(udtf_obj.params) == 0 or udtf_obj.params[0].name.upper() != 'CONNECTION_PARAMETERS':
                            udtf_obj.params = [SnowflakeFunctionParameter(
                                                name='CONNECTION_PARAMETERS',
                                                data_type='OBJECT',
                                                description='The connection object, obtained from calling PLUGIN.PLUGIN_CONNECTION.')] + udtf_obj.params
                    matching_classes.append(udtf_obj)
            
    return matching_classes


def omnata_udf(
        name: str,
        description: str,
        params: List[SnowflakeFunctionParameter],
        result_data_type: str,
        expose_to_consumer: bool):
    """
    A decorator for a function which will be created in the native application.
    """
    def decorator(func):
        sig = signature(func)
        function_params = sig.parameters

        if not expose_to_consumer:
            # If not exposing to the consumer, there are no further requirements
            func._is_omnata_udf = True
            func._omnata_udf_name = name
            func._omnata_udf_description = description
            func._omnata_udf_params = params
            func._omnata_udf_result_data_type = result_data_type
            func._omnata_udf_expose_to_consumer = expose_to_consumer
            return func
        
        if len(function_params) == 0:
            raise ValueError("The function must have at least one parameter.")
        # Ensure the first argument is mandatory and positional
        first_param_name = list(function_params.keys())[0]
        if first_param_name != 'connection_parameters':
            raise ValueError(f"The first argument should be 'connection_parameters', instead it was '{first_param_name}'.")
        if function_params[first_param_name].annotation != ConnectionConfigurationParameters:
            raise ValueError(f"The first argument must be a ConnectionConfigurationParameters, instead it was a {function_params[first_param_name].annotation}.")
        if params[0].name.upper() != 'CONNECTION_PARAMETERS':
            params_new = [SnowflakeFunctionParameter(
                                    name='CONNECTION_PARAMETERS',
                                    data_type='OBJECT',
                                    description='The connection object, obtained from calling PLUGIN.PLUGIN_CONNECTION.')] + params
            func._omnata_udf_params = params_new
        else:
            func._omnata_udf_params = params
        if len(func._omnata_udf_params) != len(function_params):
            raise ValueError(f"You must document all the parameters of the function in the @omnata_udf decorator in the same order ('connection_parameters' will be included automatically).")

        @wraps(func)
        def wrapper(connection_parameter_arg, *args, **kwargs):
            # convert the connection parameters dictionary to a ConnectionConfigurationParameters object which includes the real secrets
            if 'other_secrets_name' in connection_parameter_arg:
                # this is the new way, where the sync engine only passes the name of the secret
                oauth_secrets_name = None
                if 'oauth_secret_name' in connection_parameter_arg:
                    oauth_secrets_name = connection_parameter_arg['oauth_secret_name']
                    del connection_parameter_arg['oauth_secret_name']
                result = get_secrets(oauth_secrets_name,connection_parameter_arg['other_secrets_name'])
                connection_parameter_arg['connection_secrets'] = result
                del connection_parameter_arg['other_secrets_name']
                
            parameters = ConnectionConfigurationParameters.model_validate(connection_parameter_arg)

            # Pass the validated arguments to the function
            return func(parameters, *args, **kwargs)
        
        wrapper._is_omnata_udf = True
        wrapper._omnata_udf_name = name
        wrapper._omnata_udf_description = description
        wrapper._omnata_udf_result_data_type = result_data_type
        wrapper._omnata_udf_expose_to_consumer = expose_to_consumer
        return wrapper
    
    return decorator

def find_udf_functions(path:str = '.',top_level_modules:Optional[List[str]] = None) -> List[UDFDefinition]:
    """
    Finds all functions in the specified directory which have the 'omnata_udf' decorator applied
    """
    # Get the current directory's absolute path
    current_dir = os.path.abspath(path)

    # List to hold the classes that match the attribute
    matching_classes = []

    # Iterate over all modules in the current directory
    for importer, module_name, ispkg in pkgutil.walk_packages(path=[current_dir]):
        # Import the module
        if top_level_modules is not None:
            if len([x for x in top_level_modules if module_name.startswith(x)]) == 0:
                continue
        module = importlib.import_module(module_name)

        # Iterate over all members of the module
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            # Check if the class has the specified attribute
            if hasattr(obj, '_is_omnata_udf'):
                matching_classes.append(UDFDefinition(
                    name=obj._omnata_udf_name,
                    language='python',
                    runtime_version='3.10',
                    imports=['/app.zip'],
                    description=obj._omnata_udf_description,
                    params=obj._omnata_udf_params,
                    result_data_type=obj._omnata_udf_result_data_type,
                    expose_to_consumer=obj._omnata_udf_expose_to_consumer,
                    packages=[],
                    handler=obj.__module__+'.'+obj.__name__
                ))
        # java doesn't use the python decorator, so we need to check for the class directly
        for name, obj in inspect.getmembers(module):
            # Check if the class has the specified attribute
            if isinstance(obj, UDFDefinition):
                udf_obj = cast(UDFDefinition,obj)
                if udf_obj.language == 'java':
                    # because the decorator wasn't used, we need to check if we need to add the connection_parameters parameter
                    if udf_obj.expose_to_consumer:
                        if len(udf_obj.params) == 0 or udf_obj.params[0].name.upper() != 'CONNECTION_PARAMETERS':
                            udf_obj.params = [SnowflakeFunctionParameter(
                                                name='CONNECTION_PARAMETERS',
                                                data_type='OBJECT',
                                                description='The connection object, obtained from calling PLUGIN.PLUGIN_CONNECTION.')] + udf_obj.params
                    matching_classes.append(udf_obj)

    return matching_classes

def get_static_file_contents(relative_path:str) -> bytes:
    """
    Retrieve file packaged with this plugin, by extracting it from the zip file.
    The relative path will be relative to the root of the src folder of the plugin.
    """
    # this file will be inside the zip file, so we can find it by looking at the path of this file
    full_path_to_this = os.path.abspath(__file__)
    split_position = full_path_to_this.find('app.zip')
    if split_position == -1:
        with open(relative_path, 'rb') as f:
            return f.read()
    # Add the length of 'app.zip' to split just after it
    split_position += len('app.zip')
    
    path_to_zip = full_path_to_this[:split_position]
    with zipfile.ZipFile(path_to_zip, 'r') as z:
        with z.open(relative_path, 'r') as f:
            return f.read()