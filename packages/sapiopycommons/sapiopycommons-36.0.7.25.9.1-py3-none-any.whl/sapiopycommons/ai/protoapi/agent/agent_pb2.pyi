from sapiopycommons.ai.protoapi.externalcredentials import external_credentials_pb2 as _external_credentials_pb2
from sapiopycommons.ai.protoapi.fielddefinitions import fields_pb2 as _fields_pb2
from sapiopycommons.ai.protoapi.fielddefinitions import velox_field_def_pb2 as _velox_field_def_pb2
from sapiopycommons.ai.protoapi.agent import entry_pb2 as _entry_pb2
from sapiopycommons.ai.protoapi.agent.item import item_container_pb2 as _item_container_pb2
from sapiopycommons.ai.protoapi.pipeline import step_pb2 as _step_pb2
from sapiopycommons.ai.protoapi.session import sapio_conn_info_pb2 as _sapio_conn_info_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
from sapiopycommons.ai.protoapi.externalcredentials.external_credentials_pb2 import ExternalCredentialsPbo as ExternalCredentialsPbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValuePbo as FieldValuePbo
from sapiopycommons.ai.protoapi.fielddefinitions.fields_pb2 import FieldValueMapPbo as FieldValueMapPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FieldValidatorPbo as FieldValidatorPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ColorRangePbo as ColorRangePbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import BooleanDependentFieldEntryPbo as BooleanDependentFieldEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SelectionDependentFieldEntryPbo as SelectionDependentFieldEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import EnumDependentFieldEntryPbo as EnumDependentFieldEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ProcessDetailEntryPbo as ProcessDetailEntryPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import BooleanPropertiesPbo as BooleanPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DatePropertiesPbo as DatePropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DoublePropertiesPbo as DoublePropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import IntegerPropertiesPbo as IntegerPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import LongPropertiesPbo as LongPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ShortPropertiesPbo as ShortPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SelectionPropertiesPbo as SelectionPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import StringPropertiesPbo as StringPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SideLinkPropertiesPbo as SideLinkPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import PickListPropertiesPbo as PickListPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ParentLinkPropertiesPbo as ParentLinkPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import MultiParentPropertiesPbo as MultiParentPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import IdentifierPropertiesPbo as IdentifierPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FileBlobPropertiesPbo as FileBlobPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import EnumPropertiesPbo as EnumPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DateRangePropertiesPbo as DateRangePropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ChildLinkPropertiesPbo as ChildLinkPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ActionStringPropertiesPbo as ActionStringPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import ActionPropertiesPbo as ActionPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import AccessionPropertiesPbo as AccessionPropertiesPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import VeloxFieldDefPbo as VeloxFieldDefPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import VeloxFieldDefListPbo as VeloxFieldDefListPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FieldTypePbo as FieldTypePbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import SortDirectionPbo as SortDirectionPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import FontSizePbo as FontSizePbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import TextDecorationPbo as TextDecorationPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import StringFormatPbo as StringFormatPbo
from sapiopycommons.ai.protoapi.fielddefinitions.velox_field_def_pb2 import DoubleFormatPbo as DoubleFormatPbo
from sapiopycommons.ai.protoapi.agent.entry_pb2 import StepInputBatchPbo as StepInputBatchPbo
from sapiopycommons.ai.protoapi.agent.entry_pb2 import StepOutputBatchPbo as StepOutputBatchPbo
from sapiopycommons.ai.protoapi.pipeline.step_pb2 import StepIoInfoPbo as StepIoInfoPbo
from sapiopycommons.ai.protoapi.pipeline.step_pb2 import StepIoDetailsPbo as StepIoDetailsPbo
from sapiopycommons.ai.protoapi.pipeline.step_pb2 import StepInputDetailsPbo as StepInputDetailsPbo
from sapiopycommons.ai.protoapi.pipeline.step_pb2 import StepOutputDetailsPbo as StepOutputDetailsPbo
from sapiopycommons.ai.protoapi.session.sapio_conn_info_pb2 import SapioConnectionInfoPbo as SapioConnectionInfoPbo
from sapiopycommons.ai.protoapi.session.sapio_conn_info_pb2 import SapioUserSecretTypePbo as SapioUserSecretTypePbo

