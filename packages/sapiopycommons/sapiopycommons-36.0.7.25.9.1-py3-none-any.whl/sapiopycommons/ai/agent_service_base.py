from __future__ import annotations

import base64
import json
import logging
import re
import subprocess
import traceback
from abc import abstractmethod, ABC
from logging import Logger
from os import PathLike
from subprocess import CompletedProcess
from typing import Any, Iterable, Mapping, Sequence

from grpc import ServicerContext
from sapiopylib.rest.User import SapioUser, ensure_logger_initialized
from sapiopylib.rest.pojo.DateRange import DateRange
from sapiopylib.rest.pojo.datatype.FieldDefinition import AbstractVeloxFieldDefinition

from sapiopycommons.ai.external_credentials import ExternalCredentials
from sapiopycommons.ai.protoapi.agent.agent_pb2 import AgentDetailsResponsePbo, \
    AgentDetailsPbo, ProcessStepRequestPbo, ProcessStepResponsePbo, AgentOutputDetailsPbo, AgentIoConfigBasePbo, \
    AgentInputDetailsPbo, ExampleContainerPbo, ProcessStepResponseStatusPbo, AgentCitationPbo
from sapiopycommons.ai.protoapi.agent.agent_pb2_grpc import AgentServiceServicer
from sapiopycommons.ai.protoapi.agent.entry_pb2 import StepOutputBatchPbo, StepItemContainerPbo, \
    StepBinaryContainerPbo, StepCsvContainerPbo, StepCsvHeaderRowPbo, StepCsvRowPbo, StepJsonContainerPbo, \
    StepTextContainerPbo
from sapiopycommons.ai.protoapi.agent.item.item_container_pb2 import ContentTypePbo
from sapiopycommons.ai.protoapi.externalcredentials.external_credentials_pb2 import ExternalCredentialsPbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValueMapPbo, FieldValuePbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import VeloxFieldDefPbo, FieldTypePbo, \
    SelectionPropertiesPbo, IntegerPropertiesPbo, DoublePropertiesPbo, BooleanPropertiesPbo, StringPropertiesPbo, \
    FieldValidatorPbo, DatePropertiesPbo, BooleanDependentFieldEntryPbo, SelectionDependentFieldEntryPbo
from sapiopycommons.ai.protoapi.session.sapio_conn_info_pb2 import SapioUserSecretTypePbo, SapioConnectionInfoPbo
from sapiopycommons.ai.protobuf_utils import ProtobufUtils
from sapiopycommons.ai.test_client import ContainerType
from sapiopycommons.files.file_util import FileUtil
from sapiopycommons.files.temp_files import TempFileHandler
from sapiopycommons.general.aliases import FieldMap, FieldValue


# FR-47422: Created classes.
class SapioAgentResult(ABC):
    """
    A class representing a result from a Sapio agent. Instantiate one of the subclasses to create a result object.
    """

    @abstractmethod
    def to_proto(self) -> StepOutputBatchPbo | list[FieldValueMapPbo]:
        """
        Convert this SapioAgentResult object to a StepOutputBatchPbo or list of FieldValueMapPbo proto objects.
        """
        pass


class BinaryResult(SapioAgentResult):
    """
    A class representing binary results from a Sapio agent.
    """
    binary_data: list[bytes]
    content_type: str
    file_extensions: list[str]
    name: str

    def __init__(self, binary_data: list[bytes], content_type: str = "binary", file_extensions: list[str] = None,
                 name: str | None = None):
        """
        :param binary_data: The binary data as a list of bytes.
        :param content_type: The content type of the data.
        :param file_extensions: A list of file extensions that this binary data can be saved as.
        :param name: An optional identifying name for this result that will be accessible to the next agent.
        """
        self.binary_data = binary_data
        self.content_type = content_type
        self.file_extensions = file_extensions if file_extensions else []
        self.name = name

    def to_proto(self) -> StepOutputBatchPbo | list[FieldValueMapPbo]:
        return StepOutputBatchPbo(
            item_container=StepItemContainerPbo(
                content_type=ContentTypePbo(name=self.content_type, extensions=self.file_extensions),
                container_name=self.name,
                binary_container=StepBinaryContainerPbo(items=self.binary_data)
            )
        )


class CsvResult(SapioAgentResult):
    """
    A class representing CSV results from a Sapio agent.
    """
    csv_data: list[dict[str, Any]]
    content_type: str
    file_extensions: list[str]
    name: str

    def __init__(self, csv_data: list[dict[str, Any]], content_type: str = "csv", file_extensions: list[str] = None,
                 name: str | None = None):
        """
        :param csv_data: The list of CSV data results, provided as a list of dictionaries of column name to value.
        :param content_type: The content type of the data.
        :param file_extensions: A list of file extensions that this binary data can be saved as.
        :param name: An optional identifying name for this result that will be accessible to the next agent.
        """
        self.csv_data = csv_data
        self.content_type = content_type
        self.file_extensions = file_extensions if file_extensions else ["csv"]
        self.name = name

    def to_proto(self) -> StepOutputBatchPbo | list[FieldValueMapPbo]:
        return StepOutputBatchPbo(
            item_container=StepItemContainerPbo(
                content_type=ContentTypePbo(name=self.content_type, extensions=self.file_extensions),
                container_name=self.name,
                csv_container=StepCsvContainerPbo(
                    header=StepCsvHeaderRowPbo(cells=self.csv_data[0].keys()),
                    items=[StepCsvRowPbo(cells=[str(x) for x in row.values()]) for row in self.csv_data]
                )
            ) if self.csv_data else None
        )


class FieldMapResult(SapioAgentResult):
    """
    A class representing field map results from a Sapio agent.
    """
    field_maps: list[FieldMap]

    def __init__(self, field_maps: list[FieldMap]):
        """
        :param field_maps: A list of field maps, where each map is a dictionary of field names to values. Each entry
            will create a new data record in the system, so long as the agent definition specifies an output data type
            name.
        """
        self.field_maps = field_maps

    def to_proto(self) -> StepOutputBatchPbo | list[FieldValueMapPbo]:
        new_records: list[FieldValueMapPbo] = []
        for field_map in self.field_maps:
            fields: dict[str, FieldValuePbo] = {}
            for field, value in field_map.items():
                field_value = FieldValuePbo()
                if isinstance(value, str):
                    field_value.string_value = value
                elif isinstance(value, int):
                    field_value.int_value = value
                elif isinstance(value, float):
                    field_value.double_value = value
                elif isinstance(value, bool):
                    field_value.bool_value = value
                fields[field] = field_value
            new_records.append(FieldValueMapPbo(fields=fields))
        return new_records


class JsonResult(SapioAgentResult):
    """
    A class representing JSON results from a Sapio agent.
    """
    json_data: list[dict[str, Any]]
    content_type: str
    file_extensions: list[str]
    name: str

    def __init__(self, json_data: list[dict[str, Any]], content_type: str = "json", file_extensions: list[str] = None,
                 name: str | None = None):
        """
        :param json_data: The list of JSON data results. Each entry in the list represents a separate JSON object.
            These entries must be able to be serialized to JSON using json.dumps().
        :param content_type: The content type of the data.
        :param file_extensions: A list of file extensions that this binary data can be saved as.
        :param name: An optional identifying name for this result that will be accessible to the next agent.
        """
        # Verify that the given json_data is actually a list of dictionaries.
        if not isinstance(json_data, list) or not all(isinstance(x, dict) for x in json_data):
            raise ValueError("json_data must be a list of dictionaries.")
        self.json_data = json_data
        self.content_type = content_type
        self.file_extensions = file_extensions if file_extensions else ["json"]
        self.name = name

    def to_proto(self) -> StepOutputBatchPbo | list[FieldValueMapPbo]:
        return StepOutputBatchPbo(
            item_container=StepItemContainerPbo(
                content_type=ContentTypePbo(name=self.content_type, extensions=self.file_extensions),
                container_name=self.name,
                json_container=StepJsonContainerPbo(items=[json.dumps(x) for x in self.json_data])
            )
        )


