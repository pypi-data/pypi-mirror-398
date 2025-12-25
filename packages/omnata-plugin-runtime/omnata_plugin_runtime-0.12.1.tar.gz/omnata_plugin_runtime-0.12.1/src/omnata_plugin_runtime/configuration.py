"""
Omnata Plugin Runtime configuration objects.
Includes data container classes related to plugin configuration.
"""
from __future__ import annotations
import json
import sys
import logging
from typing import Any, List, Dict, Literal, Union, Optional
from typing_extensions import Self
from enum import Enum

from abc import ABC
from pydantic import BaseModel, Field, PrivateAttr, SerializationInfo, TypeAdapter, field_validator, model_serializer, model_validator  # pylint: disable=no-name-in-module
from .logging import logger, tracer

if tuple(sys.version_info[:2]) >= (3, 9):
    # Python 3.9 and above
    from typing import Annotated  # pylint: disable=ungrouped-imports
else:
    # Python 3.8 and below
    from typing_extensions import Annotated

class MapperType(str, Enum):
    FIELD_MAPPING_SELECTOR = "field_mapping_selector"
    JINJA_TEMPLATE = "jinja_template"


class SyncDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class InboundStorageBehaviour(str, Enum):
    APPEND = "append"
    MERGE = "merge"
    REPLACE = "replace" # now deprecated, full refreshes now use merge

class ConnectivityOption(str, Enum):
    """
    Describes the connectivity options available to a plugin.
    These result in slightly different network rules and connection onboarding.
    """
    DIRECT = "direct"
    NGROK = "ngrok"
    PRIVATELINK = "privatelink"

class InboundSyncStrategy(str, Enum):
    FULL_REFRESH = "Full Refresh"
    INCREMENTAL = "Incremental"
    AUTO = "Auto" # not valid as an individual stream choice, only when referring to a forward preference (new_stream_sync_strategy)

class InboundSyncStrategyBulkConfiguration(str, Enum):
    """
    Supercedes InboundSyncBulkConfiguration, which was a combination of sync strategy and storage behaviour.
    """
    AUTO = "auto"
    MANUAL = "manual"

class InboundStorageBehaviourBulkConfiguration(str, Enum):
    """
    Supercedes InboundSyncBulkConfiguration, which was a combination of sync strategy and storage behaviour.
    """
    MERGE = "merge"
    APPEND = "append"
    MANUAL = "manual"

class InboundSyncBulkConfiguration(str, Enum):
    """
    Provides a way to apply a combination of sync strategy and storage behaviour to all selected streams.
    These options will be reduce to the set of supported strategies. If there is no overlap, only CUSTOMIZE will be supported
    """
    AUTO_MERGE = "Auto / Merge changes" # Merge
    AUTO_APPEND = "Auto / Keep history"  # Append
    CUSTOMIZE = "Customize - choose sync behaviours for each object"
    # These are legacy values, back when we used to let people bulk set the full combination
    ALL_FULL_REPLACE = "All Objects - Full refresh / Replace"
    ALL_FULL_APPEND = "All Objects - Full refresh / Append"
    ALL_INCR_MERGE = "All Objects - Incremental / Merge"
    ALL_INCR_APPEND = "All Objects - Incremental / Append"


ICON_URL_CODE = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="m8 18l-6-6l6-6l1.425 1.425l-4.6 4.6L9.4 16.6Zm8 0l-1.425-1.425l4.6-4.6L14.6 7.4L16 6l6 6Z"/></svg>'
ICON_URL_ADD = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="M11 19v-6H5v-2h6V5h2v6h6v2h-6v6Z"/></svg>'
ICON_URL_MERGE = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><g transform="rotate(90 12 12)"><path fill="currentColor" d="M7.4 20L6 18.6l5-5V6.875L8.425 9.45L7 8.025l5-5l5.025 5.025L15.6 9.475l-2.6-2.6V14.4Zm9.2.025l-3.2-3.175l1.425-1.425l3.175 3.2Z"/></g></svg>'
ICON_URL_CALL_MADE = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="M5.4 20L4 18.6L15.6 7H9V5h10v10h-2V8.4Z"/></svg>'
ICON_URL_DELETE = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="m9.4 16.5l2.6-2.6l2.6 2.6l1.4-1.4l-2.6-2.6L16 9.9l-1.4-1.4l-2.6 2.6l-2.6-2.6L8 9.9l2.6 2.6L8 15.1ZM7 21q-.825 0-1.412-.587Q5 19.825 5 19V6H4V4h5V3h6v1h5v2h-1v13q0 .825-.587 1.413Q17.825 21 17 21ZM17 6H7v13h10ZM7 6v13Z"/></svg>'
ICON_URL_BASELINE_MERGE = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="M6.41 21L5 19.59l4.83-4.83c.75-.75 1.17-1.77 1.17-2.83v-5.1L9.41 8.41L8 7l4-4l4 4l-1.41 1.41L13 6.83v5.1c0 1.06.42 2.08 1.17 2.83L19 19.59L17.59 21L12 15.41L6.41 21z"/></svg>'
ICON_URL_REPLACE = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><rect width="6" height="6" x="3" y="3" rx="1"/><rect width="6" height="6" x="15" y="15" rx="1"/><path d="M21 11V8a2 2 0 0 0-2-2h-6l3 3m0-6l-3 3M3 13v3a2 2 0 0 0 2 2h6l-3-3m0 6l3-3"/></g></svg>'
ICON_URL_REFRESH = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="M12 20q-3.35 0-5.675-2.325Q4 15.35 4 12q0-3.35 2.325-5.675Q8.65 4 12 4q1.725 0 3.3.713q1.575.712 2.7 2.037V4h2v7h-7V9h4.2q-.8-1.4-2.187-2.2Q13.625 6 12 6Q9.5 6 7.75 7.75T6 12q0 2.5 1.75 4.25T12 18q1.925 0 3.475-1.1T17.65 14h2.1q-.7 2.65-2.85 4.325Q14.75 20 12 20Z"/></svg>'
ICON_URL_ADD_ROW = '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24"><path fill="currentColor" d="M22 10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V3h2v2h4V3h2v2h4V3h2v2h4V3h2v7M4 10h4V7H4v3m6 0h4V7h-4v3m10 0V7h-4v3h4m-9 4h2v3h3v2h-3v3h-2v-3H8v-2h3v-3Z"/></svg>'


