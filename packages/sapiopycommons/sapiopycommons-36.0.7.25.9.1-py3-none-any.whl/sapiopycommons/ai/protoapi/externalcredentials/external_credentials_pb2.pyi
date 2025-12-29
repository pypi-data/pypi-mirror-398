from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ExternalCredentialsPbo(_message.Message):
    __slots__ = ("id", "display_name", "description", "category", "url", "username", "password", "token", "custom_field")
    class CustomFieldEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_FIELD_FIELD_NUMBER: _ClassVar[int]
    id: str
    display_name: str
    description: str
    category: str
    url: str
    username: str
    password: str
    token: str
    custom_field: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., display_name: _Optional[str] = ..., description: _Optional[str] = ..., category: _Optional[str] = ..., url: _Optional[str] = ..., username: _Optional[str] = ..., password: _Optional[str] = ..., token: _Optional[str] = ..., custom_field: _Optional[_Mapping[str, str]] = ...) -> None: ...
