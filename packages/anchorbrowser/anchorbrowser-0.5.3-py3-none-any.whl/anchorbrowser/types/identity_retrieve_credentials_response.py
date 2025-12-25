# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias

from .._models import BaseModel

__all__ = [
    "IdentityRetrieveCredentialsResponse",
    "Credential",
    "CredentialUsernamePasswordCredentialSchema",
    "CredentialAuthenticatorCredentialSchema",
    "CredentialCustomCredentialSchema",
    "CredentialCustomCredentialSchemaField",
]


class CredentialUsernamePasswordCredentialSchema(BaseModel):
    password: Optional[str] = None
    """The password of the credential"""

    type: Optional[Literal["username_password"]] = None
    """The type of credential"""

    username: Optional[str] = None
    """The username of the credential"""


class CredentialAuthenticatorCredentialSchema(BaseModel):
    otp: Optional[str] = None
    """The OTP of the credential"""

    secret: Optional[str] = None
    """The secret of the credential"""

    type: Optional[Literal["authenticator"]] = None
    """The type of credential"""


class CredentialCustomCredentialSchemaField(BaseModel):
    name: Optional[str] = None
    """The name of the field"""

    value: Optional[str] = None
    """The value of the field"""


class CredentialCustomCredentialSchema(BaseModel):
    fields: Optional[List[CredentialCustomCredentialSchemaField]] = None

    type: Optional[Literal["custom"]] = None
    """The type of credential"""


Credential: TypeAlias = Union[
    CredentialUsernamePasswordCredentialSchema,
    CredentialAuthenticatorCredentialSchema,
    CredentialCustomCredentialSchema,
]


class IdentityRetrieveCredentialsResponse(BaseModel):
    id: Optional[str] = None
    """The ID of the identity"""

    credentials: Optional[List[Credential]] = None

    name: Optional[str] = None
    """The name of the identity"""

    source: Optional[str] = None
    """The url related to the identity"""
