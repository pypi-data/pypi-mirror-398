import inspect
from typing import List, Optional, Type

import uritemplate

from ..docstring import DocstringParser
from ..reflection import (BookOAuthAuthenticationDescriptor,
                          OauthArgumentDescriptor, OAuthFlow, OAuthProvider)


class oauth:  # pylint: disable=invalid-name
    id_prefix: str
    provider: OAuthProvider
    flows: List[OAuthFlow]
    authorize_endpoint: str
    token_endpoint: str
    authorization_code_scopes: List[str]
    client_credentials_scopes: List[str]

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        id_prefix: str,  # pylint: disable=redefined-builtin
        provider: OAuthProvider,
        authorize_endpoint: str,
        token_endpoint: str,
        flows: Optional[List[OAuthFlow]] = None,
        authorization_code_scopes: Optional[List[str]] = None,
        client_credentials_scopes: Optional[List[str]] = None,
    ):
        self.id_prefix = id_prefix
        self.provider = provider
        self.flows = flows if flows else [OAuthFlow.AUTHORIZATION_CODE]
        self.authorize_endpoint = authorize_endpoint
        self.token_endpoint = token_endpoint
        self.authorization_code_scopes = authorization_code_scopes or []
        self.client_credentials_scopes = client_credentials_scopes or []

    def __call__(self, cls: Type):
        def decorator(cls):
            if not inspect.isclass(cls):
                raise TypeError("The oauth decorator can only be applied to classes.")

            if not hasattr(cls, "__oauth__"):
                cls.__oauth__ = []

            if cls.__doc__:
                parsed_docstring = DocstringParser.parse(cls.__doc__)
            else:
                parsed_docstring = None

            additional_arg_names = list(set(uritemplate.variables(self.authorize_endpoint)).union(set(uritemplate.variables(self.token_endpoint))))
            additional_args = []

            for additional_arg in additional_arg_names:
                parsed_param = parsed_docstring.param_by_name(additional_arg) if parsed_docstring else None

                additional_args.append(
                    OauthArgumentDescriptor(
                        id=parsed_param.name if parsed_param else additional_arg,  # type: ignore
                        name=(parsed_param.label or parsed_param.name) if parsed_param else additional_arg,  # type: ignore
                        description=parsed_param.description if parsed_param else None,
                    )
                )

            for flow in self.flows:
                if flow == OAuthFlow.AUTHORIZATION_CODE:
                    scopes = self.authorization_code_scopes
                    name = "OAuth Authorization Code"
                elif flow == OAuthFlow.CLIENT_CREDENTIALS:
                    scopes = self.client_credentials_scopes
                    name = "OAuth Client Credentials"
                else:
                    raise ValueError(f"Invalid flow: {flow}")

                cls.__oauth__.append(
                    BookOAuthAuthenticationDescriptor(
                        id=self.id_prefix + "_" + flow.name.lower(),
                        description=None,
                        provider=self.provider,
                        flows=[flow],
                        authorize_endpoint=self.authorize_endpoint,
                        token_endpoint=self.token_endpoint,
                        scopes=scopes,
                        name=name,
                        arguments=additional_args,
                    )
                )

            return cls

        if cls is None:
            return decorator

        return decorator(cls)