DESCRIPTOR: _descriptor.FileDescriptor
FIELD_TYPE_UNSPECIFIED: _velox_field_def_pb2.FieldTypePbo
BOOLEAN: _velox_field_def_pb2.FieldTypePbo
DOUBLE: _velox_field_def_pb2.FieldTypePbo
ENUM: _velox_field_def_pb2.FieldTypePbo
LONG: _velox_field_def_pb2.FieldTypePbo
INTEGER: _velox_field_def_pb2.FieldTypePbo
SHORT: _velox_field_def_pb2.FieldTypePbo
STRING: _velox_field_def_pb2.FieldTypePbo
DATE: _velox_field_def_pb2.FieldTypePbo
ACTION: _velox_field_def_pb2.FieldTypePbo
SELECTION: _velox_field_def_pb2.FieldTypePbo
PARENTLINK: _velox_field_def_pb2.FieldTypePbo
IDENTIFIER: _velox_field_def_pb2.FieldTypePbo
PICKLIST: _velox_field_def_pb2.FieldTypePbo
LINK: _velox_field_def_pb2.FieldTypePbo
MULTIPARENTLINK: _velox_field_def_pb2.FieldTypePbo
CHILDLINK: _velox_field_def_pb2.FieldTypePbo
AUTO_ACCESSION: _velox_field_def_pb2.FieldTypePbo
DATE_RANGE: _velox_field_def_pb2.FieldTypePbo
SIDE_LINK: _velox_field_def_pb2.FieldTypePbo
ACTION_STRING: _velox_field_def_pb2.FieldTypePbo
FILE_BLOB: _velox_field_def_pb2.FieldTypePbo
SORT_DIRECTION_UNSPECIFIED: _velox_field_def_pb2.SortDirectionPbo
SORT_DIRECTION_ASCENDING: _velox_field_def_pb2.SortDirectionPbo
SORT_DIRECTION_DESCENDING: _velox_field_def_pb2.SortDirectionPbo
SORT_DIRECTION_NONE: _velox_field_def_pb2.SortDirectionPbo
FONT_SIZE_UNSPECIFIED: _velox_field_def_pb2.FontSizePbo
FONT_SIZE_SMALL: _velox_field_def_pb2.FontSizePbo
FONT_SIZE_MEDIUM: _velox_field_def_pb2.FontSizePbo
FONT_SIZE_LARGE: _velox_field_def_pb2.FontSizePbo
TEXT_DECORATION_UNSPECIFIED: _velox_field_def_pb2.TextDecorationPbo
TEXT_DECORATION_NONE: _velox_field_def_pb2.TextDecorationPbo
TEXT_DECORATION_UNDERLINE: _velox_field_def_pb2.TextDecorationPbo
TEXT_DECORATION_STRIKETHROUGH: _velox_field_def_pb2.TextDecorationPbo
STRING_FORMAT_UNSPECIFIED: _velox_field_def_pb2.StringFormatPbo
STRING_FORMAT_PHONE: _velox_field_def_pb2.StringFormatPbo
STRING_FORMAT_EMAIL: _velox_field_def_pb2.StringFormatPbo
DOUBLE_FORMAT_UNSPECIFIED: _velox_field_def_pb2.DoubleFormatPbo
DOUBLE_FORMAT_CURRENCY: _velox_field_def_pb2.DoubleFormatPbo
DOUBLE_FORMAT_PERCENTAGE: _velox_field_def_pb2.DoubleFormatPbo
SESSION_TOKEN: _sapio_conn_info_pb2.SapioUserSecretTypePbo
PASSWORD: _sapio_conn_info_pb2.SapioUserSecretTypePbo

