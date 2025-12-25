import datetime
import importlib
import json
import logging
import os
import sys
import time
import threading
from typing import Dict, List, Optional, cast

from pydantic import BaseModel,TypeAdapter  # pylint: disable=no-name-in-module
from pydantic_core import to_jsonable_python
from snowflake.snowpark import Session

from .api import PluginMessageStreamProgressUpdate, SyncRequestPayload, ConfigurationFormPayload
from .configuration import (
    ConnectionConfigurationParameters,
    InboundSyncConfigurationParameters,
    OutboundSyncConfigurationParameters,
    OutboundSyncStrategy,
    StoredConfigurationValue,
    StoredMappingValue,
    get_secrets,
    ConnectivityOption
)
from .forms import ConnectionMethod, FormInputField, FormOption
from .logging import OmnataPluginLogHandler, logger, tracer
from .omnata_plugin import (
    SnowflakeBillingEvent,
    BillingEventRequest,
    HttpRateLimiting,
    InboundSyncRequest,
    OmnataPlugin,
    OutboundSyncRequest,
    DeadlineReachedException,
)
from pydantic import TypeAdapter
from .rate_limiting import ApiLimits, RateLimitState
from opentelemetry import trace

IMPORT_DIRECTORY_NAME = "snowflake_import_directory"