class SubscriptableBaseModel(BaseModel):
    """
    Extends the Pydantic BaseModel to make it subscriptable
    """

    def __getitem__(self, item):
        """Gets the attribute"""
        return getattr(self, item)


class OutboundSyncAction(SubscriptableBaseModel, ABC):
    """
    Base class for Outbound Sync Actions.
    Describes what action will be taken by the plugin with a particular record.
    These actions are linked to via sync strategies in response to a record create/update/delete.
    """

    action_name: str
    description: str
    custom_action: bool = True

    def __eq__(self, other):
        if hasattr(other, 'custom_action') and hasattr(other, 'action_name'):
            return (
                self.custom_action == other.custom_action
                and self.action_name == other.action_name
            )
        else:
            return False

    def __init__(self, **data):
        """
        Initialises an OutboundSyncStrategy
        """
        if "action_name" not in data:
            raise ValueError("'action_name' not set on OutboundSyncStrategy object")
        if "custom_action" in data and data["custom_action"] is False:
            # The built-in outbound sync strategies do not need to have their entire contents stored, just the name
            if self.__class__ != STANDARD_OUTBOUND_SYNC_ACTIONS[data["action_name"]]:
                data = {
                    **data,
                    **STANDARD_OUTBOUND_SYNC_ACTIONS[data["action_name"]]().__dict__,
                }
        super().__init__(**data)
    
    @model_serializer(mode='wrap')
    # no return type hint, see https://github.com/fastapi/fastapi/discussions/10661#discussioncomment-7631104
    def ser_model(self,handler,info:SerializationInfo):
        serialized:Dict[str,Any] = handler(self)
        if not self.custom_action and (info.exclude_none is None or info.exclude_none == False):
            return {k:v for k,v in serialized.items() if k not in [
                "description"]}
        return serialized
    
    def model_dump_no_trim(self) -> Dict[str, Any]:
        # we use our own special include value to signal not to trim
        return self.model_dump(exclude_none=True)


class CreateSyncAction(OutboundSyncAction):
    """
    The standard Create sync action.
    Indicates that a record/object will be created in the target app.
    """

    def __init__(self):
        OutboundSyncAction.__init__(
            self,
            action_name="Create",
            description="Object will be created in the app",
            custom_action=False,
        )


class UpdateSyncAction(OutboundSyncAction):
    """
    The standard Update sync action.
    Indicates that a record/object will be updated in the target app.
    """

    def __init__(self):
        OutboundSyncAction.__init__(
            self,
            action_name="Update",
            description="Object will be updated in the app",
            custom_action=False,
        )


class DeleteSyncAction(OutboundSyncAction):
    """
    The standard Delete sync action.
    Indicates that a record/object will be deleted in the target app.
    """

    def __init__(self):
        OutboundSyncAction.__init__(
            self,
            action_name="Delete",
            description="Object will be deleted in the app",
            custom_action=False,
        )


class SendSyncAction(OutboundSyncAction):
    """
    The standard Send sync action.
    Indicates that a record/object will be sent to the target app. This action is typically
    used in event-style applications, to indicate that the action is more of a message than a record operation.
    """

    def __init__(self):
        OutboundSyncAction.__init__(
            self,
            action_name="Send",
            description="Record will be sent to the app",
            custom_action=False,
        )


class RecreateSyncAction(OutboundSyncAction):
    """
    The standard Recreate sync action.
    Similar to the Create action, but indicates that all existing records in the app will be replaced by these.
    If a sync strategy uses this sync action, it doesn't make sense to include any other actions.
    """

    def __init__(self):
        OutboundSyncAction.__init__(
            self,
            action_name="Recreate",
            description="Record(s) will replace any currently in the app",
            custom_action=False,
        )


STANDARD_OUTBOUND_SYNC_ACTIONS: Dict[str, OutboundSyncAction] = {
    "Create": CreateSyncAction,
    "Update": UpdateSyncAction,
    "Delete": DeleteSyncAction,
    "Send": SendSyncAction,
    "Recreate": RecreateSyncAction,
}

