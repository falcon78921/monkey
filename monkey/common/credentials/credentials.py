from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional, Sequence, Type

from marshmallow import Schema, fields, post_load, pre_dump
from marshmallow.exceptions import MarshmallowError

from ..utils import IJSONSerializable
from . import (
    CredentialComponentType,
    InvalidCredentialComponentError,
    InvalidCredentialsError,
    LMHash,
    NTHash,
    Password,
    SSHKeypair,
    Username,
)
from .i_credential_component import ICredentialComponent
from .lm_hash import LMHashSchema
from .nt_hash import NTHashSchema
from .password import PasswordSchema
from .ssh_keypair import SSHKeypairSchema
from .username import UsernameSchema

CREDENTIAL_COMPONENT_TYPE_TO_CLASS: Mapping[CredentialComponentType, Type[ICredentialComponent]] = {
    CredentialComponentType.LM_HASH: LMHash,
    CredentialComponentType.NT_HASH: NTHash,
    CredentialComponentType.PASSWORD: Password,
    CredentialComponentType.SSH_KEYPAIR: SSHKeypair,
    CredentialComponentType.USERNAME: Username,
}

CREDENTIAL_COMPONENT_TYPE_TO_CLASS_SCHEMA: Mapping[CredentialComponentType, Schema] = {
    CredentialComponentType.LM_HASH: LMHashSchema(),
    CredentialComponentType.NT_HASH: NTHashSchema(),
    CredentialComponentType.PASSWORD: PasswordSchema(),
    CredentialComponentType.SSH_KEYPAIR: SSHKeypairSchema(),
    CredentialComponentType.USERNAME: UsernameSchema(),
}


class CredentialsSchema(Schema):
    identity = fields.Mapping(allow_none=True)
    secret = fields.Mapping(allow_none=True)

    @post_load
    def _make_credentials(
        self, data: MutableMapping, **kwargs: Mapping[str, Any]
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        if not any(data.values()):
            raise InvalidCredentialsError("At least one credentials component must be defined")

        data["identity"] = CredentialsSchema._build_credential_component(data["identity"])
        data["secret"] = CredentialsSchema._build_credential_component(data["secret"])

        return data

    @staticmethod
    def _build_credential_component(
        credential_component: Optional[Mapping[str, Any]]
    ) -> Optional[ICredentialComponent]:
        if credential_component is None:
            return None

        try:
            credential_component_type = CredentialComponentType[
                credential_component["credential_type"]
            ]
        except KeyError as err:
            raise InvalidCredentialsError(f"Unknown credential component type {err}")

        credential_component_class = CREDENTIAL_COMPONENT_TYPE_TO_CLASS[credential_component_type]
        credential_component_schema = CREDENTIAL_COMPONENT_TYPE_TO_CLASS_SCHEMA[
            credential_component_type
        ]

        try:
            return credential_component_class(
                **credential_component_schema.load(credential_component)
            )
        except MarshmallowError as err:
            raise InvalidCredentialComponentError(credential_component_class, str(err))

    @pre_dump
    def _serialize_credentials(
        self, credentials: Credentials, **kwargs
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        data = {}

        data["identity"] = CredentialsSchema._serialize_credential_component(credentials.identity)
        data["secret"] = CredentialsSchema._serialize_credential_component(credentials.secret)

        return data

    @staticmethod
    def _serialize_credential_component(
        credential_component: Optional[ICredentialComponent],
    ) -> Optional[Mapping[str, Any]]:
        if credential_component is None:
            return None

        credential_component_schema = CREDENTIAL_COMPONENT_TYPE_TO_CLASS_SCHEMA[
            credential_component.credential_type
        ]

        return credential_component_schema.dump(credential_component)


@dataclass(frozen=True)
class Credentials(IJSONSerializable):
    identity: Optional[ICredentialComponent]
    secret: Optional[ICredentialComponent]

    def __post_init__(self):
        schema = CredentialsSchema()
        try:
            serialized_data = schema.dump(self)

            # This will raise an exception if the object is invalid. Calling this in __post__init()
            # makes it impossible to construct an invalid object
            schema.load(serialized_data)
        except Exception as err:
            raise InvalidCredentialsError(err)

    @staticmethod
    def from_mapping(credentials: Mapping) -> Credentials:
        """
        Construct a Credentials object from a Mapping

        :param credentials: A mapping that represents a Credentials object
        :return: A Credentials object
        :raises InvalidCredentialsError: If the provided Mapping does not represent a valid
                                         Credentials object
        :raises InvalidCredentialComponentError: If any of the contents of `identities` or `secrets`
                                                 are not a valid ICredentialComponent
        """

        try:
            deserialized_data = CredentialsSchema().load(credentials)
            return Credentials(**deserialized_data)
        except (InvalidCredentialsError, InvalidCredentialComponentError) as err:
            raise err
        except MarshmallowError as err:
            raise InvalidCredentialsError(str(err))

    @classmethod
    def from_json(cls, credentials: str) -> Credentials:
        """
        Construct a Credentials object from a JSON string

        :param credentials: A JSON string that represents a Credentials object
        :return: A Credentials object
        :raises InvalidCredentialsError: If the provided JSON does not represent a valid
                                         Credentials object
        :raises InvalidCredentialComponentError: If any of the contents of `identities` or `secrets`
                                                 are not a valid ICredentialComponent
        """

        try:
            deserialized_data = CredentialsSchema().loads(credentials)
            return Credentials(**deserialized_data)
        except (InvalidCredentialsError, InvalidCredentialComponentError) as err:
            raise err
        except MarshmallowError as err:
            raise InvalidCredentialsError(str(err))

    @staticmethod
    def to_mapping(credentials: Credentials) -> Mapping:
        """
        Serialize a Credentials object to a Mapping

        :param credentials: A Credentials object
        :return: A mapping representing a Credentials object
        """

        return CredentialsSchema().dump(credentials)

    @classmethod
    def to_json(cls, credentials: Credentials) -> str:
        """
        Serialize a Credentials object to JSON

        :param credentials: A Credentials object
        :return: A JSON string representing a Credentials object
        """

        return CredentialsSchema().dumps(credentials)