class PluginEntrypoint:
    """
    This class gives each plugin's stored procs an initial point of contact.
    It will only work within Snowflake because it uses the _snowflake module.
    """

    def __init__(
        self, plugin_fqn: str, session: Session, module_name: str, class_name: str
    ):
        logger.info(f"Initialising plugin entrypoint for {plugin_fqn}")
        with tracer.start_as_current_span("plugin_initialization") as span:
            self._session = session
            import_dir = sys._xoptions[IMPORT_DIRECTORY_NAME]
            span.add_event("Adding plugin zip to path")
            sys.path.append(os.path.join(import_dir, "app.zip"))
            span.add_event("Importing plugin module")
            module = importlib.import_module(module_name)
            class_obj = getattr(module, class_name)
            self._plugin_instance: OmnataPlugin = class_obj()
            self._plugin_instance._session = session  # pylint: disable=protected-access
            # logging defaults
            snowflake_logger = logging.getLogger("snowflake")
            snowflake_logger.setLevel(logging.WARN) # we don't want snowflake queries being logged by default
            # also snowflake.snowpark._internal.open_telemetry can be very noisy, so we set it to ERROR
            snowflake_telemetry_logger = logging.getLogger("snowflake.snowpark._internal.open_telemetry")
            snowflake_telemetry_logger.setLevel(logging.ERROR)
            # the sync engine can tell the plugin to override log level via a session variable
            if session is not None:
                try:
                    span.add_event("Checking log level overrides")
                    v = session.sql("select getvariable('LOG_LEVEL_OVERRIDES')").collect()
                    result = v[0][0]
                    if result is not None:
                        log_level_overrides:Dict[str,str] = json.loads(result)
                        span.add_event("Applying log level overrides",log_level_overrides)
                        for logger_name,level in log_level_overrides.items():
                            logger_override = logging.getLogger(logger_name)
                            logger_override.setLevel(level)
                            logger_override.propagate = False
                            for handler in logger_override.handlers:
                                handler.setLevel(level)
                except Exception as e:
                    logger.error(f"Error setting log level overrides: {str(e)}")
        

    def sync(self, sync_request: Dict):
        request:SyncRequestPayload = TypeAdapter(SyncRequestPayload).validate_python(sync_request)
        logger.add_extra('omnata.operation', 'sync')
        logger.add_extra('omnata.sync.id', request.sync_id)
        logger.add_extra('omnata.sync.direction', request.sync_direction)
        logger.add_extra('omnata.connection.id', request.connection_id)
        logger.add_extra('omnata.sync_run.id', request.run_id)
        logger.add_extra('omnata.sync_branch.id', request.sync_branch_id)
        logger.add_extra('omnata.sync_branch.name', request.sync_branch_name)
        logger.info("Entered sync method")
        with tracer.start_as_current_span("initialization") as span:
            span.add_event("Fetching secrets")

            connection_secrets = get_secrets(
                request.oauth_secret_name, request.other_secrets_name
            )
            span.add_event("Configuring log handler")
            omnata_log_handler = OmnataPluginLogHandler(
                session=self._session,
                sync_id=request.sync_id,
                sync_branch_id=request.sync_branch_id,
                connection_id=request.connection_id,
                sync_run_id=request.run_id,
            )

            omnata_log_handler.register(
                request.logging_level, self._plugin_instance.additional_loggers()
            )
            # construct some connection parameters for the purpose of getting the api limits
            connection_parameters = ConnectionConfigurationParameters(
                connection_method=request.connection_method,
                connectivity_option=request.connectivity_option,
                connection_parameters=request.connection_parameters,
                connection_secrets=connection_secrets
            )
            if request.oauth_secret_name is not None:
                connection_parameters.access_token_secret_name = request.oauth_secret_name
            span.add_event("Configuring API Limits")
            all_api_limits = self._plugin_instance.api_limits(connection_parameters)
            logger.info(
                f"Default API limits: {json.dumps(to_jsonable_python(all_api_limits))}"
            )
            all_api_limits_by_category = {
                api_limit.endpoint_category: api_limit for api_limit in all_api_limits
            }
            all_api_limits_by_category.update(
                {
                    k: v
                    for k, v in [
                        (x.endpoint_category, x) for x in request.api_limit_overrides
                    ]
                }
            )
            api_limits = list(all_api_limits_by_category.values())
            return_dict = {}
            logger.info(
                f"Rate limits state: {json.dumps(to_jsonable_python(request.rate_limits_state))}"
            )
            (rate_limit_state_all, rate_limit_state_this_branch) = RateLimitState.collapse(request.rate_limits_state,request.sync_id, request.sync_branch_name)
            # if any endpoint categories have no state, give them an empty state
            for api_limit in api_limits:
                if api_limit.endpoint_category not in rate_limit_state_all:
                    rate_limit_state_all[api_limit.endpoint_category] = RateLimitState(
                        wait_until=None, previous_request_timestamps=[]
                    )
                if api_limit.endpoint_category not in rate_limit_state_this_branch:
                    rate_limit_state_this_branch[api_limit.endpoint_category] = RateLimitState(
                        wait_until=None, previous_request_timestamps=[]
                    )

        if request.sync_direction == "outbound":
            parameters = OutboundSyncConfigurationParameters(
                connection_method=request.connection_method,
                connectivity_option=request.connectivity_option,
                connection_parameters=request.connection_parameters,
                connection_secrets=connection_secrets,
                sync_parameters=request.sync_parameters,
                current_form_parameters={},
                target_type=request.target_type,
                sync_strategy=request.sync_strategy,
                field_mappings=request.field_mappings,
            )
            if request.oauth_secret_name is not None:
                parameters.access_token_secret_name = request.oauth_secret_name

            outbound_sync_request = OutboundSyncRequest(
                run_id=request.run_id,
                session=self._session,
                source_app_name=request.source_app_name,
                records_schema_name=request.records_schema_name,
                records_table_name=request.records_table_name,
                results_schema_name=request.results_schema_name,
                results_table_name=request.results_table_name,
                plugin_instance=self._plugin_instance,
                api_limits=api_limits,
                rate_limit_state_all=rate_limit_state_all,
                rate_limit_state_this_sync_and_branch=rate_limit_state_this_branch,
                run_deadline=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=request.time_limit_mins),
                # for now, use the development mode flag to disable background workers
                development_mode=self._plugin_instance.disable_background_workers,
                sync_id=request.sync_id,
                branch_name=request.sync_branch_name
            )
            try:
                self._plugin_instance._configuration_parameters = parameters
                with tracer.start_as_current_span("invoke_plugin") as span:
                    with HttpRateLimiting(outbound_sync_request, parameters):
                        self._plugin_instance.sync_outbound(parameters, outbound_sync_request)
                if self._plugin_instance.disable_background_workers is False:
                    with tracer.start_as_current_span("results_finalization") as span:
                        outbound_sync_request.apply_results_queue()
                        outbound_sync_request.apply_rate_limit_state()
                if outbound_sync_request.deadline_reached:
                    # if we actually hit the deadline, this is flagged by the cancellation checking worker and the cancellation
                    # token is set. We throw it here as an error since that's currently how it flows back to the engine with a DELAYED state
                    raise DeadlineReachedException()
            finally:
                try:
                    # cancel the thread so we don't leave anything hanging around and cop a nasty error
                    outbound_sync_request._thread_cancellation_token.set()  # pylint: disable=protected-access
                    if outbound_sync_request._apply_results_task is not None:
                        outbound_sync_request._apply_results_task.join()  # pylint: disable=protected-access
                    if outbound_sync_request._cancel_checking_task is not None:
                        outbound_sync_request._cancel_checking_task.join()  # pylint: disable=protected-access
                    if outbound_sync_request._rate_limit_update_task is not None:
                        outbound_sync_request._rate_limit_update_task.join()  # pylint: disable=protected-access
                except Exception as e:
                    logger.error(f"Error cleaning up threading: {str(e)}")


        elif request.sync_direction == "inbound":
            logger.info("Running inbound sync")
            parameters = InboundSyncConfigurationParameters(
                connection_method=request.connection_method,
                connectivity_option=request.connectivity_option,
                connection_parameters=request.connection_parameters,
                connection_secrets=connection_secrets,
                sync_parameters=request.sync_parameters,
                current_form_parameters={},
            )
            if request.oauth_secret_name is not None:
                parameters.access_token_secret_name = request.oauth_secret_name
            
            inbound_sync_request = InboundSyncRequest(
                run_id=request.run_id,
                session=self._session,
                source_app_name=request.source_app_name,
                results_schema_name=request.results_schema_name,
                results_table_name=request.results_table_name,
                plugin_instance=self._plugin_instance,
                api_limits=api_limits,
                rate_limit_state_all=rate_limit_state_all,
                rate_limit_state_this_sync_and_branch=rate_limit_state_this_branch,
                run_deadline=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=request.time_limit_mins),
                # for now, use the development mode flag to disable background workers
                development_mode=self._plugin_instance.disable_background_workers,
                streams=list(request.streams_configuration.included_streams.values()),
                omnata_log_handler=omnata_log_handler,
                sync_id=request.sync_id,
                branch_name=request.sync_branch_name
            )
            try:
                self._plugin_instance._configuration_parameters = parameters

                inbound_sync_request.update_activity("Invoking plugin")
                # plugin_instance._inbound_sync_request = outbound_sync_request
                with tracer.start_as_current_span("invoke_plugin"):
                    with HttpRateLimiting(inbound_sync_request, parameters):
                        self._plugin_instance.sync_inbound(parameters, inbound_sync_request)
                logger.info("Finished invoking plugin")
                if self._plugin_instance.disable_background_workers is False:
                    with tracer.start_as_current_span("results_finalization") as span:
                        inbound_sync_request.update_activity("Staging remaining records")
                        logger.info("Calling apply_results_queue")
                        inbound_sync_request.apply_results_queue()
                        try:
                            # this is not critical, we wouldn't fail the sync over rate limit usage capture
                            logger.info("Calling apply_rate_limit_state")
                            inbound_sync_request.apply_rate_limit_state()
                        except Exception as e:
                            logger.error(f"Error applying rate limit state: {str(e)}")
                    # here we used to do a final inbound_sync_request.apply_progress_updates(ignore_errors=False)
                    # but it was erroring too much since there was usually a lot of DDL activity on the Snowflake side
                    # so instead, we'll provide a final progress update via a return value from the proc
                final_progress_update = PluginMessageStreamProgressUpdate(
                    stream_total_counts=inbound_sync_request._stream_record_counts,
                    completed_streams=inbound_sync_request._completed_streams,
                    stream_errors=omnata_log_handler.stream_global_errors,
                    total_records_estimate=inbound_sync_request._total_records_estimate
                )
                return_dict["streams_requiring_view_refresh"] = inbound_sync_request.streams_requiring_view_refresh
                return_dict["final_progress_update"] = final_progress_update.model_dump()
                if inbound_sync_request.deadline_reached:
                    # if we actually hit the deadline, this is flagged by the cancellation checking worker and the cancellation
                    # token is set. We throw it here as an error since that's currently how it flows back to the engine with a DELAYED state
                    raise DeadlineReachedException()
            finally:
                # try to upload any remaining results
                try:
                    inbound_sync_request.apply_results_queue()
                except Exception as e:
                    logger.warning(f"Error uploading remaining results: {str(e)}", exc_info=True)
                # cancel the thread so we don't leave anything hanging around and cop a nasty error
                try:
                    inbound_sync_request._thread_cancellation_token.set()  # pylint: disable=protected-access
                    if inbound_sync_request._apply_results_task is not None:
                        inbound_sync_request._apply_results_task.join()  # pylint: disable=protected-access
                    if inbound_sync_request._cancel_checking_task is not None:
                        inbound_sync_request._cancel_checking_task.join()  # pylint: disable=protected-access
                    if inbound_sync_request._rate_limit_update_task is not None:
                        inbound_sync_request._rate_limit_update_task.join()  # pylint: disable=protected-access
                except Exception as e:
                    logger.error(f"Error cleaning up threading: {str(e)}")
        logger.info("Finished applying records")
        return return_dict

    def configuration_form(self, configuration_form_request: Dict):
        request:ConfigurationFormPayload = TypeAdapter(ConfigurationFormPayload).validate_python(configuration_form_request)
        logger.add_extra('omnata.operation', 'configuration_form')
        logger.add_extra('omnata.connection.connectivity_option', request.connectivity_option)
        logger.add_extra('omnata.connection.connection_method', request.connection_method)
        logger.add_extra('omnata.configuration_form.function_name', request.function_name)
        logger.add_extra('omnata.sync.direction', request.sync_direction)

        logger.info("Entered configuration_form method")
        connection_secrets = get_secrets(request.oauth_secret_name, request.other_secrets_name)
        if request.sync_direction == "outbound":
            parameters = OutboundSyncConfigurationParameters(
                connection_parameters=request.connection_parameters,
                connection_secrets=connection_secrets,
                sync_strategy=request.sync_strategy,
                sync_parameters=request.sync_parameters,
                connection_method=request.connection_method,
                connectivity_option=request.connectivity_option,
                current_form_parameters=request.current_form_parameters,
                target_type=request.target_type
            )
        elif request.sync_direction == "inbound":
            parameters = InboundSyncConfigurationParameters(
                connection_parameters=request.connection_parameters,
                connection_secrets=connection_secrets,
                sync_parameters=request.sync_parameters,
                connection_method=request.connection_method,
                connectivity_option=request.connectivity_option,
                current_form_parameters=request.current_form_parameters,
            )
        else:
            raise ValueError(f"Unknown direction {request.sync_direction}")
        if request.oauth_secret_name is not None:
                parameters.access_token_secret_name = request.oauth_secret_name
        the_function = getattr(
            self._plugin_instance,
            request.function_name
        )
        with tracer.start_as_current_span("invoke_plugin"):
            script_result = the_function(parameters)
        if isinstance(script_result, BaseModel):
            script_result = script_result.model_dump()
        elif isinstance(script_result, List):
            if len(script_result) > 0 and isinstance(script_result[0], BaseModel):
                script_result = cast(List[BaseModel], script_result)
                script_result = [r.model_dump() for r in script_result]
        return script_result
        
    def inbound_list_streams(
        self,
        connectivity_option:str,
        connection_method: str,
        connection_parameters: Dict,
        oauth_secret_name: Optional[str],
        other_secrets_name: Optional[str],
        sync_parameters: Dict,
        selected_streams: Optional[List[str]], # None to return all streams without requiring schema
    ):
        logger.add_extra('omnata.operation', 'list_streams')
        logger.add_extra('omnata.connection.connectivity_option', connectivity_option)
        logger.add_extra('omnata.connection.connection_method', connection_method)
        logger.add_extra('omnata.sync.direction', 'inbound')
        logger.debug("Entered list_streams method")
        oauth_secret_name = normalise_nulls(oauth_secret_name)
        other_secrets_name = normalise_nulls(other_secrets_name)
        connection_secrets = get_secrets(oauth_secret_name, other_secrets_name)
        connectivity_option = TypeAdapter(ConnectivityOption).validate_python(connectivity_option)
        connection_parameters = TypeAdapter(
            Dict[str, StoredConfigurationValue]).validate_python(connection_parameters)
        sync_parameters = TypeAdapter(
            Dict[str, StoredConfigurationValue]).validate_python(sync_parameters)
        parameters = InboundSyncConfigurationParameters(
            connection_parameters=connection_parameters,
            connection_secrets=connection_secrets,
            sync_parameters=sync_parameters,
            connectivity_option=connectivity_option,
            connection_method=connection_method,
            current_form_parameters=None,
            currently_selected_streams=selected_streams
        )
        if oauth_secret_name is not None:
            parameters.access_token_secret_name = oauth_secret_name
        with tracer.start_as_current_span("invoke_plugin"):
            script_result = self._plugin_instance.inbound_stream_list(parameters)
        if isinstance(script_result, BaseModel):
            script_result = script_result.model_dump()
        elif isinstance(script_result, List):
            if len(script_result) > 0 and isinstance(script_result[0], BaseModel):
                script_result = [r.model_dump() for r in script_result]
        return script_result


    def construct_form_option(
        self,
        function_name: str,
        stored_values: List[Dict],
    ):
        logger.info("Entered construct_form_option method")
        stored_values_parsed = TypeAdapter(
            List[StoredConfigurationValue]).validate_python(stored_values)
        the_function = getattr(
            self._plugin_instance,
            function_name,
        )
        results:List[FormOption] = []
        for stored_value in stored_values_parsed:
            script_result = the_function(stored_value)
            if not isinstance(script_result, FormOption):
                raise ValueError(f"Expected a FormOption from function {function_name}, got {type(script_result)}")
            results.append(script_result.model_dump())
        return results

    def connection_form(self,connectivity_option: str):
        logger.add_extra('omnata.operation', 'connection_form')
        logger.add_extra('omnata.connection.connectivity_option', connectivity_option)
        connectivity_option = TypeAdapter(ConnectivityOption).validate_python(connectivity_option)
        logger.info("Entered connection_form method")
        with tracer.start_as_current_span("invoke_plugin"):
            if self._plugin_instance.connection_form.__code__.co_argcount==1:
                form: List[ConnectionMethod] = self._plugin_instance.connection_form()
            else:
                form: List[ConnectionMethod] = self._plugin_instance.connection_form(connectivity_option)
        return [f.model_dump() for f in form]

    def create_billing_events(self, session, event_request: Dict):
        logger.add_extra('omnata.operation', 'create_billing_events')
        logger.info("Entered create_billing_events method")
        request = TypeAdapter(BillingEventRequest).validate_python(event_request)
        with tracer.start_as_current_span("invoke_plugin"):
            events: List[SnowflakeBillingEvent] = self._plugin_instance.create_billing_events(
                request
            )
        # create each billing event, waiting a second between each one
        first_time = True
        for billing_event in events:
            if not first_time:
                time.sleep(1)
            else:
                first_time = False
            timestamp_value = int(billing_event.timestamp.timestamp()*1000)
            if billing_event.start_timestamp is None:
                billing_event.start_timestamp = billing_event.timestamp
            start_timestamp_value=int(billing_event.start_timestamp.timestamp()*1000)
            try:
                event_query = f"""call SYSTEM$CREATE_BILLING_EVENT(
                        $${billing_event.billing_class}$$,
                        $${billing_event.sub_class}$$,
                        {start_timestamp_value},
                        {timestamp_value},
                        {str(billing_event.base_charge)},
                        $${json.dumps(billing_event.objects)}$$,
                        $${json.dumps(billing_event.additional_info)}$$)
                        """
                logger.info(f"Executing billing event query: {event_query}")
                result = session.sql(event_query).collect()
                logger.info(f"Billing event result: {result}")
            except Exception as e:
                if '370001:3159209004' in str(e) or 'Application instance is not installed from listing' in str(e):
                    logger.warn('Billing event creation failed due to running internally to Omnata')
                else:
                    raise e
        return [e.model_dump() for e in events]

    def ngrok_post_tunnel_fields(
        self,
        connection_method: str,
        connection_parameters: Dict,
        oauth_secret_name: Optional[str],
        other_secrets_name: Optional[str],
        function_name: str,
    ) -> List[FormInputField]:
        raise ValueError(f"ngrok_post_tunnel_fields is deprecated")

    def network_addresses(self, connectivity_option:str, method: str, connection_parameters: Dict) -> List[str]:
        logger.info("Entered network_addresses method")
        logger.info(f"Connection parameters: {connection_parameters}")
        from omnata_plugin_runtime.omnata_plugin import (
            ConnectionConfigurationParameters,
        )

        return self._plugin_instance.network_addresses(
            ConnectionConfigurationParameters(
                connectivity_option=TypeAdapter(ConnectivityOption).validate_python(connectivity_option),
                connection_method=method,
                connection_parameters=TypeAdapter(
                    Dict[str, StoredConfigurationValue]).validate_python(connection_parameters),
                connection_secrets={},
            )
        )

    def connect(
        self,
        connectivity_option:str,
        method:str,
        connection_parameters: Dict,
        network_rule_name: str,
        oauth_secret_name: Optional[str],
        other_secrets_name: Optional[str],
    ):
        logger.add_extra('omnata.operation', 'connection_test')
        logger.add_extra('omnata.connection.connectivity_option', connectivity_option)
        logger.add_extra('omnata.connection.connection_method', method)
        logger.info("Entered connect method")
        logger.info(f"Connection parameters: {connection_parameters}")
        connection_secrets = get_secrets(oauth_secret_name, other_secrets_name)

        from omnata_plugin_runtime.omnata_plugin import (
            ConnectionConfigurationParameters,
        )
        parameters = ConnectionConfigurationParameters(
            connectivity_option=TypeAdapter(ConnectivityOption).validate_python(connectivity_option),
            connection_method=method,
            connection_parameters=TypeAdapter(
                Dict[str, StoredConfigurationValue]).validate_python(connection_parameters),
            connection_secrets=connection_secrets
        )
        if oauth_secret_name is not None:
            parameters.access_token_secret_name = oauth_secret_name
        with tracer.start_as_current_span("invoke_plugin"):
            connect_response = self._plugin_instance.connect(
                parameters=parameters
            )
        # the connect method can also return more network addresses. If so, we need to update the
        # network rule associated with the external access integration
        if connect_response is None:
            raise ValueError("Plugin did not return a ConnectResponse object from the connect method")
        if connect_response.network_addresses is not None:
            with tracer.start_as_current_span("network_rule_update") as network_rule_update_span:
                network_rule_update_span.add_event("Retrieving existing network rule")
                existing_rule_result = self._session.sql(
                    f"desc network rule {network_rule_name}"
                ).collect()
                rule_values: List[str] = existing_rule_result[0].value_list.split(",")
                rule_values = [r for r in rule_values if r != '']
                logger.info(f"Existing rules for {network_rule_name}: {rule_values}")
                for network_address in connect_response.network_addresses:
                    if network_address not in rule_values:
                        rule_values.append(network_address)
                #if len(rule_values)==0:
                #    logger.info("No network addresses for plugin, adding localhost")
                #    rule_values.append("https://localhost")
                logger.info(f"New rules for {network_rule_name}: {rule_values}")
                rule_values_string = ",".join([f"'{value}'" for value in rule_values])
                network_rule_update_span.add_event("Updating network rule")
                self._session.sql(
                    f"alter network rule {network_rule_name} set value_list = ({rule_values_string})"
                ).collect()

        return connect_response.model_dump()

    def api_limits(self,
                   connectivity_option:str,
                   method:str,
                    connection_parameters: Dict,
                    oauth_secret_name: Optional[str],
                    other_secrets_name: Optional[str]):
        logger.add_extra('omnata.operation', 'api_limits')
        logger.add_extra('omnata.connection.connectivity_option', connectivity_option)
        logger.add_extra('omnata.connection.connection_method', method)
        logger.info("Entered api_limits method")
        connection_secrets = get_secrets(oauth_secret_name, other_secrets_name)
        from omnata_plugin_runtime.omnata_plugin import (
            ConnectionConfigurationParameters,
        )
        connection_parameters = ConnectionConfigurationParameters(
            connectivity_option=TypeAdapter(ConnectivityOption).validate_python(connectivity_option),
            connection_method=method,
            connection_parameters=TypeAdapter(
                Dict[str, StoredConfigurationValue]).validate_python(connection_parameters),
            connection_secrets=connection_secrets
        )
        if oauth_secret_name is not None:
            connection_parameters.access_token_secret_name = oauth_secret_name
        with tracer.start_as_current_span("invoke_plugin"):
            response: List[ApiLimits] = self._plugin_instance.api_limits(connection_parameters)
        return [api_limit.model_dump() for api_limit in response]

    def outbound_record_validator(
        self,
        sync_parameters: Dict,
        field_mappings: Dict,
        transformed_record: Dict,
        source_types: Dict[str, str],
    ):
        # There's a bit of parsing here that could possibly be done outside of the handler function, but this shouldn't be too expensive
        sync_parameters: Dict[str, StoredConfigurationValue] = TypeAdapter(
            Dict[str, StoredConfigurationValue]).validate_python(sync_parameters)
        field_mappings: StoredMappingValue = TypeAdapter(StoredMappingValue).validate_python(field_mappings)
        return self._plugin_instance.outbound_record_validator(
            sync_parameters, field_mappings, transformed_record, source_types
        )


def normalise_nulls(obj):
    """
    If an object came through a SQL interface with a null value, we convert it to a regular None here
    """
    if type(obj).__name__ == "sqlNullWrapper":
        return None
    # handle a bunch of objects being given at once
    if type(obj).__name__ == "list":
        return [normalise_nulls(x) for x in obj]
    return obj