class ProcessStepResponseStatusPbo(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[ProcessStepResponseStatusPbo]
    SUCCESS: _ClassVar[ProcessStepResponseStatusPbo]
    FAILURE: _ClassVar[ProcessStepResponseStatusPbo]
UNKNOWN: ProcessStepResponseStatusPbo
SUCCESS: ProcessStepResponseStatusPbo
FAILURE: ProcessStepResponseStatusPbo

class ExampleContainerPbo(_message.Message):
    __slots__ = ("text_example", "binary_example")
    TEXT_EXAMPLE_FIELD_NUMBER: _ClassVar[int]
    BINARY_EXAMPLE_FIELD_NUMBER: _ClassVar[int]
    text_example: str
    binary_example: bytes
    def __init__(self, text_example: _Optional[str] = ..., binary_example: _Optional[bytes] = ...) -> None: ...

class AgentIoConfigBasePbo(_message.Message):
    __slots__ = ("content_type", "io_number", "display_name", "description", "deprecated_old_example", "structure_example", "testing_example")
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    IO_NUMBER_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    DEPRECATED_OLD_EXAMPLE_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_EXAMPLE_FIELD_NUMBER: _ClassVar[int]
    TESTING_EXAMPLE_FIELD_NUMBER: _ClassVar[int]
    content_type: str
    io_number: int
    display_name: str
    description: str
    deprecated_old_example: str
    structure_example: ExampleContainerPbo
    testing_example: ExampleContainerPbo
    def __init__(self, content_type: _Optional[str] = ..., io_number: _Optional[int] = ..., display_name: _Optional[str] = ..., description: _Optional[str] = ..., deprecated_old_example: _Optional[str] = ..., structure_example: _Optional[_Union[ExampleContainerPbo, _Mapping]] = ..., testing_example: _Optional[_Union[ExampleContainerPbo, _Mapping]] = ...) -> None: ...

class AgentInputDetailsPbo(_message.Message):
    __slots__ = ("base_config", "validation", "min_input_count", "max_input_count", "paged", "min_page_size", "max_page_size", "max_request_bytes")
    BASE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_FIELD_NUMBER: _ClassVar[int]
    MIN_INPUT_COUNT_FIELD_NUMBER: _ClassVar[int]
    MAX_INPUT_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGED_FIELD_NUMBER: _ClassVar[int]
    MIN_PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAX_REQUEST_BYTES_FIELD_NUMBER: _ClassVar[int]
    base_config: AgentIoConfigBasePbo
    validation: str
    min_input_count: int
    max_input_count: int
    paged: bool
    min_page_size: int
    max_page_size: int
    max_request_bytes: int
    def __init__(self, base_config: _Optional[_Union[AgentIoConfigBasePbo, _Mapping]] = ..., validation: _Optional[str] = ..., min_input_count: _Optional[int] = ..., max_input_count: _Optional[int] = ..., paged: bool = ..., min_page_size: _Optional[int] = ..., max_page_size: _Optional[int] = ..., max_request_bytes: _Optional[int] = ...) -> None: ...

class AgentOutputDetailsPbo(_message.Message):
    __slots__ = ("base_config",)
    BASE_CONFIG_FIELD_NUMBER: _ClassVar[int]
    base_config: AgentIoConfigBasePbo
    def __init__(self, base_config: _Optional[_Union[AgentIoConfigBasePbo, _Mapping]] = ...) -> None: ...

class ProcessStepRequestPbo(_message.Message):
    __slots__ = ("sapio_user", "agent_name", "pipeline_id", "pipeline_step_id", "invocation_id", "input_configs", "output_configs", "config_field_values", "dry_run", "verbose_logging", "external_credential", "output_data_type_name", "input")
    class ConfigFieldValuesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _fields_pb2.FieldValuePbo
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_fields_pb2.FieldValuePbo, _Mapping]] = ...) -> None: ...
    SAPIO_USER_FIELD_NUMBER: _ClassVar[int]
    AGENT_NAME_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_ID_FIELD_NUMBER: _ClassVar[int]
    PIPELINE_STEP_ID_FIELD_NUMBER: _ClassVar[int]
    INVOCATION_ID_FIELD_NUMBER: _ClassVar[int]
    INPUT_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_VALUES_FIELD_NUMBER: _ClassVar[int]
    DRY_RUN_FIELD_NUMBER: _ClassVar[int]
    VERBOSE_LOGGING_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_CREDENTIAL_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_DATA_TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    sapio_user: _sapio_conn_info_pb2.SapioConnectionInfoPbo
    agent_name: str
    pipeline_id: int
    pipeline_step_id: int
    invocation_id: int
    input_configs: _containers.RepeatedCompositeFieldContainer[_step_pb2.StepIoInfoPbo]
    output_configs: _containers.RepeatedCompositeFieldContainer[_step_pb2.StepIoInfoPbo]
    config_field_values: _containers.MessageMap[str, _fields_pb2.FieldValuePbo]
    dry_run: bool
    verbose_logging: bool
    external_credential: _containers.RepeatedCompositeFieldContainer[_external_credentials_pb2.ExternalCredentialsPbo]
    output_data_type_name: str
    input: _containers.RepeatedCompositeFieldContainer[_entry_pb2.StepInputBatchPbo]
    def __init__(self, sapio_user: _Optional[_Union[_sapio_conn_info_pb2.SapioConnectionInfoPbo, _Mapping]] = ..., agent_name: _Optional[str] = ..., pipeline_id: _Optional[int] = ..., pipeline_step_id: _Optional[int] = ..., invocation_id: _Optional[int] = ..., input_configs: _Optional[_Iterable[_Union[_step_pb2.StepIoInfoPbo, _Mapping]]] = ..., output_configs: _Optional[_Iterable[_Union[_step_pb2.StepIoInfoPbo, _Mapping]]] = ..., config_field_values: _Optional[_Mapping[str, _fields_pb2.FieldValuePbo]] = ..., dry_run: bool = ..., verbose_logging: bool = ..., external_credential: _Optional[_Iterable[_Union[_external_credentials_pb2.ExternalCredentialsPbo, _Mapping]]] = ..., output_data_type_name: _Optional[str] = ..., input: _Optional[_Iterable[_Union[_entry_pb2.StepInputBatchPbo, _Mapping]]] = ...) -> None: ...