class OutboundTargetParameter(BaseModel):
    """
    Accomodates testing outbound syncs in production by nominating a form field who's value stays in the branch.
    The reason this information is set statically here instead of as a flag on the FormField, is so that the sync engine 
    can have this information readily available without calling the plugin.
    """
    field_name: str = Field(title="""The name of the form field that toggles the location, e.g. 'channel','customer_list'.
This must match a field which will be returned by the outbound_configuration_form for this target type.""")
    is_branching_toggle: bool = Field(title="""Whether or not this field is a target toggle for branching.
If true, the value of this field will be used to determine the location of the sync in production.
For example, a messaging plugin could have a "channel" field to route messages to an alternate location.
Or, a marketing platform could have an alternate customer list name which is connected to test campaigns that don't actually send.

This should only be used in situations where all other sync parameters and field mappings can remain consistent between branches.""")
    label: str = Field(title="""Used in the UI when describing the location., e.g. 'Channel','Customer List'. 
It should completely describe the behaviour when used in a sentence like this: 
'Changes will be tested against a different <label> when running in a branch.'""")

class OutboundTargetType(BaseModel):
    """
    Some products have APIs that can be grouped together in ways that support different strategies and may or may not support toggling.
    The label should answer the question: "What would you like to sync to?"
    Examples:
    - A CRM system may have "Standard objects", "Custom objects" or "Events"
    - A messaging platform may have "Channels", "Users" or "Messages"
    - A marketing platform may have "Customer lists", "Campaigns" or "Automations"
    - An Ad platform may have "Campaigns", "Ad groups" or "Ads"
    The target type cannot be changed after the sync is created.
    """
    label: str
    supported_strategies: List[str] = Field(
        title="The names of the sync strategies supported by this target. Each one must match the name of a sync strategy declared in supported_outbound_strategies."
    )
    target_parameter: Optional[OutboundTargetParameter] = Field(
        default=None,
        title="""The sync configuration parameter that designates the target object, if applicable. For example, 'object_name' or 'channel_name'. 
This will be used for two purposes:
1. To show a more readable indication of what this sync is doing in the UI, e.g. Standard object: Account
2. Designates this field as serving as a br toggle for testing in production.""")


class OutboundSyncStrategy(SubscriptableBaseModel, ABC):
    """OutboundSyncStrategy is a base class for all outbound sync strategies.
    Each implementation decides on what pattern of record changes it needs to observe.
    For each type of record change, an OutboundSyncAction describes what it will do in the target app.

    Custom OutboundSyncStrategies can be devised, which provide for use cases beyond applying records
    and publishing events.

    """

    name: str
    description: str
    icon_source: str = ICON_URL_CODE
    action_on_record_create: Optional[OutboundSyncAction] = Field(default=None)
    action_on_record_update: Optional[OutboundSyncAction] = Field(default=None)
    action_on_record_delete: Optional[OutboundSyncAction] = Field(default=None)
    action_on_record_unchanged: Optional[OutboundSyncAction] = Field(default=None)
    custom_strategy: bool = True

    def __eq__(self, other:OutboundSyncStrategy):
        if hasattr(other, 'custom_strategy') and hasattr(other, 'name'):
            return (
                self.custom_strategy == other.custom_strategy
                and self.name == other.name
            )
        else:
            return False

    def __init__(self, **data):
        """
        Initialises an OutboundSyncStrategy
        """
        if "name" not in data:
            raise ValueError("'name' not set on OutboundSyncStrategy object")
        if "custom_strategy" in data and data["custom_strategy"] is False:
            # The built-in outbound sync strategies do not need to have their entire contents stored, just the name
            if self.__class__ != STANDARD_OUTBOUND_SYNC_STRATEGIES[data["name"]]:
                data = {
                    **data,
                    **STANDARD_OUTBOUND_SYNC_STRATEGIES[data["name"]]().__dict__,
                }
        super().__init__(**data)

    @model_serializer(mode='wrap')
    # no return type hint, see https://github.com/fastapi/fastapi/discussions/10661#discussioncomment-7631104
    def ser_model(self,handler,info:SerializationInfo):
        serialized:Dict[str,Any] = handler(self)
        if not self.custom_strategy and (info.exclude_none is None or info.exclude_none == False):
            return {k:v for k,v in serialized.items() if k not in [
                "description",
                "icon_source",
                "action_on_record_create",
                "action_on_record_update",
                "action_on_record_delete",
                "action_on_record_unchanged"]}
        return serialized
    
    def model_dump_no_trim(self) -> Dict[str, Any]:
        # we use our own special include value to signal not to trim
        return self.model_dump(exclude_none=True)
    

class CreateSyncStrategy(OutboundSyncStrategy):
    """
    The standard Create sync strategy.
    Record creation -> CreateSyncAction
    """

    def __init__(self):
        OutboundSyncStrategy.__init__(
            self,
            name="Create",
            description="Creates new objects only, does not update or delete",
            action_on_record_create=CreateSyncAction(),
            icon_source=ICON_URL_ADD,
            custom_strategy=False,
        )


class UpsertSyncStrategy(OutboundSyncStrategy):
    """
    The standard Upsert sync strategy.
    Record creation -> CreateSyncAction
    Record update -> UpdateSyncAction
    """

    def __init__(self):
        OutboundSyncStrategy.__init__(
            self,
            name="Upsert",
            description="Creates new objects, updates existing objects, does not delete",
            action_on_record_create=CreateSyncAction(),
            action_on_record_update=UpdateSyncAction(),
            icon_source=ICON_URL_MERGE,
            custom_strategy=False,
        )


