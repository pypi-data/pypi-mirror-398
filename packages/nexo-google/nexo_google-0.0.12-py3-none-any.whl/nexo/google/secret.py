from copy import deepcopy
from datetime import datetime, timezone
from enum import StrEnum
from google.api_core.exceptions import NotFound as GoogleNotFound
from google.cloud import secretmanager
from pydantic import BaseModel, Field
from typing import Annotated, Dict, Generic, Literal, TypeVar, Union, overload
from uuid import uuid4
from nexo.logging.config import LogConfig
from nexo.logging.enums import LogLevel
from nexo.schemas.application import OptApplicationContext
from nexo.schemas.connection import OptConnectionContext
from nexo.schemas.error.enums import ErrorCode
from nexo.schemas.exception.factory import MaleoExceptionFactory
from nexo.schemas.operation.enums import OperationType
from nexo.schemas.operation.mixins import Timestamp
from nexo.schemas.operation.resource import (
    CreateResourceOperationAction,
    ReadResourceOperationAction,
    CreateSingleResourceOperation,
    ReadSingleResourceOperation,
)
from nexo.schemas.resource import ResourceIdentifier, AggregateField
from nexo.schemas.response import (
    SingleDataResponse,
    CreateSingleDataResponse,
    ReadSingleDataResponse,
)
from nexo.schemas.security.authentication import OptAnyAuthentication
from nexo.schemas.security.authorization import OptAnyAuthorization
from nexo.schemas.security.impersonation import OptImpersonation
from nexo.types.misc import OptPathOrStr
from nexo.types.string import ListOfStrs
from nexo.types.uuid import OptUUID
from nexo.utils.exception import extract_details
from .base import GOOGLE_RESOURCE, GoogleClientManager
from .types import OptionalCredentials


SECRET_MANAGER_RESOURCE = deepcopy(GOOGLE_RESOURCE)
SECRET_MANAGER_RESOURCE.identifiers.append(
    ResourceIdentifier(
        key="secret_manager", name="Secret Manager", slug="secret-manager"
    )
)


class Format(StrEnum):
    BYTES = "bytes"
    STRING = "string"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


FORMAT_TYPE_MAP: Dict[Format, type] = {
    Format.BYTES: bytes,
    Format.STRING: str,
}


ValueT = TypeVar("ValueT", bytes, str)


class Secret(BaseModel, Generic[ValueT]):
    name: Annotated[str, Field(..., description="Secret's name")]
    version: Annotated[str, Field("latest", description="Secret's version")] = "latest"
    value: Annotated[ValueT, Field(..., description="Secret's value")]