class TextResult(SapioAgentResult):
    """
    A class representing text results from a Sapio agent.
    """
    text_data: list[str]
    content_type: str
    file_extensions: list[str]
    name: str

    def __init__(self, text_data: list[str], content_type: str = "text", file_extensions: list[str] = None,
                 name: str | None = None):
        """
        :param text_data: The text data as a list of strings.
        :param content_type: The content type of the data.
        :param file_extensions: A list of file extensions that this binary data can be saved as.
        :param name: An optional identifying name for this result that will be accessible to the next agent.
        """
        self.text_data = text_data
        self.content_type = content_type
        self.file_extensions = file_extensions if file_extensions else ["txt"]
        self.name = name

    def to_proto(self) -> StepOutputBatchPbo | list[FieldValueMapPbo]:
        return StepOutputBatchPbo(
            item_container=StepItemContainerPbo(
                content_type=ContentTypePbo(name=self.content_type, extensions=self.file_extensions),
                container_name=self.name,
                text_container=StepTextContainerPbo(items=self.text_data)
            )
        )


# TODO: Get rid of this once all the agents are using the new function.
def _agent_name(ab: type[AgentBase] | AgentBase) -> str:
    metadata: AgentMetaData = ab.agent_meta_data()
    if not metadata:
        return ab.name()
    return metadata.name


class AgentServiceBase(AgentServiceServicer, ABC):
    """
    A base class for implementing an agent service. Subclasses should implement the register_agents method to register
    their agents with the service.
    """
    debug_mode: bool = False

    def GetAgentDetails(self, request: AgentDetailsPbo, context: ServicerContext) -> AgentDetailsResponsePbo:
        try:
            # Get the agent details from the registered agents.
            details: list[AgentDetailsPbo] = []
            for agent in self.register_agents():
                details.append(agent().to_pbo())
            if not details:
                raise Exception("No agents registered with this service.")
            return AgentDetailsResponsePbo(agent_framework_version=self.server_version(), agent_details=details)
        except Exception as e:
            # Woe to you if you somehow cause an exception to be raised when just initializing your agents.
            # There's no way to log this.
            print(f"CRITICAL ERROR: {e}")
            print(traceback.format_exc())
            return AgentDetailsResponsePbo()

    def ProcessData(self, request: ProcessStepRequestPbo, context: ServicerContext) -> ProcessStepResponsePbo:
        try:
            # Convert the SapioConnectionInfo proto object to a SapioUser object.
            user = self._create_user(request.sapio_user)
            # Get the agent results from the registered agent matching the request.
            success, msg, results, logs = self.run(user, request, context)
            # Convert the results to protobuf objects.
            output_data: list[StepOutputBatchPbo] = []
            new_records: list[FieldValueMapPbo] = []
            for result in results:
                data: StepOutputBatchPbo | list[FieldValueMapPbo] = result.to_proto()
                if isinstance(data, StepOutputBatchPbo):
                    output_data.append(data)
                else:
                    new_records.extend(data)
            # Return a ProcessStepResponse proto object containing the results to the caller.
            status = ProcessStepResponseStatusPbo.SUCCESS if success else ProcessStepResponseStatusPbo.FAILURE
            return ProcessStepResponsePbo(status=status, status_message=msg, output=output_data, log=logs,
                                          new_records=new_records)
        except Exception as e:
            # This try/except should never be needed, as the agent should handle its own exceptions, but better safe
            # than sorry.
            print(f"CRITICAL ERROR: {e}")
            print(traceback.format_exc())
            return ProcessStepResponsePbo(status=ProcessStepResponseStatusPbo.FAILURE,
                                          status_message=f"CRITICAL ERROR: {e}",
                                          log=[traceback.format_exc()])

    @staticmethod
    def _create_user(info: SapioConnectionInfoPbo, timeout_seconds: int = 60) -> SapioUser:
        """
        Create a SapioUser object from the given SapioConnectionInfo proto object.

        :param info: The SapioConnectionInfo proto object.
        :param timeout_seconds: The request timeout for calls made from this user object.
        """
        user = SapioUser(info.webservice_url.rstrip("/"), True, timeout_seconds, guid=info.app_guid)
        match info.secret_type:
            case SapioUserSecretTypePbo.SESSION_TOKEN:
                user.api_token = info.secret
            case SapioUserSecretTypePbo.PASSWORD:
                secret: str = info.secret
                if secret.startswith("Basic "):
                    secret = secret[6:]
                credentials: list[str] = base64.b64decode(secret).decode().split(":", 1)
                user.username = credentials[0]
                user.password = credentials[1]
            case _:
                raise Exception(f"Unexpected secret type: {info.secret_type}")
        return user

    @staticmethod
    def server_version() -> int:
        """
        :return: The version of this set of .
        """
        return 1

    @abstractmethod
    def register_agents(self) -> list[type[AgentBase]]:
        """
        Register agent types with this service. Provided agents should implement the AgentBase class.

        :return: A list of agents to register to this service.
        """
        pass

    def run(self, user: SapioUser, request: ProcessStepRequestPbo, context: ServicerContext) \
            -> tuple[bool, str, list[SapioAgentResult], list[str]]:
        """
        Execute an agent from this service.

        :param user: A user object that can be used to initialize manager classes using DataMgmtServer to query the
            system.
        :param request: The request object containing the input data.
        :param context: The gRPC context.
        :return: Whether or not the agent succeeded, the status message, the results of the agent, and any logs
            generated by the agent.
        """
        # Locate the agent named in the request.
        agent_name: str = request.agent_name
        registered_agents: dict[str, type[AgentBase]] = {_agent_name(a): a for a in self.register_agents()}
        if agent_name not in registered_agents:
            # If the agent is not found, list all of the registered agents for this service so that the LLM can correct
            # the agent it is requesting.
            all_agent_names: str = "\n".join(registered_agents.keys())
            msg: str = (f"Agent \"{agent_name}\" not found in the registered agents for this service. The registered "
                        f"agents for this service are: \n{all_agent_names}")
            return False, msg, [], []

        # Instantiate the agent class.
        agent: AgentBase = registered_agents[agent_name]()
        # Setup the agent with details from the request.
        agent.setup(user, request, context, self.debug_mode)
        try:
            success: bool = True
            msg: str = ""
            results: list[SapioAgentResult] = []

            # Validate that the provided inputs match the agent's expected inputs.
            errors: list[str] | None = self.validate_input(agent, request)
            if errors:
                msg = f"Agent input validation error(s):\n\t" + "\n\t".join(errors)
                success = False

            # If this is a dry run, then provide the fixed dry run output, even if there were errors with the input.
            # Otherwise, if the inputs were successfully validated, then the agent is executed normally.
            if request.dry_run:
                results = agent.dry_run_output()
                msg = f"{agent_name} dry run successfully completed."
            elif success:
                results = agent.run(user)
                # Verify that the run results match what is expected of this agent.
                # Otherwise, update the status message to reflect the successful execution of the agent.
                errors: list[str] | None = self.validate_output(agent, results)
                if errors:
                    # Wipe the results list so that malformed results aren't returned
                    # to the server and mark the run as a failure.
                    msg = f"Agent output validation error(s):\n\t" + "\n\t".join(errors)
                    results = []
                    success = False
                else:
                    msg = f"{agent_name} successfully completed."
            return success, msg, results, agent.logs
        except Exception as e:
            agent.log_exception("Exception occurred during agent execution.", e)
            return False, str(e), [], agent.logs
        finally:
            # Clean up any temporary files created by the agent. If in debug mode, then log the files instead
            # so that they can be manually inspected.
            if self.debug_mode:
                print("Temporary files/directories created during agent execution:")
                for directory in agent.temp_data.directories:
                    print(f"\tDirectory: {directory}")
                for file in agent.temp_data.files:
                    print(f"\tFile: {file}")
            else:
                agent.temp_data.cleanup()

    @staticmethod
    def validate_input(agent: AgentBase, request: ProcessStepRequestPbo) -> list[str] | None:
        """
        Verify that the input from the server matches the expected input according to the agent's input config
        definitions.

        :param agent: The agent to verify input against.
        :param request: The request from the server.
        :return: A list of errors with the input, if any.
        """
        if len(request.input) != len(agent.input_configs):
            return [f"Expected {len(agent.input_configs)} inputs for this agent, but got {len(request.input)} instead."]
        return agent.validate_input()

    @staticmethod
    def validate_output(agent: AgentBase, results: list[SapioAgentResult]) -> list[str] | None:
        """
        Verify that the output from an agent run matches the expected output according to the agent's output config
        definitions.

        :param agent: The agent to verify output for.
        :param results: The results of the agent run.
        :return: A list of errors with the output, if any.
        """
        # Validate the output from the agent. Were we actually given a list of results?
        if not isinstance(results, list):
            return [f"Expected a list for results, but got {type(results)} instead."]
        bad_results: list[Any] = [x for x in results if not isinstance(x, SapioAgentResult)]
        if bad_results:
            return [f"The list of results should only contain SapioAgentResult objects. "
                    f"Got {[type(x) for x in bad_results]} object(s) instead."]

        # Look out for missing or out-of-order outputs.
        num_expected_outputs: int = len(agent.output_container_types)
        expects_field_maps: bool = agent.output_data_type() is not None or agent.data_type_name() is not None
        if expects_field_maps:
            num_expected_outputs += 1
        if len(results) != num_expected_outputs:
            expected_outputs_str: str = ", ".join(x.value for x in agent.output_container_types)
            if expects_field_maps:
                expected_outputs_str += ", field maps"
            return [f"Expected {num_expected_outputs} outputs for this agent ({expected_outputs_str}), "
                    f"but got {len(results)} instead."]

        errors: list[str] = []
        output_index: int = 0
        field_map_result: FieldMapResult | None = None
        for output in results:
            # FieldMapResult can be given at any point. Everything else needs to be given in the proper order.
            if isinstance(output, FieldMapResult):
                field_map_result = output
                continue
            match agent.output_container_types[output_index]:
                case ContainerType.BINARY:
                    if not isinstance(output, BinaryResult):
                        errors.append(f"Mismatched output type at index {output_index}: expected "
                                      f"BinaryResult but got {type(output)}.")
                case ContainerType.CSV:
                    if not isinstance(output, CsvResult):
                        errors.append(f"Mismatched output type at index {output_index}: expected "
                                        f"CsvResult but got {type(output)}.")
                case ContainerType.JSON:
                    if not isinstance(output, JsonResult):
                        errors.append(f"Mismatched output type at index {output_index}: expected "
                                        f"JsonResult but got {type(output)}.")
                case ContainerType.TEXT:
                    if not isinstance(output, TextResult):
                        errors.append(f"Mismatched output type at index {output_index}: expected "
                                        f"TextResult but got {type(output)}.")
            output_index += 1

        # Validate that the field maps match what is expected.
        if expects_field_maps and not field_map_result:
            errors.append(f"Expected FieldMapResult output for agent, but received none.")
        elif expects_field_maps and agent.output_data_type():
            def value_field(fd: VeloxFieldDefPbo) -> bool:
                valueless_types: list[FieldTypePbo] = [
                    FieldTypePbo.ACTION, FieldTypePbo.PARENTLINK, FieldTypePbo.IDENTIFIER, FieldTypePbo.LINK,
                    FieldTypePbo.MULTIPARENTLINK, FieldTypePbo.CHILDLINK, FieldTypePbo.AUTO_ACCESSION
                ]
                return fd.data_field_type not in valueless_types

            field_defs: dict[str, VeloxFieldDefPbo] = {x.data_field_name: x for x in
                                                       agent.output_data_type().field_defs if value_field(x)}
            expected_fields: set[str] = set(field_defs)

            for i, field_map in enumerate(field_map_result.field_maps):
                output_fields: set[str] = set(field_map.keys())
                missing: set[str] = expected_fields.difference(output_fields)
                if missing:
                    errors.append(f"Entry {i} is missing field names specified by the AgentDataType: {missing}")
                else:
                    for field in expected_fields:
                        value: Any = field_map[field]
                        field_def: VeloxFieldDefPbo = field_defs[field]
                        if value is None:
                            if field_def.required:
                                errors.append(f"Entry {i} is missing required value for field {field}.")
                            continue
                        match field_def.data_field_type:
                            case FieldTypePbo.BOOLEAN:
                                if not isinstance(value, bool):
                                    errors.append(f"Entry {i} field {field} expects a boolean but "
                                                  f"received {type(value)}.")
                            case FieldTypePbo.SHORT | FieldTypePbo.INTEGER | FieldTypePbo.LONG \
                                 | FieldTypePbo.ENUM | FieldTypePbo.DATE | FieldTypePbo.SIDE_LINK:
                                if not isinstance(value, int):
                                    errors.append(f"Entry {i} field {field} expects an integer but "
                                                  f"received {type(value)}.")
                            case FieldTypePbo.DOUBLE:
                                if not isinstance(value, (int, float)):
                                    errors.append(f"Entry {i} field {field} expects a float or integer but "
                                                  f"received {type(value)}.")
                            case FieldTypePbo.DATE_RANGE:
                                if not isinstance(value, str):
                                    errors.append(f"Entry {i} field {field} expects a string but "
                                                  f"received {type(value)}.")
                                else:
                                    try:
                                        DateRange.from_str(value)
                                    except:
                                        errors.append(f"Entry {i} field {field} expects a date range "
                                                      f"formatted string (<start timestamp>/<end timestamp>) "
                                                      f"but received \"{value}\".")
                            case FieldTypePbo.STRING | FieldTypePbo.SELECTION | FieldTypePbo.PICKLIST \
                                 | FieldTypePbo.ACTION_STRING:
                                if not isinstance(value, str):
                                    errors.append(f"Entry {i} field {field} expects a string but "
                                                  f"received {type(value)}.")
                            case FieldTypePbo.FILE_BLOB:
                                # TODO: What does a file blob store?
                                pass

        # Run the agent's output validation, but only if no other errors were encountered.
        if not errors:
            errors = agent.validate_output()
        return errors