class UpdateSyncStrategy(OutboundSyncStrategy):
    """
    The standard Update sync strategy, designed for applying updates to records which already exist in the remote.
    Record create -> UpdateSyncAction
    Record update -> UpdateSyncAction
    """

    def __init__(self):
        OutboundSyncStrategy.__init__(
            self,
            name="Update",
            description="Updates existing objects only",
            action_on_record_create=UpdateSyncAction(),
            action_on_record_update=UpdateSyncAction(),
            icon_source=ICON_URL_CALL_MADE,
            custom_strategy=False,
        )



class DeleteSyncStrategy(OutboundSyncStrategy):
    """
    The standard Delete sync strategy.
    Record deletion -> DeleteSyncAction
    """

    def __init__(self):
        OutboundSyncStrategy.__init__(
            self,
            name="Delete",
            description="Deletes objects as they appear in the source",
            action_on_record_create=DeleteSyncAction(),
            icon_source=ICON_URL_DELETE,
            custom_strategy=False,
        )


class MirrorSyncStrategy(OutboundSyncStrategy):
    """
    The standard Mirror sync strategy.
    Record creation -> CreateSyncAction
    Record update -> UpdateSyncAction
    Record delete -> DeleteSyncAction
    """

    def __init__(self):
        OutboundSyncStrategy.__init__(
            self,
            name="Mirror",
            description="Creates new objects, updates existing objects, deletes when removed",
            action_on_record_create=CreateSyncAction(),
            action_on_record_update=UpdateSyncAction(),
            action_on_record_delete=DeleteSyncAction(),
            icon_source=ICON_URL_BASELINE_MERGE,
            custom_strategy=False,
        )


class SendSyncStrategy(OutboundSyncStrategy):
    """
    The standard Send sync strategy.
    Record creation -> SendSyncAction
    """

    def __init__(self):
        OutboundSyncStrategy.__init__(
            self,
            name="Send",
            description="Sends new objects. Similar to create, but intended for event-style rather than record-style syncs",
            action_on_record_create=SendSyncAction(),
            icon_source=ICON_URL_ADD,
            custom_strategy=False,
        )


class ReplaceSyncStrategy(OutboundSyncStrategy):
    """
    The standard Replace sync strategy.
    This is a special strategy that means all records that currently exist will be recreated each sync.
    Record creation -> RecreateSyncAction
    Record update -> RecreateSyncAction
    Record unchanged -> RecreateSyncAction
    """

    def __init__(self):
        OutboundSyncStrategy.__init__(
            self,
            name="Replace",
            description="Applies all current records, regardless of history",
            action_on_record_create=RecreateSyncAction(),
            action_on_record_update=RecreateSyncAction(),
            action_on_record_unchanged=RecreateSyncAction(),
            icon_source=ICON_URL_REPLACE,
            custom_strategy=False,
        )


STANDARD_OUTBOUND_SYNC_STRATEGIES: Dict[str, OutboundSyncStrategy] = {
    "Create": CreateSyncStrategy,
    "Upsert": UpsertSyncStrategy,
    "Update": UpdateSyncStrategy,
    "Delete": DeleteSyncStrategy,
    "Mirror": MirrorSyncStrategy,
    "Replace": ReplaceSyncStrategy,
    "Send": SendSyncStrategy,
}