class GoogleSecretManager(GoogleClientManager):
    def __init__(
        self,
        log_config: LogConfig,
        *,
        application_context: OptApplicationContext = None,
        credentials: OptionalCredentials = None,
        credentials_path: OptPathOrStr = None,
    ) -> None:
        super().__init__(
            SECRET_MANAGER_RESOURCE.aggregate(),
            SECRET_MANAGER_RESOURCE.aggregate(AggregateField.NAME),
            log_config,
            application_context,
            credentials,
            credentials_path,
        )
        self._client = secretmanager.SecretManagerServiceClient(
            credentials=self._credentials
        )

    def create(
        self,
        name: str,
        value: ValueT,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> SingleDataResponse[Secret[ValueT], None]:
        if not isinstance(value, (bytes, str)):
            raise TypeError("Value type can only either be 'bytes' or 'str'")

        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = CreateResourceOperationAction()

        resource = deepcopy(SECRET_MANAGER_RESOURCE)
        resource.details = {"name": name}

        executed_at = datetime.now(tz=timezone.utc)

        parent = f"projects/{self._credentials.project_id}"
        secret_path = f"{parent}/secrets/{name}"
        # Check if the secret already exists
        try:
            request = secretmanager.GetSecretRequest(name=secret_path)
            self._client.get_secret(request=request)
        except GoogleNotFound:
            # Secret does not exist, create it first
            try:
                secret = secretmanager.Secret(name=name, replication={"automatic": {}})
                request = secretmanager.CreateSecretRequest(
                    parent=parent, secret_id=name, secret=secret
                )
                self._client.create_secret(request=request)
            except Exception as e:
                exc = MaleoExceptionFactory.from_code(
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    details=extract_details(e),
                    operation_type=OperationType.RESOURCE,
                    application_context=self._application_context,
                    operation_id=operation_id,
                    operation_context=self._operation_context,
                    operation_action=operation_action,
                    resource=resource,
                    operation_timestamp=Timestamp.completed_now(executed_at),
                    operation_summary="Unexpected error raised while creating new secret",
                    connection_context=connection_context,
                    authentication=authentication,
                    authorization=authorization,
                    impersonation=impersonation,
                )
                exc.log_operation(self._logger)
                raise exc from e

        # Add a new secret version
        try:
            bytes_value = value.encode() if isinstance(value, str) else value
            payload = secretmanager.SecretPayload(data=bytes_value)
            request = secretmanager.AddSecretVersionRequest(
                parent=secret_path, payload=payload
            )
            self._client.add_secret_version(request=request)

            secret = Secret[ValueT](name=name, version="latest", value=value)
            operation_response = CreateSingleDataResponse[Secret[ValueT], None].new(
                data=secret, metadata=None, other=None
            )
            CreateSingleResourceOperation[Secret[ValueT], None](
                application_context=self._application_context,
                id=operation_id,
                context=self._operation_context,
                action=operation_action,
                resource=resource,
                timestamp=Timestamp.completed_now(executed_at),
                summary=f"Successfully added new secret '{name}' version",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
                response=operation_response,
            ).log(self._logger, LogLevel.INFO)

            return SingleDataResponse[Secret[ValueT], None](
                data=secret,
                metadata=None,
                other=None,
            )

        except Exception as e:
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(e),
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="Unexpected error raised while adding new secret version",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.log_operation(self._logger)
            raise exc from e

    @overload
    def read(
        self,
        format: Literal[Format.BYTES],
        name: str,
        version: str = "latest",
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> SingleDataResponse[Secret[bytes], None]: ...
    @overload
    def read(
        self,
        format: Literal[Format.STRING],
        name: str,
        version: str = "latest",
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> SingleDataResponse[Secret[str], None]: ...
    def read(
        self,
        format: Format,
        name: str,
        version: str = "latest",
        *,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> Union[
        SingleDataResponse[Secret[bytes], None],
        SingleDataResponse[Secret[str], None],
    ]:
        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = ReadResourceOperationAction()

        resource = deepcopy(SECRET_MANAGER_RESOURCE)
        resource.details = {"name": name, "version": version}

        value_type = FORMAT_TYPE_MAP.get(format, None)
        if value_type is None:
            raise ValueError(
                f"Unable to determine secret value type for given format: '{format}'"
            )

        executed_at = datetime.now(tz=timezone.utc)

        # Check if secret exists
        secret_name = f"projects/{self._credentials.project_id}/secrets/{name}"
        try:
            request = secretmanager.GetSecretRequest(name=secret_name)
            self._client.get_secret(request=request)
        except GoogleNotFound as gnf:
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.NOT_FOUND,
                details=gnf.reason,
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary=f"Secret '{secret_name}' not found",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.log_operation(self._logger)
            raise exc from gnf
        except Exception as e:
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(e),
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary=f"Exception raised while ensuring secret '{secret_name}' exists",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.log_operation(self._logger)
            raise exc from e

        # Check if secret's version exists
        secret_version_name = f"{secret_name}/versions/{version}"
        try:
            request = secretmanager.GetSecretVersionRequest(name=secret_version_name)
            self._client.get_secret_version(request=request)
        except GoogleNotFound as gnf:
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.NOT_FOUND,
                details=gnf.reason,
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary=f"Secret's version '{secret_version_name}' not found",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.log_operation(self._logger)
            raise exc from gnf
        except Exception as e:
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(e),
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary=f"Exception raised while ensuring secret's version '{secret_version_name}' exists",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.log_operation(self._logger)
            raise exc from e

        try:
            request = secretmanager.AccessSecretVersionRequest(name=secret_version_name)
            response = self._client.access_secret_version(request=request)

            if format is Format.BYTES:
                value = response.payload.data
            elif format is Format.STRING:
                value = response.payload.data.decode()

            secret = Secret[value_type](name=name, version=version, value=value)
            operation_response = ReadSingleDataResponse[Secret[value_type], None].new(
                data=secret, metadata=None, other=None
            )

            ReadSingleResourceOperation[
                Secret[value_type],
                None,
            ](
                application_context=self._application_context,
                id=operation_id,
                context=self._operation_context,
                action=operation_action,
                resource=resource,
                timestamp=Timestamp.completed_now(executed_at),
                summary=f"Successfully retrieved secret '{name}' with version '{version}'",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
                response=operation_response,
            ).log(self._logger, LogLevel.INFO)

            return SingleDataResponse[Secret[value_type], None](
                data=secret,
                metadata=None,
                other=None,
            )

        except Exception as e:
            exc = MaleoExceptionFactory.from_code(
                ErrorCode.INTERNAL_SERVER_ERROR,
                details=extract_details(e),
                operation_type=OperationType.RESOURCE,
                application_context=self._application_context,
                operation_id=operation_id,
                operation_context=self._operation_context,
                operation_action=operation_action,
                resource=resource,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary=f"Exception raised while accessing secret's version '{secret_version_name}'",
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            )
            exc.log_operation(self._logger)
            raise exc from e
