"""
Data classes for internal API calls between the sync engine native application and the plugin native application.
Not used in plugins.
"""
import sys
import json

from typing import (
    Dict,
    List,
    Literal,
    Optional,
    Union,
    cast,
)  # pylint: disable=ungrouped-imports

from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module
from snowflake.snowpark import Row

from .configuration import (
    InboundSyncStreamsConfiguration,
    OutboundSyncStrategy,
    StoredConfigurationValue,
    StoredMappingValue,
    ConnectivityOption
)
from .rate_limiting import ApiLimits, RateLimitState

if tuple(sys.version_info[:2]) >= (3, 9):
    # Python 3.9 and above
    from typing import Annotated
else:
    # Python 3.8 and below, Streamlit in Snowflake still runs 3.8
    from typing_extensions import Annotated


class PluginMessageCurrentActivity(BaseModel):
    """
    A message that is sent to the plugin to update the current activity status of a sync
    """

    message_type: Literal["activity"] = "activity"
    current_activity: str


class PluginMessageStreamState(BaseModel):
    """
    Updates the state of the streams for a sync run
    """

    message_type: Literal["stream_state"] = "stream_state"
    stream_state: Dict

class PluginMessageRateLimitState(BaseModel):
    """
    Updates the state of the rate limiting for a connection during a sync run
    """

    message_type: Literal["rate_limit_state"] = "rate_limit_state"
    rate_limit_state: Dict[str,RateLimitState]

class PluginMessageStreamProgressUpdate(BaseModel):
    """
    Updates the record counts and completed streams for a sync run
    """

    message_type: Literal["stream_record_counts"] = "stream_record_counts"
    stream_total_counts: Dict[str, int]
    completed_streams: List[str]
    # older runtime versions didn't have these, so the sync engine can't expect it
    stream_errors: Optional[Dict[str,str]] = None
    total_records_estimate: Optional[Dict[str,int]] = None


class PluginMessageCancelledStreams(BaseModel):
    """
    Updates the list of cancelled streams for a sync run
    """

    message_type: Literal["cancelled_streams"] = "cancelled_streams"
    cancelled_streams: List[str]


class PluginMessageAbandonedStreams(BaseModel):
    """
    Updates the list of abandoned streams for a sync run
    """

    message_type: Literal["abandoned_streams"] = "abandoned_streams"
    abandoned_streams: List[str]


PluginMessage = Annotated[
    Union[
        PluginMessageCurrentActivity,
        PluginMessageStreamState,
        PluginMessageStreamProgressUpdate,
        PluginMessageCancelledStreams,
        PluginMessageAbandonedStreams,
        PluginMessageRateLimitState
    ],
    Field(discriminator="message_type"),
]


class OutboundSyncRequestPayload(BaseModel):
    """
    Encapsulates the payload that is sent to the plugin when it is invoked to perform an outbound sync.
    """

    sync_id: int
    sync_branch_name: str = 'main'
    sync_branch_id: Optional[int]
    connection_id: int  # only used by log handler
    run_id: int  # used by log handler and for reporting back run status updates
    source_app_name: str  # the name of the app which is invoking this plugin
    records_schema_name: str  # the name of the schema where the source records reside
    records_table_name: str  # used to provide the source records to the engine, resides in the main Omnata app database
    results_schema_name: str  # the name of the schema where the results table resides
    results_table_name: str  # used to stage results back to the engine, resides in the main Omnata app database
    logging_level: str
    connection_method: str
    target_type: Optional[str] = None
    connectivity_option: ConnectivityOption = Field(default=ConnectivityOption.DIRECT)
    connection_parameters: Dict[str, StoredConfigurationValue]
    oauth_secret_name: Optional[str] = None
    other_secrets_name: Optional[str] = None
    sync_direction: Literal["outbound"] = "outbound"
    sync_strategy: OutboundSyncStrategy
    sync_parameters: Dict[str, StoredConfigurationValue]
    api_limit_overrides: List[ApiLimits]
    rate_limits_state: Dict[int,Dict[str,Dict[str,RateLimitState]]]
    field_mappings: Optional[StoredMappingValue] = None
    time_limit_mins: int = 60 * 4