class InboundSyncStreamsConfiguration(SubscriptableBaseModel):
    """
    Encapsulates the whole value stored under STREAMS_CONFIGURATION. Includes configuration of streams,
    as well as which ones were excluded and how to treat newly discovered objects
    """

    include_new_streams: bool
    new_stream_sync_strategy: Optional[InboundSyncStrategy] = Field(default=None)
    new_stream_storage_behaviour: Optional[InboundStorageBehaviour] = Field(default=None)
    included_streams: Dict[str, StoredStreamConfiguration]
    excluded_streams: List[str]
    bulk_configuration: Optional[InboundSyncBulkConfiguration] = None
    sync_strategy_bulk_configuration: Optional[InboundSyncStrategyBulkConfiguration] = None
    storage_behaviour_bulk_configuration: Optional[InboundStorageBehaviourBulkConfiguration] = None

    """
    We use a model_validator to manage the migration from bulk_configuration to the new
    sync_strategy_bulk_configuration and storage_behaviour_bulk_configuration objects.
    This means that if bulk_configuration is set, it will be used to populate the new objects.
    """
    @model_validator(mode='before')
    @classmethod
    def migrate_bulk_configuration(cls, data: Any) -> Any:
        if 'sync_strategy_bulk_configuration' in data \
                and data['sync_strategy_bulk_configuration'] is not None \
                and 'storage_behaviour_bulk_configuration' in data \
                and data['storage_behaviour_bulk_configuration'] is not None:
            return data
        if 'bulk_configuration' not in data:
            # This was previously a default value
            data['bulk_configuration'] = InboundSyncBulkConfiguration.CUSTOMIZE.value
        # Recently deprecated values
        # AUTO_MERGE = "Auto / Merge changes" # Merge
        # AUTO_APPEND = "Auto / Keep history"  # Append
        # CUSTOMIZE = "Customize - choose sync behaviours for each object"
        # Deprecated longer ago
        # ALL_FULL_REPLACE = "All Objects - Full refresh / Replace"
        # ALL_FULL_APPEND = "All Objects - Full refresh / Append"
        # ALL_INCR_MERGE = "All Objects - Incremental / Merge"
        # ALL_INCR_APPEND = "All Objects - Incremental / Append"
        if data['bulk_configuration']== InboundSyncBulkConfiguration.AUTO_MERGE.value:
            data['sync_strategy_bulk_configuration']= InboundSyncStrategyBulkConfiguration.AUTO.value
            data['storage_behaviour_bulk_configuration']= InboundStorageBehaviourBulkConfiguration.MERGE.value
        elif data['bulk_configuration']== InboundSyncBulkConfiguration.AUTO_APPEND.value:
            data['sync_strategy_bulk_configuration']= InboundSyncStrategyBulkConfiguration.AUTO.value
            data['storage_behaviour_bulk_configuration']= InboundStorageBehaviourBulkConfiguration.APPEND.value
        elif data['bulk_configuration']== InboundSyncBulkConfiguration.CUSTOMIZE.value:
            data['sync_strategy_bulk_configuration']= InboundSyncStrategyBulkConfiguration.MANUAL.value
            data['storage_behaviour_bulk_configuration']= InboundStorageBehaviourBulkConfiguration.MANUAL.value
        elif data['bulk_configuration']== InboundSyncBulkConfiguration.ALL_FULL_REPLACE.value:
            data['sync_strategy_bulk_configuration']= InboundSyncStrategyBulkConfiguration.MANUAL.value
            data['storage_behaviour_bulk_configuration']= InboundStorageBehaviourBulkConfiguration.MERGE.value
        elif data['bulk_configuration']== InboundSyncBulkConfiguration.ALL_FULL_APPEND.value:
            data['sync_strategy_bulk_configuration']= InboundSyncStrategyBulkConfiguration.MANUAL.value
            data['storage_behaviour_bulk_configuration']= InboundStorageBehaviourBulkConfiguration.APPEND.value
        elif data['bulk_configuration']== InboundSyncBulkConfiguration.ALL_INCR_MERGE.value:
            data['sync_strategy_bulk_configuration']= InboundSyncStrategyBulkConfiguration.AUTO.value
            data['storage_behaviour_bulk_configuration']= InboundStorageBehaviourBulkConfiguration.MERGE.value
        elif data['bulk_configuration']== InboundSyncBulkConfiguration.ALL_INCR_APPEND.value:
            data['sync_strategy_bulk_configuration']= InboundSyncStrategyBulkConfiguration.AUTO.value
            data['storage_behaviour_bulk_configuration']= InboundStorageBehaviourBulkConfiguration.APPEND.value
            # remove this once the old UI is deprecated
            #del data['bulk_configuration']
        return data


class StoredStreamConfiguration(SubscriptableBaseModel):
    """
    Encapsulates all of the configuration necessary to sync an inbound stream.
    This information is parsed from the metadata of the streams Sync config object, for convenience.
    """

    stream_name: str
    sync_strategy: InboundSyncStrategy
    cursor_field: Optional[str] = Field(
        None,
        description="The field to use as a cursor",
    )
    primary_key_field: Optional[Union[str,List[str]]] = Field(
        None,
        description="The field(s) that will be used as primary key.",
    )
    storage_behaviour: InboundStorageBehaviour
    stream: StreamConfiguration
    latest_state: dict = Field(default_factory=dict,description="The latest state of the stream, used for incremental syncs")

    @field_validator('latest_state',mode='before')
    @classmethod
    def state_must_not_be_none(cls, v: Optional[dict]) -> dict:
        if v is None:
            return {}
        return v


class StreamConfiguration(SubscriptableBaseModel):
    """
    Encapsulates all of the configuration necessary to sync an inbound stream.
    Derived from the Airbyte protocol, with minor tweaks to suit our differences.
    """

    stream_name: str
    supported_sync_strategies: List[InboundSyncStrategy]
    source_defined_cursor: Optional[bool] = Field(
        None,
        description="If true, the plugin controls the cursor field",
    )
    source_defined_primary_key: Optional[Union[str,List[str]]] = Field(
        None,
        description="If defined, the plugin controls the primary key field",
    )
    # For SaaS applications, typically the primary key is a single field, known to the plugin.
    # For databases, the primary key can be composite, and the plugin may not know what it is if there is no key defined explicitly on the table.
    # this flag was added to support this scenario. If it is to True, then source_defined_primary_key will be a list of fields.
    # When this occurs, the plugin runtime will build the APP_IDENTIFIER from the fields in the order they are listed, by concatenating them.
    primary_key_can_be_composite: Optional[bool] = Field(
        False,
        description="If true, the primary key can be composite",
    )
    default_cursor_field: Optional[str] = Field(
        None,
        description="The default field to use as a cursor",
    )
    json_schema: Optional[Dict[str, Any]] = Field(
        None, description="JSON Schema for objects provided by stream"
    )
    metadata: dict = Field(
        default_factory=dict, description="Metadata associated with the stream. Be careful not to include environment-specific information like GUIDs"
    )
    depends_on_stream: Optional[str] = Field(
        None,
        description="Marks the stream as requiring another stream to be selected"
    )
    mandatory: bool = Field(
        False,
        description="Marks the stream as mandatory, meaning it cannot be excluded from the sync configuration"
    )