class ProcessStepResponsePbo(_message.Message):
    __slots__ = ("status", "status_message", "step_summary", "new_records", "log", "output")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    STEP_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    NEW_RECORDS_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    status: ProcessStepResponseStatusPbo
    status_message: str
    step_summary: str
    new_records: _containers.RepeatedCompositeFieldContainer[_fields_pb2.FieldValueMapPbo]
    log: _containers.RepeatedScalarFieldContainer[str]
    output: _containers.RepeatedCompositeFieldContainer[_entry_pb2.StepOutputBatchPbo]
    def __init__(self, status: _Optional[_Union[ProcessStepResponseStatusPbo, str]] = ..., status_message: _Optional[str] = ..., step_summary: _Optional[str] = ..., new_records: _Optional[_Iterable[_Union[_fields_pb2.FieldValueMapPbo, _Mapping]]] = ..., log: _Optional[_Iterable[str]] = ..., output: _Optional[_Iterable[_Union[_entry_pb2.StepOutputBatchPbo, _Mapping]]] = ...) -> None: ...

class AgentDetailsRequestPbo(_message.Message):
    __slots__ = ("sapio_conn_info",)
    SAPIO_CONN_INFO_FIELD_NUMBER: _ClassVar[int]
    sapio_conn_info: _sapio_conn_info_pb2.SapioConnectionInfoPbo
    def __init__(self, sapio_conn_info: _Optional[_Union[_sapio_conn_info_pb2.SapioConnectionInfoPbo, _Mapping]] = ...) -> None: ...

