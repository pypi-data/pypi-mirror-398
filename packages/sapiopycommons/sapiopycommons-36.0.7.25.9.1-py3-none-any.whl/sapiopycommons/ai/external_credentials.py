from __future__ import annotations

from sapiopycommons.ai.protoapi.externalcredentials.external_credentials_pb2 import ExternalCredentialsPbo


class ExternalCredentials:
    """
    A class representing external credentials.
    """
    _identifier: str
    _display_name: str
    _description: str
    _category: str
    _url: str
    _username: str
    _password: str
    _token: str
    _custom_fields: dict[str, str]

    def __init__(self, url: str, category: str, identifier: str = "", display_name: str = "", description: str = "",
                 username: str = "", password: str = "", token: str = "", custom_fields: dict[str, str] | None = None):
        """
        :param url: The URL that the credentials are for.
        :param category: The category of the credentials. This can be used to search for the credentials using the
            AgentBase.get_credentials function.
        :param identifier: The unique identifier for the credentials.
        :param display_name: The display name for the credentials.
        :param description: A description of the credentials.
        :param username: The username for the credentials.
        :param password: The password for the credentials.
        :param token: The token for the credentials.
        :param custom_fields: A dictionary of custom fields associated with the credentials.
        """
        self._identifier = identifier
        self._display_name = display_name
        self._description = description
        self._category = category
        self._url = url
        self._username = username
        self._password = password
        self._token = token
        self._custom_fields = custom_fields or {}

    @staticmethod
    def from_pbo(pbo: ExternalCredentialsPbo) -> ExternalCredentials:
        """
        Create an ExternalCredentials instance from a protobuf object.

        :param pbo: An ExternalCredentialsPbo object.
        :return: An ExternalCredentials instance.
        """
        creds = ExternalCredentials(pbo.url, pbo.category)
        creds._identifier = pbo.id
        creds._display_name = pbo.display_name
        creds._description = pbo.description
        creds._username = pbo.username
        creds._password = pbo.password
        creds._token = pbo.token
        creds._custom_fields = dict(pbo.custom_field)
        return creds

    @property
    def identifier(self) -> str:
        """The unique identifier for the credentials."""
        return self._identifier

    @property
    def display_name(self) -> str:
        """The display name for the credentials."""
        return self._display_name

    @property
    def description(self) -> str:
        """A description of the credentials."""
        return self._description

    @property
    def category(self) -> str:
        """The category of the credentials."""
        return self._category

    @property
    def url(self) -> str:
        """The URL that the credentials are for."""
        return self._url

    @property
    def username(self) -> str:
        """The username for the credentials."""
        return self._username

    @property
    def password(self) -> str:
        """The password for the credentials."""
        return self._password

    @property
    def token(self) -> str:
        """The token for the credentials."""
        return self._token

    def get_custom_field(self, key: str, default: str = None) -> str | None:
        """
        Get a custom field by key.

        :param key: The key of the custom field to retrieve.
        :param default: The value to return if the key does not exist.
        :return: The value of the custom field, or None if the key does not exist.
        """
        return self._custom_fields.get(key, default)

    def to_pbo(self) -> ExternalCredentialsPbo:
        """
        Convert the ExternalCredentials instance to a protobuf object.

        :return: An ExternalCredentialsPbo object.
        """
        return ExternalCredentialsPbo(
            id=self._identifier,
            display_name=self._display_name,
            description=self._description,
            category=self._category,
            url=self._url,
            username=self._username,
            password=self._password,
            token=self._token,
            custom_field=self._custom_fields
        )