class StoredConfigurationValue(SubscriptableBaseModel):
    """
    A configuration value that was provided by a user (to configure a sync or connection).
    It contains only a string value and optionally some metadata, all of the display-related properties are discarded
    """

    value: str = Field(
        description="The stored value",
    )
    metadata: dict = Field(
        default_factory=dict, description="Metadata associated with the value"
    )

class NgrokTunnelSettings(SubscriptableBaseModel):
    """
    Stores connection information for ngrok tunnels.
    Retrieved from the connection configuration parameters/secrets.
    """

    endpoint_host: str = Field(
        description="The ngrok endpoint (x.ngrok.app)",
    )
    endpoint_port: int = Field(
        description="The ngrok endpoint port",
        default=443
    )
    client_certificate: str = Field(
        description="The ngrok client certificate, in PEM format",
    )
    client_key: str = Field(
        description="The ngrok client key, in PEM format",
    )

class OutboundRecordTransformationParameters(SubscriptableBaseModel):
    """
    Allows the plugin author to determine how records are transformed before being sent to the target app.
    Since conversion to objects causes a loss of some data types (e.g. timestamps and dates become strings),
    and different Snowflake accounts may have different timestamp output formats, specifying the format allows
    for a consistent result in the transformed records.
    """
    timestamp_tz_format: str = Field(
        default="YYYY-MM-DD HH24:MI:SS.FF3 TZHTZM",
        title="The format to use when converting TIMESTAMP_TZ values to strings in the transformed record."
    )
    timestamp_ntz_format: str = Field(
        default="YYYY-MM-DD HH24:MI:SS.FF3",
        title="The format to use when converting TIMESTAMP_NTZ values to strings in the transformed record."
    )
    timestamp_ltz_format: str = Field(
        default="YYYY-MM-DD HH24:MI:SS.FF3 TZHTZM",
        title="The format to use when converting TIMESTAMP_LTZ values to strings in the transformed record."
    )
    date_format: str = Field(
        default="YYYY-MM-DD",
        title="YYYY-MM-DD"
    )

class ConnectionConfigurationParameters(SubscriptableBaseModel):
    """
    Contains user-provided information completed during connection configuration.
    This acts as a base class since connection parameters are the first things collected.
    """

    connection_method: str
    connectivity_option: ConnectivityOption = Field(default=ConnectivityOption.DIRECT)
    connection_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    connection_secrets: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    ngrok_tunnel_settings: Optional[NgrokTunnelSettings] = Field(default=None)
    access_token_secret_name: Optional[str] = Field(default=None)

    _snowflake: Optional[Any] = PrivateAttr(  # or use Any to annotate the type and use Field to initialize
        default=None
    )

    @model_validator(mode='after')
    def validate_ngrok_tunnel_settings(self) -> Self:
        if self.connection_secrets:
            if "ngrok_client_certificate" in self.connection_secrets and \
                "ngrok_client_key" in self.connection_secrets and \
                "ngrok_endpoint_host" in self.connection_secrets and \
                "ngrok_endpoint_port" in self.connection_secrets:
                self.ngrok_tunnel_settings = NgrokTunnelSettings(
                    endpoint_host=self.connection_secrets["ngrok_endpoint_host"].value,
                    endpoint_port=int(self.connection_secrets["ngrok_endpoint_port"].value),
                    client_certificate=self.connection_secrets["ngrok_client_certificate"].value,
                    client_key=self.connection_secrets["ngrok_client_key"].value
                )
        return self

    def get_connection_parameter(self, parameter_name: str) -> StoredConfigurationValue:
        """
        Retrieves a connection parameter, which was collected during connection configuration.
        What you can expect to retrieve is based on the form definition returned by your connection_form function (form fields returned with secret=False).

        :param str parameter_name: The name of the parameter
        :return: the configuration value, which contains a string property named "value", and a metadata dict
        :rtype: StoredConfigurationValue
        :raises ValueError: if a connection parameter by that name does not exist
        """
        if self.connection_parameters is None:
            raise ValueError("Connection parameters were not provided")
        if parameter_name not in self.connection_parameters.keys():
            raise ValueError(f"Connection parameter '{parameter_name}' not available")
        return self.connection_parameters[  # pylint: disable=unsubscriptable-object
            parameter_name
        ]

    def get_connection_secret(self, parameter_name: str) -> StoredConfigurationValue:
        """
        Retrieves a connection secret, which was collected during connection configuration.
        What you can expect to retrieve is based on the form definition returned by your connection_form function (form fields returned with secret=False).

        :param str parameter_name: The name of the parameter
        :return: the configuration value, which contains a string property named "value", and a metadata dict
        :rtype: StoredConfigurationValue
        :raises ValueError: if a connection parameter by that name does not exist
        """
        if parameter_name=='access_token' and self.access_token_secret_name is not None:
            import _snowflake # pylint: disable=import-error, import-outside-toplevel # type: ignore
            return StoredConfigurationValue(
                value=_snowflake.get_oauth_access_token(self.access_token_secret_name)
            )
        if self.connection_secrets is None:
            raise ValueError("Connection secrets were not provided")
        if parameter_name not in self.connection_secrets.keys():
            raise ValueError(f"Connection secret '{parameter_name}' not available")
        return self.connection_secrets[  # pylint: disable=unsubscriptable-object
            parameter_name
        ]