class AgentDetailsPbo(_message.Message):
    __slots__ = ("import_id", "name", "description", "output_data_type_name", "input_configs", "output_configs", "config_fields", "license_info", "category", "citation", "review_on_instance_field_names", "output_data_type_display_name", "output_type_fields", "sub_category", "icon", "output_data_type_icon")
    IMPORT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_DATA_TYPE_NAME_FIELD_NUMBER: _ClassVar[int]
    INPUT_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_CONFIGS_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELDS_FIELD_NUMBER: _ClassVar[int]
    LICENSE_INFO_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    CITATION_FIELD_NUMBER: _ClassVar[int]
    REVIEW_ON_INSTANCE_FIELD_NAMES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_DATA_TYPE_DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TYPE_FIELDS_FIELD_NUMBER: _ClassVar[int]
    SUB_CATEGORY_FIELD_NUMBER: _ClassVar[int]
    ICON_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_DATA_TYPE_ICON_FIELD_NUMBER: _ClassVar[int]
    import_id: str
    name: str
    description: str
    output_data_type_name: str
    input_configs: _containers.RepeatedCompositeFieldContainer[AgentInputDetailsPbo]
    output_configs: _containers.RepeatedCompositeFieldContainer[AgentOutputDetailsPbo]
    config_fields: _containers.RepeatedCompositeFieldContainer[_velox_field_def_pb2.VeloxFieldDefPbo]
    license_info: str
    category: str
    citation: _containers.RepeatedCompositeFieldContainer[AgentCitationPbo]
    review_on_instance_field_names: _containers.RepeatedScalarFieldContainer[str]
    output_data_type_display_name: str
    output_type_fields: _containers.RepeatedCompositeFieldContainer[_velox_field_def_pb2.VeloxFieldDefPbo]
    sub_category: str
    icon: bytes
    output_data_type_icon: bytes
    def __init__(self, import_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., output_data_type_name: _Optional[str] = ..., input_configs: _Optional[_Iterable[_Union[AgentInputDetailsPbo, _Mapping]]] = ..., output_configs: _Optional[_Iterable[_Union[AgentOutputDetailsPbo, _Mapping]]] = ..., config_fields: _Optional[_Iterable[_Union[_velox_field_def_pb2.VeloxFieldDefPbo, _Mapping]]] = ..., license_info: _Optional[str] = ..., category: _Optional[str] = ..., citation: _Optional[_Iterable[_Union[AgentCitationPbo, _Mapping]]] = ..., review_on_instance_field_names: _Optional[_Iterable[str]] = ..., output_data_type_display_name: _Optional[str] = ..., output_type_fields: _Optional[_Iterable[_Union[_velox_field_def_pb2.VeloxFieldDefPbo, _Mapping]]] = ..., sub_category: _Optional[str] = ..., icon: _Optional[bytes] = ..., output_data_type_icon: _Optional[bytes] = ...) -> None: ...

class AgentCitationPbo(_message.Message):
    __slots__ = ("title", "url")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    title: str
    url: str
    def __init__(self, title: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class AgentDetailsResponsePbo(_message.Message):
    __slots__ = ("agent_framework_version", "agent_details")
    AGENT_FRAMEWORK_VERSION_FIELD_NUMBER: _ClassVar[int]
    AGENT_DETAILS_FIELD_NUMBER: _ClassVar[int]
    agent_framework_version: int
    agent_details: _containers.RepeatedCompositeFieldContainer[AgentDetailsPbo]
    def __init__(self, agent_framework_version: _Optional[int] = ..., agent_details: _Optional[_Iterable[_Union[AgentDetailsPbo, _Mapping]]] = ...) -> None: ...