class AgentMetaData:
    """
    A class that allows agents to self-describe their metadata.
    """
    name: str
    description: str
    category: str
    citations: dict[str, str]
    sub_category: str | None
    icon: bytes | None
    license_flag: str | None

    def __init__(self, name: str, description: str, category: str, citations: dict[str, str],
                 sub_category: str | None = None, icon: bytes | None = None, license_flag: str | None = None):
        """
        :param name: The display name of the agent. This should be unique across all agents in the service.
        :param description: The description of the agent.
        :param category: The category of the agent. This is used to group similar agents in the pipeline manager.
        :param citations: Any citations or references for this agent, as a dictionary of citation name to URL.
        :param sub_category: The sub-category of the agent. Agents with the same category and sub-category will appear
            as one item in the list of agents in the pipeline manager. Clicking on this item will then expand to allow
            the selection of which agent in the sub-category should be used. This is used to group multiple agents
            from the same service into one item as not to clutter the list of agents, as some services may have a large
            number of individual agents created for them.
        :param icon: The icon to use for the agent. This will appear in the list of agents and on individual steps
            in the pipeline manager.
        :param license_flag: The license flag for this agent. The system must have this license in order to use this
            agent. If None, the agent is not license locked.
        """
        self.name = name
        self.description = description
        self.category = category
        self.sub_category = sub_category
        self.citations = citations
        self.icon = icon
        self.license_flag = license_flag