class SyncConfigurationParameters(ConnectionConfigurationParameters):
    """
    A base class for Sync configuration parameters.
    """

    connection_method: str
    connection_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    connection_secrets: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    sync_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    current_form_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)

    def sync_parameter_exists(self, parameter_name: str) -> bool:
        """
        Advises whether or not a sync parameter exists.

        :param str parameter_name: The name of the parameter
        :return: True if the given parameter exists, otherwise False
        :rtype: bool
        """
        return parameter_name in self.sync_parameters.keys()

    def get_sync_parameter(
        self, parameter_name: str, default_value: Optional[str] = None
    ) -> StoredConfigurationValue:
        """
        Retrieves a sync parameter, which was collected during sync configuration.
        What you can expect to retrieve is based on the form definition returned by your configuration function.

        :param str parameter_name: The name of the parameter
        :param str default_value: A default value to return (under the "value" property) if the parameter does not exist
        :return: the configuration value, which contains a string property named "value", and a metadata dict
        :rtype: StoredConfigurationValue
        :raises ValueError: if a sync parameter by that name does not exist, and no default was provided
        """
        if parameter_name not in self.sync_parameters.keys():
            if default_value is not None:
                return StoredConfigurationValue(value=default_value)
            raise ValueError(f"Sync parameter '{parameter_name}' not available")
        return self.sync_parameters[  # pylint: disable=unsubscriptable-object
            parameter_name
        ]

    def get_current_form_parameter(
        self, parameter_name: str, default_value: Optional[str] = None
    ) -> StoredConfigurationValue:
        """
        Retrieves a parameter from the current form. The "current form" refers to a temporary form which is not part of the final sync configuration,
        such as a new option creator for a data source.
        What you can expect to retrieve is based on the form definition returned by your NewOptionCreator's creation form function.

        :param str parameter_name: The name of the parameter
        :param str default_value: A default value to return if the parameter does not exist
        :return: the configuration value, which contains a string property named "value", and a metadata dict
        :rtype: StoredConfigurationValue
        :raises ValueError: if a form parameter by that name does not exist, and no default was provided
        """
        if parameter_name not in self.current_form_parameters.keys():
            if default_value is not None:
                return StoredConfigurationValue(value=default_value)
            raise ValueError(f"Form parameter '{parameter_name}' not available")
        return self.current_form_parameters[  # pylint: disable=unsubscriptable-object
            parameter_name
        ]

    def condense_current_form_parameters(self, exclude_fields: List[str]) -> dict:
        """
        Takes a dictionary representing a completed form, and condenses it into a simple dictionary containing just the values of each field.
        This is useful for building a metadata object that typically accompanies a value in a StoredConfigurationValue.
        """
        return_dict = {}
        for dict_key in self.current_form_parameters.keys():
            if dict_key not in exclude_fields:
                return_dict[
                    dict_key
                ] = self.current_form_parameters[  # pylint: disable=unsubscriptable-object
                    dict_key
                ].value
        return return_dict


class OutboundSyncConfigurationParameters(SyncConfigurationParameters):
    """
    Contains user-provided information completed during outbound connection/sync configuration.
    """

    connection_method: str
    target_type: Optional[str] = Field(default=None, description="The label of the OutboundTargetType selected by the user")
    connection_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    connection_secrets: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    sync_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    current_form_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    sync_strategy: Optional[OutboundSyncStrategy] = Field(default=None)
    field_mappings: Optional[StoredMappingValue] = Field(default=None)


class InboundSyncConfigurationParameters(SyncConfigurationParameters):
    """
    Contains user-provided information completed during inbound connection/sync configuration.
    If currently_selected_streams is None, return all streams but only include json schema if it's feasible.
    If currently_selected_streams is not None, you should return a list of only those streams  with full json schema included.
    If json schema is not returned in either of these cases, then the user will not see the fields in the UI and the 
    normalized view will look the same as the raw table.
    Note that currently_selected_streams only relates to stream listers. When a sync occurs, the InboundSyncRequest includes
    the requested streams.
    """

    connection_method: str
    connection_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    connection_secrets: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    sync_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    current_form_parameters: Optional[Dict[str, StoredConfigurationValue]] = Field(default=None)
    currently_selected_streams: Optional[List[str]] = Field(default=None)


class StoredJinjaTemplate(SubscriptableBaseModel):
    """
    Mapping information that was provided by a user (to configure a sync or connection).
    It contains either a list of mappings or a jinja template
    """

    mapper_type: Literal["jinja_template"] = "jinja_template"
    additional_column_expressions: Dict[str, str] = Field(default={})
    jinja_template: str


class StoredFieldMappings(SubscriptableBaseModel):
    """
    Mapping information that was provided by a user (to configure a sync or connection).
    It contains either a list of mappings or a jinja template
    """

    mapper_type: Literal["field_mapping_selector"] = "field_mapping_selector"
    field_mappings: List[StoredFieldMapping]


StoredMappingValue = Annotated[
    Union[StoredJinjaTemplate, StoredFieldMappings], Field(discriminator="mapper_type")
]


