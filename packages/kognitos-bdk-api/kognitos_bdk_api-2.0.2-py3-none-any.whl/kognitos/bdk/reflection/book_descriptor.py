import inspect
from typing import List, Optional, Type

from kognitos.bdk.api.noun_phrase import NounPhrase

from .authentication import (BookAuthenticationDescriptor,
                             BookOAuthAuthenticationDescriptor,
                             OAuthTokenFunction)
from .book_config_descriptor import BookConfigDescriptor
from .book_procedure_descriptor import (BookProcedureDescriptor,
                                        ConnectionRequired)
from .book_trigger_descriptor import BookTriggerDescriptor


class BookDescriptor:
    cls: Type
    _id: str
    _name: str
    _author: Optional[str]
    _short_description: Optional[str]
    _long_description: Optional[str]
    _icon: Optional[bytes]
    _configuration: List[BookConfigDescriptor]
    _tags: List[str]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        cls: Type,
        identifier: str,
        name: Optional[str] = None,
        noun_phrase: Optional[NounPhrase] = None,
        author: Optional[str] = None,
        short_description: Optional[str] = None,
        long_description: Optional[str] = None,
        icon: Optional[bytes] = None,
        icon_path: Optional[str] = None,
        configuration: Optional[List[BookConfigDescriptor]] = None,
        tags: Optional[List[str]] = None,
    ):
        self._id = identifier
        self._name = name
        self.cls = cls
        self._author = author
        self._noun_phrase = noun_phrase
        self._short_description = short_description
        self._long_description = long_description
        self._icon = icon
        self._icon_path = icon_path
        self._configuration = configuration
        self._tags = tags or []

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def noun_phrase(self) -> Optional[NounPhrase]:
        return self._noun_phrase

    @property
    def author(self) -> Optional[str]:
        return self._author

    @property
    def short_description(self) -> Optional[str]:
        return self._short_description

    @property
    def long_description(self) -> Optional[str]:
        return self._long_description

    @property
    def configuration(self) -> List[BookConfigDescriptor]:
        return self._configuration

    @property
    def icon(self) -> Optional[bytes]:
        return self._icon

    @property
    def icon_path(self) -> Optional[str]:
        return self._icon_path

    @property
    def authentications(self) -> List[BookAuthenticationDescriptor]:
        authentications = []
        oauth_token_function = None

        for _, member in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            authentication = getattr(member, "__connect__", None)
            if authentication:
                authentications.append(authentication)

            is_oauth_token_function = getattr(member, "__oauthtoken__", None)
            if is_oauth_token_function:
                oauth_token_function = OAuthTokenFunction(name=member.__name__, access_token_is_sensitive=member.__access_token_is_sensitive__)

        oauths: List[BookOAuthAuthenticationDescriptor] = getattr(self.cls, "__oauth__", [])

        for oauth in oauths:
            oauth.oauth_token_function = oauth_token_function

        authentications.extend(oauths)

        return authentications

    @property
    def procedures(self) -> List[BookProcedureDescriptor]:
        has_authentications = len(self.authentications) > 0
        procedures = []

        for _, member in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            procedure = getattr(member, "__procedure__", None)
            if procedure:
                if procedure.override_connection_required is not None:
                    # Legacy support for boolean
                    if isinstance(procedure.override_connection_required, ConnectionRequired):
                        connection_required = procedure.override_connection_required
                    else:  # Is boolean
                        connection_required = ConnectionRequired.ALWAYS if procedure.override_connection_required else ConnectionRequired.OPTIONAL
                else:
                    connection_required = ConnectionRequired.ALWAYS if has_authentications else ConnectionRequired.NEVER

                procedure.connection_required = connection_required
                procedures.append(procedure)

        return procedures

    @property
    def blueprints(self) -> List[str]:
        return getattr(self.cls, "__blueprints__", [])

    @property
    def connection_required(self) -> bool:
        if not self.authentications:
            return False
        procedures = self.procedures
        return all(p.connection_required == ConnectionRequired.ALWAYS for p in procedures)

    @property
    def discover_function_name(self) -> Optional[str]:
        for _, member in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            if getattr(member, "__discover__", None):
                return member.__name__

        return None

    @property
    def invoke_function_name(self) -> Optional[str]:
        for _, member in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            if getattr(member, "__invoke__", None):
                return member.__name__

        return None

    @property
    def discoverables_function_name(self) -> Optional[str]:
        for _, member in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            if getattr(member, "__discoverables__", None):
                return member.__name__

        return None

    @property
    def userinfo_function_name(self) -> Optional[str]:
        for _, member in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            if getattr(member, "__userinfo__", None):
                return member.__name__

        return None

    @property
    def discover_capable(self) -> bool:
        return self.discover_function_name is not None and self.invoke_function_name is not None

    @property
    def tags(self) -> List[str]:
        return self._tags

    @property
    def triggers(self) -> List[BookTriggerDescriptor]:
        """
        Get all triggers defined in the book.

        Returns:
            List of BookTriggerDescriptor for all functions decorated with @trigger
        """
        triggers = []

        for _, member in inspect.getmembers(self.cls, predicate=inspect.isfunction):
            trigger = getattr(member, "__trigger__", None)
            if trigger:
                triggers.append(trigger)

        return triggers