class AgentDataType:
    """
    A class that allows agents to self-describe the fields that will be present in the FieldMapResults of the agent.
    """
    data_type_name: str
    display_name: str
    field_defs: list[VeloxFieldDefPbo]
    icon: bytes | None

    def __init__(self, data_type_name: str, display_name: str,
                 field_defs: list[AbstractVeloxFieldDefinition | VeloxFieldDefPbo],
                 icon: bytes | None = None):
        """
        :param data_type_name: The name of the data type to use.
        :param display_name: The display name of the data type to use.
        :param field_defs: The fields to use for this data type.
        :param icon: The icon to use for this data type.
        """
        self.data_type_name = data_type_name
        self.display_name = display_name
        self.icon = icon
        self.field_defs = []
        for field_def in field_defs:
            if isinstance(field_def, AbstractVeloxFieldDefinition):
                self.field_defs.append(ProtobufUtils.field_def_to_pbo(field_def))
            else:
                self.field_defs.append(field_def)


class AgentBase(ABC):
    """
    A base class for implementing an agent.
    """
    input_configs: list[AgentInputDetailsPbo]
    input_container_types: list[ContainerType]
    output_configs: list[AgentOutputDetailsPbo]
    output_container_types: list[ContainerType]
    config_fields: list[VeloxFieldDefPbo]

    logs: list[str]
    logger: Logger
    _verbose_logging: bool | None = None

    _temp_data: TempFileHandler | None = None

    _user: SapioUser | None = None
    _request: ProcessStepRequestPbo | None = None
    _context: ServicerContext | None = None
    _debug_mode: bool | None = None
    
    __is_setup: bool

    @property
    def verbose_logging(self) -> bool:
        if not self.__is_setup:
            raise Exception("Agent must be set up to respond to a request before accessing this property.")
        return self._verbose_logging

    @property
    def temp_data(self) -> TempFileHandler:
        if not self.__is_setup:
            raise Exception("Agent must be set up to respond to a request before accessing this property.")
        return self._temp_data

    @property
    def user(self) -> SapioUser:
        if not self.__is_setup:
            raise Exception("Agent must be set up to respond to a request before accessing this property.")
        return self._user

    @property
    def request(self) -> ProcessStepRequestPbo:
        if not self.__is_setup:
            raise Exception("Agent must be set up to respond to a request before accessing this property.")
        return self._request

    @property
    def context(self) -> ServicerContext:
        if not self.__is_setup:
            raise Exception("Agent must be set up to respond to a request before accessing this property.")
        return self._context

    @property
    def debug_mode(self) -> bool:
        if not self.__is_setup:
            raise Exception("Agent must be set up to respond to a request before accessing this property.")
        return self._debug_mode

    @classmethod
    # @abstractmethod
    def identifier(cls):
        """
        :return: The unique identifier of the agent. This is used by the system to determine which agent should be
            updated if an agent is re-imported. This should not be changed after the first time that an agent is
            imported, otherwise a duplicate agent will be created.
        """
        pass

    @staticmethod
    # @abstractmethod
    def agent_meta_data() -> AgentMetaData:
        """
        :return: The metadata information of this agent.
        """
        pass

    @staticmethod
    # @abstractmethod
    def output_data_type() -> AgentDataType | None:
        """
        :return: The information of the output data type of this agent, if applicable. This will be the initial data
            type for this agent when it is first imported into the system. Note that further customization can be made
            to the data type that cause it to differ from this definition.
        """
        pass

    @staticmethod
    def name() -> str:
        """
        DEPRECATED: Use agent_meta_data instead.

        :return: The display name of the agent. This should be unique across all agents in the service.
        """
        pass

    @staticmethod
    def category() -> str | tuple[str, str] | None:
        """
        DEPRECATED: Use agent_meta_data instead.

        :return: The category of the agent. This is used to group similar agents together in the plan manager.
            If a 2-tuple of strings is provided, then the first value is the category and the second is the subcategory.
        """
        pass

    @staticmethod
    def description() -> str:
        """
        DEPRECATED: Use agent_meta_data instead.

        :return: A description of the agent.
        """
        pass

    @staticmethod
    def citations() -> dict[str, str]:
        """
        DEPRECATED: Use agent_meta_data instead.

        :return: Any citations or references for this agent, as a dictionary of citation name to URL.
        """
        pass

    @staticmethod
    def data_type_name() -> str | None:
        """
        DEPRECATED: Use output_data_type instead.

        :return: The name of the output data type of this agent, if applicable. When this agent returns
            FieldMapResult objects in its run method, this name will be used to set the data type of the output data.
        """
        return None


    @staticmethod
    def license_flag() -> str | None:
        """
        DEPRECATED: Use agent_meta_data instead.

        :return: The license flag for this agent. The system must have this license in order to use this agent.
            If None, the agent is not license locked.
        """
        return None

    def __init__(self):
        self.__is_setup = False
        self.input_configs = []
        self.input_container_types = []
        self.output_configs = []
        self.output_container_types = []
        self.config_fields = []
        self.logs = []
        self.logger = logging.getLogger(f"AgentBase.{_agent_name(self)}")
        ensure_logger_initialized(self.logger)

    def to_pbo(self) -> AgentDetailsPbo:
        """
        :return: The AgentDetailsPbo proto object representing this agent.
        """
        metadata: AgentMetaData = self.agent_meta_data()
        # TODO: This is only temporarily here until we update all the tools to use the new function.
        if not metadata:
            categories: str | tuple[str, str] | None = self.category()
            category: str = "Uncategorized"
            sub_category: str | None = None
            if isinstance(categories, str):
                category = categories
            elif isinstance(categories, tuple) and len(categories) == 2:
                category = categories[0]
                sub_category = categories[1]
            elif categories is not None:
                raise TypeError("The return value of the \"category\" function must be either None, a string, "
                                "or a 2-tuple of strings.")

            metadata = AgentMetaData(
                name=self.name(),
                description=self.description(),
                category=category,
                sub_category=sub_category,
                citations=self.citations(),
                license_flag=self.license_flag(),
            )

        data_type: AgentDataType = self.output_data_type()
        # TODO: This is only temporarily here until we update all the tools to use the new function.
        if not data_type:
            # noinspection PyTypeChecker
            data_type = AgentDataType(
                data_type_name=self.data_type_name(),
                display_name=None,
                field_defs=[],
            )
            # noinspection PyTypeChecker
            data_type.field_defs = None

        return AgentDetailsPbo(
            import_id=self.identifier(),
            name=metadata.name,
            description=metadata.description,
            category=metadata.category,
            sub_category=metadata.sub_category,
            icon=metadata.icon,
            citation=[AgentCitationPbo(title=x, url=y) for x, y in metadata.citations.items()],
            license_info=metadata.license_flag,
            config_fields=self.config_fields,
            input_configs=self.input_configs,
            output_configs=self.output_configs,
            output_data_type_name=data_type.data_type_name if data_type else None,
            output_data_type_display_name=data_type.display_name if data_type else None,
            output_type_fields=data_type.field_defs if data_type else None,
            output_data_type_icon=data_type.icon if data_type else None,
        )

    def setup(self, user: SapioUser, request: ProcessStepRequestPbo, context: ServicerContext, debug_mode: bool) -> None:
        """
        Setup the agent with the user, request, and context. This method can be overridden by subclasses to perform
        additional setup.

        :param user: A user object that can be used to initialize manager classes using DataMgmtServer to query the
            system.
        :param request: The request object containing the input data.
        :param context: The gRPC context.
        :param debug_mode: If true, the agent should run in debug mode, providing additional logging and not cleaning
            up temporary files.
        """
        self.__is_setup = True
        self._user = user
        self._request = request
        self._context = context
        self._verbose_logging = request.verbose_logging
        self._debug_mode = debug_mode
        self._temp_data = TempFileHandler()

    @staticmethod
    def _parse_jsonl(example: str) -> list[dict[str, Any]]:
        """
        Given a testing example for a JSON output, parse the JSONL into plain JSON.
        """
        # Use a JSON decoder to find all valid JSON strings within the testing example.
        decoder = json.JSONDecoder()
        idx: int = 0
        json_strings: list[str] = []
        while idx < len(example):
            try:
                # Find the next valid JSON object in the example.
                obj, end = decoder.raw_decode(example, idx)
                # Extract the exact substring corresponding to this JSON object
                json_strings.append(example[idx:end].strip())
                idx = end
            except json.JSONDecodeError:
                # Skip invalid character and keep searching
                idx += 1
        # If no valid JSON was encountered, then a bad example was given.
        if not json_strings:
            raise Exception("No valid JSON encountered in testing example.")

        # At this point, each line is its own top-level JSON object. Verify that every line is a dictionary.
        # For lines that are dictionaries, parse them as JSON.
        data: list[dict[str, Any]] = []
        for line in json_strings:
            line = line.strip()
            if not line.startswith("{") and not line.endswith("}"):
                raise Exception("Testing examples must be JSON dictionaries in the JSONL format. "
                                "(The top-level object may not be a list.)")
            data.append(json.loads(line))
        return data

    def add_input(self, container_type: ContainerType, content_type: str, display_name: str, description: str,
                  structure_example: str | bytes | None = None, validation: str | None = None,
                  input_count: tuple[int, int] | None = None, is_paged: bool = False,
                  page_size: tuple[int, int] | None = None, max_request_bytes: int | None = None) -> None:
        """
        Add an input configuration to the agent. This determines how many inputs this agent will accept in the plan
        manager, as well as what those inputs are. The IO number of the input will be set to the current number of
        inputs. That is, the first time this is called, the IO number will be 0, the second time it is called, the IO
        number will be 1, and so on.

        :param container_type: The container type of the input.
        :param content_type: The content type of the input.
        :param display_name: The display name of the input.
        :param description: The description of the input.
        :param structure_example: An optional example of the structure of the input, such as how the structure of a
            JSON output may look. This does not need to be an entirely valid example, and should often be truncated for
            brevity. This must be provided for any container type other than BINARY.
        :param validation: An optional validation string for the input.
        :param input_count: A tuple of the minimum and maximum number of inputs allowed for this agent.
        :param is_paged: If true, this input will be paged. If false, this input will not be paged.
        :param page_size: A tuple of the minimum and maximum page size for this agent. The input must be paged in order
            for this to have an effect.
        :param max_request_bytes: The maximum request size in bytes for this agent.
        """
        if container_type != ContainerType.BINARY and structure_example is None:
            raise ValueError("structure_example must be provided for inputs with a container_type other than BINARY.")
        structure: ExampleContainerPbo | None = None
        if isinstance(structure_example, str):
            structure = ExampleContainerPbo(text_example=structure_example)
        elif isinstance(structure_example, bytes):
            structure = ExampleContainerPbo(binary_example=structure_example)
        self.input_configs.append(AgentInputDetailsPbo(
            base_config=AgentIoConfigBasePbo(
                io_number=len(self.input_configs),
                content_type=content_type,
                display_name=display_name,
                description=description,
                structure_example=structure,
                # The testing example on the input is never used, hence why it can't be set by this function.
                # The testing example is only used during dry runs, in which the testing_example of the output
                # of the previous step is what gets passed to the next step's input validation.
                testing_example=None
            ),
            validation=validation,
            min_input_count=input_count[0] if input_count else None,
            max_input_count=input_count[1] if input_count else None,
            paged=is_paged,
            min_page_size=page_size[0] if page_size else None,
            max_page_size=page_size[1] if page_size else None,
            max_request_bytes=max_request_bytes,
        ))
        self.input_container_types.append(container_type)

    def add_output(self, container_type: ContainerType, content_type: str, display_name: str, description: str,
                   testing_example: str | bytes, structure_example: str | bytes | None = None) -> None:
        """
        Add an output configuration to the agent. This determines how many inputs this agent will accept in the plan
        manager, as well as what those inputs are. The IO number of the output will be set to the current number of
        outputs. That is, the first time this is called, the IO number will be 0, the second time it is called, the IO
        number will be 1, and so on.

        :param container_type: The container type of the output.
        :param content_type: The content type of the output.
        :param display_name: The display name of the output.
        :param description: The description of the output.
        :param testing_example: An example of the input to be used when testing this agent in the system. This must be
            an entirely valid example of what an output of this agent could look like so that it can be properly used
            to run tests with. The provided example may be a string, such as for representing JSON or CSV outputs,
            or bytes, such as for representing binary outputs like images or files.
        :param structure_example: An optional example of the structure of the input, such as how the structure of a
            JSON output may look. This does not need to be an entirely valid example, and should often be truncated for
            brevity. This must be provided for any container type other than BINARY.
        """
        if not testing_example:
            raise ValueError("A testing_example must be provided for the output.")
        testing: ExampleContainerPbo | None = None
        if isinstance(testing_example, str):
            testing = ExampleContainerPbo(text_example=testing_example)
            # When a JSON example is provided, it MUST be in the JSONL format with top-level objects being dictionaries.
            # Attempt to parse it as JSONL. An exception will be thrown if this fails.
            if container_type == ContainerType.JSON:
                self._parse_jsonl(testing_example)
        elif isinstance(testing_example, bytes):
            testing = ExampleContainerPbo(binary_example=testing_example)

        if container_type != ContainerType.BINARY and structure_example is None:
            raise ValueError("structure_example must be provided for inputs with a container_type other than BINARY.")
        structure: ExampleContainerPbo | None = None
        if isinstance(structure_example, str):
            structure = ExampleContainerPbo(text_example=structure_example)
        elif isinstance(structure_example, bytes):
            structure = ExampleContainerPbo(binary_example=structure_example)

        self.output_configs.append(AgentOutputDetailsPbo(
            base_config=AgentIoConfigBasePbo(
                io_number=len(self.output_configs),
                content_type=content_type,
                display_name=display_name,
                description=description,
                structure_example=structure,
                testing_example=testing
            )))
        self.output_container_types.append(container_type)

    def add_config_field(self, field: VeloxFieldDefPbo) -> None:
        """
        Add a configuration field to the agent. This field will be used to configure the agent in the plan manager.

        :param field: The configuration field details.
        """
        self.config_fields.append(field)

    def add_config_field_def(self, field: AbstractVeloxFieldDefinition) -> None:
        """
        Add a configuration field to the agent. This field will be used to configure the agent in the plan manager.

        :param field: The configuration field details.
        """
        self.config_fields.append(ProtobufUtils.field_def_to_pbo(field))

    def add_boolean_config_field(self, field_name: str, display_name: str, description: str,
                                 default_value: bool | None = None, optional: bool = False,
                                 dependencies: dict[bool, list[str]] | None = None,
                                 is_hide_disabled_fields: bool = False) -> None:
        """
        Add a boolean configuration field to the agent. This field will be used to configure the agent in the plan
        manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param default_value: The default value of the field.
        :param optional: If true, this field is optional. If false, this field is required.
        :param dependencies: A dictionary of field dependencies. The value of the dictionary is a possible value of
            this field, and the key is a list of field names for other config fields of this agent that will be
            disabled if the config field matches the corresponding value.
        :param is_hide_disabled_fields: If true, fields disabled by a field dependency will be hidden. If false, the
            dependent fields will be visible, but uneditable.
        """
        dependent_fields: list[BooleanDependentFieldEntryPbo] | None = None
        if dependencies:
            dependent_fields = []
            for key, values in dependencies.items():
                dependent_fields.append(BooleanDependentFieldEntryPbo(key=key, dependent_field_names=values))
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.BOOLEAN,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            boolean_properties=BooleanPropertiesPbo(
                default_value=default_value,
                dependent_fields=dependent_fields,
                is_hide_disabled_fields=is_hide_disabled_fields
            )
        ))

    def add_double_config_field(self, field_name: str, display_name: str, description: str,
                                default_value: float | None = None, min_value: float = -10.**120,
                                max_value: float = 10.**120, precision: int = 2, optional: bool = False) -> None:
        """
        Add a double configuration field to the agent. This field will be used to configure the agent in the plan
        manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param default_value: The default value of the field.
        :param min_value: The minimum value of the field.
        :param max_value: The maximum value of the field.
        :param precision: The precision of the field.
        :param optional: If true, this field is optional. If false, this field is required.
        """
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.DOUBLE,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            double_properties=DoublePropertiesPbo(
                default_value=default_value,
                min_value=min_value,
                max_value=max_value,
                precision=precision
            )
        ))

    def add_integer_config_field(self, field_name: str, display_name: str, description: str,
                                 default_value: int | None = None, min_value: int = -2**31, max_value: int = 2**31-1,
                                 optional: bool = False) -> None:
        """
        Add an integer configuration field to the agent. This field will be used to configure the agent in the plan
        manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param default_value: The default value of the field.
        :param min_value: The minimum value of the field.
        :param max_value: The maximum value of the field.
        :param optional: If true, this field is optional. If false, this field is required.
        """
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.INTEGER,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            integer_properties=IntegerPropertiesPbo(
                default_value=default_value,
                min_value=min_value,
                max_value=max_value
            )
        ))

    def add_string_config_field(self, field_name: str, display_name: str, description: str,
                                default_value: str | None = None, max_length: int = 1000, optional: bool = False,
                                validation_regex: str | None = None, error_msg: str | None = None) -> None:
        """
        Add a string configuration field to the agent. This field will be used to configure the agent in the plan
        manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param default_value: The default value of the field.
        :param max_length: The maximum length of the field.
        :param optional: If true, this field is optional. If false, this field is required.
        :param validation_regex: An optional regex that the field value must match.
        :param error_msg: An optional error message to display if the field value does not match the regex.
        """
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.STRING,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            string_properties=StringPropertiesPbo(
                default_value=default_value,
                max_length=max_length,
                field_validator=FieldValidatorPbo(validation_regex=validation_regex, error_message=error_msg) if validation_regex else None
            )
        ))

    def add_list_config_field(self, field_name: str, display_name: str, description: str,
                              default_value: str | None = None, allowed_values: list[str] | None = None,
                              direct_edit: bool = False, optional: bool = False,
                              validation_regex: str | None = None, error_msg: str | None = None,
                              dependencies: dict[str, list[str]] | None = None,
                              is_hide_disabled_fields: bool = False) -> None:
        """
        Add a list configuration field to the agent. This field will be used to configure the agent in the plan
        manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param default_value: The default value of the field.
        :param allowed_values: The list of allowed values for the field.
        :param direct_edit: If true, the user can enter a value that is not in the list of allowed values. If false,
            the user can only select from the list of allowed values.
        :param optional: If true, this field is optional. If false, this field is required.
        :param validation_regex: An optional regex that the field value must match.
        :param error_msg: An optional error message to display if the field value does not match the regex.
        :param dependencies: A dictionary of field values to the fields that should be disabled while this field
            is set to the key value.
        :param dependencies: A dictionary of field dependencies. The value of the dictionary is a possible value of
            this field, and the key is a list of field names for other config fields of this agent that will be
            disabled if the config field matches the corresponding value.
        :param is_hide_disabled_fields: If true, fields disabled by a field dependency will be hidden. If false, the
            dependent fields will be visible, but uneditable.
        """
        dependent_fields: list[SelectionDependentFieldEntryPbo] | None = None
        if dependencies:
            dependent_fields = []
            for key, values in dependencies.items():
                dependent_fields.append(SelectionDependentFieldEntryPbo(key=key, dependent_field_names=values))
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.SELECTION,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            selection_properties=SelectionPropertiesPbo(
                default_value=default_value,
                static_list_values=allowed_values,
                direct_edit=direct_edit,
                field_validator=FieldValidatorPbo(validation_regex=validation_regex, error_message=error_msg) if validation_regex else None,
                dependent_fields=dependent_fields,
                is_hide_disabled_fields=is_hide_disabled_fields
            )
        ))

    def add_multi_list_config_field(self, field_name: str, display_name: str, description: str,
                                    default_value: list[str] | None = None, allowed_values: list[str] | None = None,
                                    direct_edit: bool = False, optional: bool = False,
                                    validation_regex: str | None = None, error_msg: str | None = None,
                                    dependencies: dict[str, list[str]] | None = None,
                                    is_hide_disabled_fields: bool = False) -> None:
        """
        Add a multi-select list configuration field to the agent. This field will be used to configure the agent in the
        plan manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param default_value: The default value of the field.
        :param allowed_values: The list of allowed values for the field.
        :param direct_edit: If true, the user can enter a value that is not in the list of allowed values. If false,
            the user can only select from the list of allowed values.
        :param optional: If true, this field is optional. If false, this field is required.
        :param validation_regex: An optional regex that the field value must match.
        :param error_msg: An optional error message to display if the field value does not match the regex.
        :param dependencies: A dictionary of field dependencies. The value of the dictionary is a possible value of
            this field, and the key is a list of field names for other config fields of this agent that will be
            disabled if the config field matches the corresponding value.
        :param is_hide_disabled_fields: If true, fields disabled by a field dependency will be hidden. If false, the
            dependent fields will be visible, but uneditable.
        """
        dependent_fields: list[SelectionDependentFieldEntryPbo] | None = None
        if dependencies:
            dependent_fields = []
            for key, values in dependencies.items():
                dependent_fields.append(SelectionDependentFieldEntryPbo(key=key, dependent_field_names=values))
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.SELECTION,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            selection_properties=SelectionPropertiesPbo(
                default_value=",".join(default_value) if default_value else None,
                static_list_values=allowed_values,
                multi_select=True,
                direct_edit=direct_edit,
                field_validator=FieldValidatorPbo(validation_regex=validation_regex, error_message=error_msg) if validation_regex else None,
                dependent_fields=dependent_fields,
                is_hide_disabled_fields=is_hide_disabled_fields
            )
        ))

    def add_date_config_field(self, field_name: str, display_name: str, description: str, optional: bool = False,
                              date_time_format: str = "MMM dd, yyyy", default_to_today: bool = False,
                              is_static_date: bool = False) -> None:
        """
        Add a date configuration field to the agent. This field will be used to configure the agent in the plan
        manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param date_time_format: The format that this date field should appear in. The date format is Java-style.
            See https://docs.oracle.com/en/java/javase/18/docs/api/java.base/java/text/SimpleDateFormat.html for more
            details.
        :param default_to_today: If true, the default value of the field will be set to today's date. If false, the
            default value will be None.
        :param is_static_date: If true, the user will input the date as UTC. If false, the user will input the date
            as local time.
        :param optional: If true, this field is optional. If false, this field is required.
        """
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.DATE,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            date_properties=DatePropertiesPbo(
                default_value="@Today" if default_to_today else None,
                static_date=is_static_date,
                date_time_format=date_time_format
            )
        ))

    def add_credentials_config_field(self, field_name: str, display_name: str, description: str, optional: bool = False,
                                     category: str | None = None, dependencies: dict[str, list[str]] | None = None,
                                     is_hide_disabled_fields: bool = False) -> None:
        """
        Add a list field that asks the user to choose which credentials to use. This field will be used to
        configure the agent in the plan manager.

        :param field_name: The name of the field.
        :param display_name: The display name of the field.
        :param description: The description of the field.
        :param optional: If true, this field is optional. If false, this field is required.
        :param category: If provided, only credentials in this category will be shown to the user.
        :param dependencies: A dictionary of field dependencies. The value of the dictionary is a possible value of
            this field, and the key is a list of field names for other config fields of this agent that will be
            disabled if the config field matches the corresponding value.
        :param is_hide_disabled_fields: If true, fields disabled by a field dependency will be hidden. If false, the
            dependent fields will be visible, but uneditable.
        """
        dependent_fields: list[SelectionDependentFieldEntryPbo] | None = None
        if dependencies:
            dependent_fields = []
            for key, values in dependencies.items():
                dependent_fields.append(SelectionDependentFieldEntryPbo(key=key, dependent_field_names=values))
        self.config_fields.append(VeloxFieldDefPbo(
            data_field_type=FieldTypePbo.SELECTION,
            data_field_name=field_name,
            display_name=display_name,
            description=description,
            required=not optional,
            editable=True,
            selection_properties=SelectionPropertiesPbo(
                # A credentials field is just a selection field with its list mode set to [ExternalCredentials].
                list_mode=f"[ExternalCredentials]{category.strip() if category else ''}",
                multi_select=False,
                default_value=None,
                direct_edit=False,
                dependent_fields=dependent_fields,
                is_hide_disabled_fields=is_hide_disabled_fields
            )
        ))

    @abstractmethod
    def validate_input(self) -> list[str] | None:
        """
        Validate the request given to this agent. If the request is validly formatted, this method should return None.
        If the request is not valid, this method should return an error message indicating what is wrong with the
        request.

        This method should not perform any actual processing of the request. It should only validate the inputs and
        configurations provided in the request.

        The request inputs can be accessed using the self.get_input_*() methods.
        The request settings can be accessed using the self.get_config_fields() method.
        The request itself can be accessed using self.request.

        :return: A list of the error messages if the request is not valid. If the request is valid, return an empty
            list or None.
        """
        pass

    def validate_output(self: list[SapioAgentResult]) -> list[str] | None:
        """
        Validate the output returned by this agent. This is an optional check that agents are able to run before
        returning their results to the server. This is called after the agent service verifies that the results
        match the output configurations defined by the agent.

        :return: A list of the error messages if the results are not valid. If the results are not valid, return an
            empty list or None.
        """
        pass

    def dry_run_output(self) -> list[SapioAgentResult]:
        """
        Provide fixed results for a dry run of this agent. This method should not perform any actual processing of the
        request. It should only return example outputs that can be used to test the next agent in the plan.

        The default implementation of this method looks at the testing_example field of each output configuration
        and returns a SapioAgentResult object based on the content type of the output.

        :return: A list of SapioAgentResult objects containing example outputs for this agent. Each result in the list
            corresponds to a separate output from the agent.
        """
        results: list[SapioAgentResult] = []
        for output, container_type in zip(self.output_configs, self.output_container_types):
            config: AgentIoConfigBasePbo = output.base_config
            example: ExampleContainerPbo = config.testing_example
            content_type: str = config.content_type
            match container_type:
                case ContainerType.BINARY:
                    example: bytes = example.binary_example
                    results.append(BinaryResult(binary_data=[example], content_type=content_type))
                case ContainerType.CSV:
                    example: str = example.text_example
                    results.append(CsvResult(FileUtil.tokenize_csv(example.encode())[0], content_type=content_type))
                case ContainerType.JSON:
                    example: str = example.text_example
                    results.append(JsonResult(json_data=self._parse_jsonl(example), content_type=content_type))
                case ContainerType.TEXT:
                    example: str = example.text_example
                    results.append(TextResult(text_data=[example], content_type=content_type))
        return results

    @abstractmethod
    def run(self, user: SapioUser) -> list[SapioAgentResult]:
        """
        Execute this agent.

        The request inputs can be accessed using the self.get_input_*() methods.
        The request settings can be accessed using the self.get_config_fields() method.
        The request itself can be accessed using self.request.

        :param user: A user object that can be used to initialize manager classes using DataMgmtServer to query the
            system.
        :return: A list of SapioAgentResult objects containing the response data. Each result in the list corresponds to
            a separate output from the agent. Field map results do not appear as agent output in the plan manager,
            instead appearing as records related to the plan step during the run.
        """
        pass

    def get_credentials(self, name: str | None = None, category: str | None = None) -> ExternalCredentials:
        """
        Get credentials for the given category and host.

        :param name: The host name of the credentials to retrieve.
        :param category: The category of the credentials to retrieve.
        :return: An ExternalCredentials object containing the credentials for the given category and host.
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        # Remove leading/trailing whitespace
        name = name.strip() if name else None
        category = category.strip() if category else None

        matching_creds: list[ExternalCredentialsPbo] = []
        for cred in self.request.external_credential:
            # Do case insensitive comparison
            if name and cred.display_name.lower != name.lower():
                continue
            if category and cred.category.lower() != category.lower():
                continue
            matching_creds.append(cred)
        if len(matching_creds) == 0:
            raise ValueError(f"No credentials found for name '{name}' and category '{category}'.")
        if len(matching_creds) > 1:
            raise ValueError(f"Multiple credentials found for name '{name}' and category '{category}'.")

        return ExternalCredentials.from_pbo(matching_creds[0])

    def get_credentials_from_config(self, value: str) -> ExternalCredentials:
        """
        Get credentials given the value of a credentials config field.

        :param value: The value of the credentials config field.
        :return: An ExternalCredentials object containing the credentials.
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        # Values should be of the format "Name (Identifier)"
        match = re.match(r"^(.*) \((.*)\)$", value)
        if not match:
            raise ValueError(f"Invalid credentials value '{value}'. Expected format 'Name (Identifier)'.")
        identifier: str = match.group(2)
        for cred in self.request.external_credential:
            if cred.id == identifier:
                return ExternalCredentials.from_pbo(cred)
        raise ValueError(f"No credentials found with identifier '{identifier}'.")

    def call_subprocess(self,
                        args: str | bytes | PathLike[str] | PathLike[bytes] | Sequence[str | bytes | PathLike[str] | PathLike[bytes]],
                        cwd: str | bytes | PathLike[str] | PathLike[bytes] | None = None,
                        **kwargs) -> CompletedProcess[str]:
        """
        Call a subprocess with the given arguments, logging the command and any errors that occur.
        This function will raise an exception if the return code of the subprocess is non-zero. The output of the
        subprocess will be captured and returned as part of the CompletedProcess object.

        :param args: The list of arguments to pass to the subprocess.
        :param cwd: The working directory to run the subprocess in. If None, the current working directory is used.
        :param kwargs: Additional keyword arguments to pass to subprocess.run().
        :return: The CompletedProcess object returned by subprocess.run().
        """
        try:
            self.log_info(f"Running subprocess with command: {' '.join(args)}")
            p: CompletedProcess[str] = subprocess.run(args, check=True, capture_output=True, text=True, cwd=cwd,
                                                      **kwargs)
            if p.stdout:
                self.log_info(f"STDOUT: {p.stdout}")
            if p.stderr:
                self.log_info(f"STDERR: {p.stderr}")
            return p
        except subprocess.CalledProcessError as e:
            self.log_error(f"Error running subprocess. Return code: {e.returncode}")
            if e.stdout:
                self.log_error(f"STDOUT: {e.stdout}")
            if e.stderr:
                self.log_error(f"STDERR: {e.stderr}")
            raise

    def log_info(self, message: str) -> None:
        """
        Log an info message for this agent. If verbose logging is enabled, this message will be included in the logs
        returned to the caller. Empty/None inputs will not be logged.
        
        Logging info can be done during initialization, but those logs will not be returned to the caller. Other
        log calls will be returned to the caller, even if done during initialization.

        :param message: The message to log.
        """
        if not message:
            return
        if self.__is_setup and self.verbose_logging:
            self.logs.append(f"INFO: {_agent_name(self)}: {message}")
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """
        Log a warning message for this agent. This message will be included in the logs returned to the caller.
        Empty/None inputs will not be logged.

        :param message: The message to log.
        """
        if not message:
            return
        self.logs.append(f"WARNING: {_agent_name(self)}: {message}")
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        """
        Log an error message for this agent. This message will be included in the logs returned to the caller.
        Empty/None inputs will not be logged.

        :param message: The message to log.
        """
        if not message:
            return
        self.logs.append(f"ERROR: {_agent_name(self)}: {message}")
        self.logger.error(message)

    def log_exception(self, message: str, e: Exception) -> None:
        """
        Log an exception for this agent. This message will be included in the logs returned to the caller.
        Empty/None inputs will not be logged.

        :param message: The message to log.
        :param e: The exception to log.
        """
        if not message and not e:
            return
        self.logs.append(f"EXCEPTION: {_agent_name(self)}: {message} - {e}")
        self.logger.error(f"{message}\n{traceback.format_exc()}")

    def is_input_partial(self, index: int = 0) -> bool:
        """
        Check if the input at the given index is marked as partial.

        :param index: The index of the input to check. Defaults to 0. Used for agents that accept multiple inputs.
        :return: True if the input is marked as partial, False otherwise.
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        return self.request.input[index].is_partial

    def get_input_name(self, index: int = 0) -> str | None:
        """
        Get the name of the input from the request object.

        :param index: The index of the input to parse. Defaults to 0. Used for agents that accept multiple inputs.
        :return: The name of the input from the request object, or None if no name is set.
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        return self.request.input[index].item_container.container_name

    def get_input_content_type(self, index: int = 0) -> ContentTypePbo:
        """
        Get the content type of the input from the request object.

        :param index: The index of the input to parse. Defaults to 0. Used for agents that accept multiple inputs.
        :return: The content type of the input from the request object.
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        return self.request.input[index].item_container.content_type

    def _validate_get_input(self, index: int, get_type: ContainerType) -> None:
        """
        Given an index and the container type being requested from it, validate that the agent is setup to respond
        to a request, that the index is not out of range, and that the input type from the config matches the
        input type being requested. If any errors are encountered, raise an exception.

        :param index: The index of the input.
        :param get_type: The type of the input being requested.
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        total_inputs: int = len(self.request.input)
        if index >= total_inputs:
            raise Exception(f"Index out of range. This agent only has {total_inputs} inputs. Attempted to retrieve "
                            f"input with index {index}.")
        config: ContainerType = self.input_container_types[index]
        if config != get_type:
            raise Exception(f"Input {index} is not a \"{get_type.value}\" input. The container type for this input "
                            f"is \"{config.value}\".")

    def get_input_binary(self, index: int = 0) -> list[bytes]:
        """
        Get the binary data from the request object.

        :param index: The index of the input to parse. Defaults to 0. Used for agents that accept multiple inputs.
        :return: The binary data from the request object.
        """
        self._validate_get_input(index, ContainerType.BINARY)
        container: StepItemContainerPbo = self.request.input[index].item_container
        if not container.HasField("binary_container"):
            return []
        return list(container.binary_container.items)

    def get_input_csv(self, index: int = 0) -> tuple[list[str], list[dict[str, str]]]:
        """
        Parse the CSV data from the request object.

        :param index: The index of the input to parse. Defaults to 0. Used for agents that accept multiple inputs.
        :return: A tuple containing the header row and the data rows. The header row is a list of strings representing
            the column names, and the data rows are a list of dictionaries where each dictionary represents a row in the
            CSV with the column names as keys and the corresponding values as strings.
        """
        self._validate_get_input(index, ContainerType.CSV)
        container: StepItemContainerPbo = self.request.input[index].item_container
        if not container.HasField("csv_container"):
            return [], []
        ret_val: list[dict[str, str]] = []
        headers: Iterable[str] = container.csv_container.header.cells
        for row in container.csv_container.items:
            row_dict: dict[str, str] = {}
            for header, value in zip(headers, row.cells):
                row_dict[header] = value
            ret_val.append(row_dict)
        return list(headers), ret_val

    def get_input_json(self, index: int = 0) -> list[dict[str, Any]]:
        """
        Parse the JSON data from the request object.

        :param index: The index of the input to parse. Defaults to 0. Used for agents that accept multiple inputs.
        :return: A list of parsed JSON objects, which are represented as dictionaries.
        """
        self._validate_get_input(index, ContainerType.JSON)
        container: StepItemContainerPbo = self.request.input[index].item_container
        if not container.HasField("json_container"):
            return []
        input_json: list[Any] = [json.loads(x) for x in container.json_container.items]
        # Verify that the given JSON actually is a list of dictionaries. If they aren't then the previous step provided
        # bad input. Agents are enforced to result in a list of dictionaries when returning JSON data, so this is likely
        # an error caused by a script or static input step.
        for i, entry in enumerate(input_json):
            if not isinstance(entry, dict):
                raise Exception(f"Element {i} of input {index} is not a dictionary object. All top-level JSON inputs "
                                f"are expected to be dictionaries.")
        return input_json

    def get_input_text(self, index: int = 0) -> list[str]:
        """
        Parse the text data from the request object.

        :param index: The index of the input to parse. Defaults to 0. Used for agents that accept multiple inputs.
        :return: A list of text data as strings.
        """
        self._validate_get_input(index, ContainerType.TEXT)
        container: StepItemContainerPbo = self.request.input[index].item_container
        if not container.HasField("text_container"):
            return []
        return list(container.text_container.items)

    def get_config_defs(self) -> dict[str, VeloxFieldDefPbo]:
        """
        Get the config field definitions for this agent.

        :return: A dictionary of field definitions, where the keys are the field names and the values are the
            VeloxFieldDefPbo objects representing the field definitions.
        """
        field_defs: dict[str, VeloxFieldDefPbo] = {}
        for field_def in self.to_pbo().config_fields:
            field_defs[field_def.data_field_name] = field_def
        return field_defs

    def get_config_fields(self) -> dict[str, FieldValue | list[str]]:
        """
        Get the configuration field values from the request object. If a field is not present in the request,
        the default value from the config definition will be returned.

        :return: A dictionary of configuration field names and their values. For multi-select selection list fields,
            a list of strings will be returned. For all other field types, the value will match the field type
            (bool for boolean fields, float for double fields, int for short, integer, long, and enum fields, and
            string for everything else).
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        config_fields: dict[str, Any] = {}
        raw_configs: Mapping[str, FieldValuePbo] = self.request.config_field_values
        for field_name, field_def in self.get_config_defs().items():
            field_value: FieldValue = None
            # If the field is present in the request, convert the protobuf value to a Python value.
            if field_name in raw_configs:
                field_value = ProtobufUtils.field_pbo_to_value(raw_configs[field_name])
            # If the field isn't present or is None, use the default value from the field definition.
            if field_value is None:
                field_value = ProtobufUtils.field_def_pbo_to_default_value(field_def)
            # If the field is a multi-select selection list, split the value by commas and strip whitespace.
            if field_def.data_field_type == FieldTypePbo.SELECTION and field_def.selection_properties.multi_select:
                field_value: list[str] = [x.strip() for x in field_value.split(',') if x.strip()]
            config_fields[field_name] = field_value
        return config_fields

    def get_current_data_type_name(self) -> str:
        """
        :return: The data type name that is currently configured for this agent in the system. If the data type name
            of the output data type is needed during the agent's run function, this is how it should be accessed, as
            opposed to getting the name from the output_data_type function, as the data type name that the system is
            currently using may differ from the initial self-described name.
        """
        if not self.__is_setup:
            raise Exception("Cannot call this function before the agent has been set up to respond to a request.")
        return self.request.output_data_type_name

    @staticmethod
    def read_from_json(json_data: list[dict[str, Any]], key: str) -> list[Any]:
        """
        From a list of dictionaries, return a list of values for the given key from each dictionary. Skips null values.

        :param json_data: The JSON data to read from.
        :param key: The key to read the values from.
        :return: A list of values corresponding to the given key in the JSON data.
        """
        ret_val: list[Any] = []
        for entry in json_data:
            if key in entry:
                value = entry[key]
                if isinstance(value, list):
                    ret_val.extend(value)
                elif value is not None:
                    ret_val.append(value)
        return ret_val

    @staticmethod
    def flatten_text(text_data: list[str]) -> list[str]:
        """
        From a list of strings that come from a text input, flatten the list by splitting each string on newlines and
        stripping whitespace. Empty lines will be removed.

        :param text_data: The text data to flatten.
        :return: A flattened list of strings.
        """
        ret_val: list[str] = []
        for entry in text_data:
            lines: list[str] = [x.strip() for x in entry.splitlines() if x.strip()]
            ret_val.extend(lines)
        return ret_val