class InboundSyncRequestPayload(BaseModel):
    """
    Encapsulates the payload that is sent to the plugin when it is invoked to perform an inbound sync.
    """

    sync_id: int
    sync_branch_name: str = 'main'
    sync_branch_id: Optional[int] = None  # only used by log handler
    connection_id: int  # only used by log handler
    run_id: int  # used by log handler and for reporting back run status updates
    source_app_name: str  # the name of the app which is invoking this plugin
    results_schema_name: str  # the name of the schema where the results table resides
    results_table_name: str  # used to stage results back to the engine, resides in the main Omnata app database
    logging_level: str
    connection_method: str
    connectivity_option: ConnectivityOption = Field(default=ConnectivityOption.DIRECT)
    connection_parameters: Dict[str, StoredConfigurationValue]
    oauth_secret_name: Optional[str] = None
    other_secrets_name: Optional[str] = None
    sync_direction: Literal["inbound"] = "inbound"
    sync_parameters: Dict[str, StoredConfigurationValue]
    api_limit_overrides: List[ApiLimits]
    rate_limits_state: Dict[int,Dict[str,Dict[str,RateLimitState]]]
    streams_configuration: InboundSyncStreamsConfiguration
    latest_stream_state: Dict
    time_limit_mins: int = 60 * 4


SyncRequestPayload = Annotated[
    Union[OutboundSyncRequestPayload, InboundSyncRequestPayload],
    Field(discriminator="sync_direction"),
]

class OutboundConfigurationFormPayload(BaseModel):
    """
    Encapsulates the payload that is sent to the plugin when it is invoked to provide a configuration form for an outbound sync.
    """
    connectivity_option: ConnectivityOption = Field(default=ConnectivityOption.DIRECT)
    connection_method: str
    connection_parameters: Dict[str, StoredConfigurationValue]
    oauth_secret_name: Optional[str] = None
    other_secrets_name: Optional[str] = None
    sync_direction: Literal["outbound"] = "outbound"
    target_type: Optional[str] = None
    sync_strategy: OutboundSyncStrategy
    function_name: str = "outbound_configuration_form"
    sync_parameters: Dict[str, StoredConfigurationValue]
    current_form_parameters: Optional[Dict[str, StoredConfigurationValue]]

class InboundConfigurationFormPayload(BaseModel):
    """
    Encapsulates the payload that is sent to the plugin when it is invoked to provide a configuration form for an inbound sync.
    """
    connectivity_option: ConnectivityOption = Field(default=ConnectivityOption.DIRECT)
    connection_method: str
    connection_parameters: Dict[str, StoredConfigurationValue]
    oauth_secret_name: Optional[str] = None
    other_secrets_name: Optional[str] = None
    sync_direction: Literal["inbound"] = "inbound"
    function_name: str = "inbound_configuration_form"
    sync_parameters: Dict[str, StoredConfigurationValue]
    current_form_parameters: Optional[Dict[str, StoredConfigurationValue]]

ConfigurationFormPayload = Annotated[
    Union[OutboundConfigurationFormPayload, InboundConfigurationFormPayload],
    Field(discriminator="sync_direction"),
]


def handle_proc_result(query_result: List[Row]) -> Dict:
    """
    Our standard proc response is a single row with a single column, which is a JSON string
    We parse the success flag and raise an error if it's not true
    Otherwise we return the data
    """
    if len(query_result) != 1:
        raise ValueError(
            f"Expected a single row result from procedure (got {len(query_result)})"
        )
    first_row = cast(Row, query_result[0])
    result = json.loads(str(first_row[0]))
    if result["success"] is not True:
        raise ValueError(result["error"])
    return result["data"] if "data" in result else result