class SyncScheduleSnowflakeTask(SubscriptableBaseModel):
    """
    A sync schedule which uses Snowflake tasks to initiate runs.

    Args:
        sync_frequency (str): The cron expression for this schedule
        sync_frequency_name (str): The plain english name for this cron schedule
        warehouse (str): The Snowflake warehouse which this task uses
        time_limit_mins (int): The maximum time the sync can run for before being cancelled
        daily_hour (Optional[int]): If the sync frequency is Daily, the hour it runs
        daily_minute (Optional[int]): If the sync frequency is Daily, the minute it runs
        minute_of_hour (Optional[int]): If the sync frequency is Hourly, the minute of the hour it runs

    """

    mode: Literal["snowflake_task"] = "snowflake_task"
    sync_frequency: str
    sync_frequency_name: Literal["1 min", "5 mins", "15 mins", "Hourly", "Daily","Custom"]
    warehouse: Optional[str] = Field(default=None)
    time_limit_mins: int = 60 * 4
    daily_hour: Optional[int] = Field(default=None)
    daily_minute: Optional[int] = Field(default=None)
    minute_of_hour: Optional[int] = Field(default=None)


class SyncScheduleDbt(SubscriptableBaseModel):
    """
    A sync schedule which runs when initiated during a dbt run, using the Omnata dbt package.

    Args:
        dbt_prod_target_name (str): The name of the dbt target used for production runs
        task_warehouse_dbt_defined (bool): If true, the dbt package will set the schedule settings
        warehouse (str): The Snowflake warehouse which this task uses. If task_warehouse_dbt_defined is True, this is only an initial default before the first run occurs
        time_limit_mins (int): The maximum time the sync can run for before being cancelled
        dbt_dev_target_name (str): The name of the dbt target used by developers outside of CI
        dbt_sync_model_name (str): The name of the dbt model used to run the sync
        dbt_source_model_name (str): The name of the dbt model used as a source for the run, if the sync is Outbound. This will be resolved at runtime and replaces the configured source table
        is_dbt_cloud (bool): If true, dbt cloud is in use
    """

    mode: Literal["dbt"] = "dbt"
    dbt_prod_target_name: str = "prod"
    task_warehouse_dbt_defined: bool = True
    warehouse: Optional[str] = Field(default=None)
    time_limit_mins: int = 60 * 4
    dbt_dev_target_name: str = "dev"
    dbt_sync_model_name: str
    dbt_source_model_name: Optional[str] = Field(default=None)
    is_dbt_cloud: bool = True


class SyncScheduleDependant(SubscriptableBaseModel):
    """
    A sync schedule which runs the sync at the same time or after another sync.

    Args:
        run_when (Literal["after_parent_completes","at_same_time_as"]): Determines if this sync runs at the same time as the parent, or after it completes
        warehouse (str): The Snowflake warehouse which this task uses
        time_limit_mins (int): The maximum time the sync can run for before being cancelled
        selected_sync (int): The sync ID of the sync to depend on
    """

    mode: Literal["dependent"] = "dependent"
    run_when: Literal[
        "after_parent_completes", "at_same_time_as"
    ] = "after_parent_completes"
    warehouse: Optional[str] = Field(default=None)
    time_limit_mins: int = 60 * 4
    selected_sync: int


class SyncScheduleManual(SubscriptableBaseModel):
    """
    A sync schedule which runs only when manually requested.

    Args:
        warehouse (str): The Snowflake warehouse which this task uses
        time_limit_mins (int): The maximum time the sync can run for before being cancelled
    """

    mode: Literal["manual"] = "manual"
    warehouse: Optional[str] = Field(default=None)
    time_limit_mins: int = 60 * 4


SyncSchedule = Annotated[
    Union[
        SyncScheduleSnowflakeTask,
        SyncScheduleDbt,
        SyncScheduleDependant,
        SyncScheduleManual,
    ],
    Field(discriminator="mode"),
]


class StoredFieldMapping(SubscriptableBaseModel):
    """
    A column->field mapping value that was provided by a user when configuring a sync.
    The source can either be a column name (e.g. EMAIL_ADDRESS) or an expression (e.g. CONTACT_DETAILS:email_address::varchar or FIRST_NAME||' '||LAST_NAME))
    """

    source_type: Literal["column_name", "expression"]
    source_value: str
    app_field: str
    app_metadata: dict = Field(default_factory=dict)


StoredStreamConfiguration.model_rebuild()
InboundSyncStreamsConfiguration.model_rebuild()
StoredFieldMappings.model_rebuild()
OutboundSyncConfigurationParameters.model_rebuild()

@tracer.start_as_current_span("get_secrets")
def get_secrets(oauth_secret_name: Optional[str], other_secrets_name: Optional[str]
) -> Dict[str, StoredConfigurationValue]:
    connection_secrets = {}
    import _snowflake # pylint: disable=import-error, import-outside-toplevel # type: ignore
    if oauth_secret_name is not None:
        connection_secrets["access_token"] = StoredConfigurationValue(
            value=_snowflake.get_oauth_access_token(oauth_secret_name)
        )
    if other_secrets_name is not None:
        try:
            secret_string_content = _snowflake.get_generic_secret_string(
                other_secrets_name
            )
            if len(secret_string_content) > 2:
                other_secrets = json.loads(secret_string_content)
                connection_secrets = {
                    **connection_secrets,
                    **TypeAdapter(Dict[str, StoredConfigurationValue]).validate_python(other_secrets),
                }
        except Exception as exception:
            logger.error(f"Error parsing secrets content for secret {other_secrets_name}: {str(exception)}")
            raise ValueError(f"Error parsing secrets content: {str(exception)}") from exception
    return connection_secrets
    