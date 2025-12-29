import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import ClassVar, Literal, overload
from uuid import UUID
from nexo.client.service import ClientService
from nexo.database.enums import Connection
from nexo.database.utils import build_cache_key
from nexo.enums.cardinality import Cardinality
from nexo.enums.connection import Header
from nexo.logging.enums import LogLevel
from maleo.metadata.constants.organization_type import ORGANIZATION_TYPE_RESOURCE
from maleo.metadata.enums.organization_type import Granularity
from maleo.metadata.mixins.organization_type import is_id_identifier
from maleo.metadata.schemas.organization_type import (
    ReadMultipleParameter,
    ReadSingleParameter,
    StandardOrganizationTypeSchema,
    FullOrganizationTypeSchema,
)
from maleo.metadata.utils.organization_type import get_schema_model
from nexo.schemas.connection import ConnectionContext
from nexo.schemas.exception.factory import MaleoExceptionFactory
from nexo.schemas.operation.action.resource import ReadResourceOperationAction
from nexo.schemas.operation.enums import OperationType, Target
from nexo.schemas.operation.mixins import Timestamp
from nexo.schemas.operation.resource import (
    ReadMultipleResourceOperation,
    ReadSingleResourceOperation,
)
from nexo.schemas.pagination import StrictPagination
from nexo.schemas.resource import Resource, AggregateField
from nexo.schemas.response import (
    MultipleDataResponse,
    ReadMultipleDataResponse,
    SingleDataResponse,
    ReadSingleDataResponse,
)
from nexo.schemas.security.authorization import (
    AnyAuthorization,
    AuthorizationFactory,
)
from nexo.schemas.security.impersonation import OptImpersonation
from nexo.types.dict import OptStrToStrDict
from nexo.utils.merger import merge_dicts
from ..config import ClientConfig


class OrganizationTypeClientService(ClientService[ClientConfig]):
    _resource: ClassVar[Resource] = ORGANIZATION_TYPE_RESOURCE

    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.MULTIPLE],
        granularity: Literal[Granularity.STANDARD],
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadMultipleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadMultipleDataResponse[
        StandardOrganizationTypeSchema, StrictPagination, None
    ]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.MULTIPLE],
        granularity: Literal[Granularity.FULL],
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadMultipleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadMultipleDataResponse[
        FullOrganizationTypeSchema, StrictPagination, None
    ]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.SINGLE],
        granularity: Literal[Granularity.STANDARD],
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadSingleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadSingleDataResponse[StandardOrganizationTypeSchema, None]: ...
    @overload
    async def read(
        self,
        cardinality: Literal[Cardinality.SINGLE],
        granularity: Literal[Granularity.FULL],
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadSingleParameter,
        headers: OptStrToStrDict = None,
    ) -> ReadSingleDataResponse[FullOrganizationTypeSchema, None]: ...
    async def read(
        self,
        cardinality: Cardinality,
        granularity: Granularity,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
        authorization: AnyAuthorization,
        impersonation: OptImpersonation = None,
        parameters: ReadMultipleParameter | ReadSingleParameter,
        headers: OptStrToStrDict = None,
    ) -> (
        ReadMultipleDataResponse[StandardOrganizationTypeSchema, StrictPagination, None]
        | ReadMultipleDataResponse[FullOrganizationTypeSchema, StrictPagination, None]
        | ReadSingleDataResponse[StandardOrganizationTypeSchema, None]
        | ReadSingleDataResponse[FullOrganizationTypeSchema, None]
    ):
        redis_client = self._redis.manager.client.get(Connection.ASYNC)
        data_model_cls = get_schema_model(granularity)

        executed_at = datetime.now(tz=timezone.utc)

        # Define arguments being used in this function
        positional_arguments = [cardinality, granularity]
        keyword_arguments = {
            "authorization": (
                authorization.model_dump(mode="json")
                if authorization is not None
                else None
            ),
            "parameters": parameters.model_dump(mode="json"),
        }

        # Define full function string
        ext = f"({json.dumps(positional_arguments)}|{json.dumps(keyword_arguments)})"

        # Define full cache_key
        cache_key = build_cache_key(ext, namespace=self._namespace)

        if parameters.use_cache:
            # Initialize cache operation context
            operation_context = deepcopy(self._operation_context)
            operation_context.target.type = Target.CACHE

            redis_response_str = await redis_client.get(cache_key)

            if redis_response_str is not None:
                operation_timestamp = Timestamp.completed_now(executed_at)
                if cardinality is Cardinality.MULTIPLE:
                    response = ReadMultipleDataResponse[
                        data_model_cls, StrictPagination, None
                    ].model_validate_json(redis_response_str)
                    operation = ReadMultipleResourceOperation[
                        data_model_cls, StrictPagination, None
                    ](
                        application_context=self._application_context,
                        id=operation_id,
                        context=operation_context,
                        resource=self._resource,
                        timestamp=operation_timestamp,
                        summary=f"Successfully read multiple {granularity} {self._resource.aggregate(AggregateField.NAME, sep=" ").lower()} from cache",
                        connection_context=connection_context,
                        authentication=None,
                        authorization=authorization,
                        impersonation=impersonation,
                        response=response,
                    )
                    operation.log(self._logger, LogLevel.INFO)
                    operation.publish(self._logger, self._publishers)
                elif cardinality is Cardinality.SINGLE:
                    response = ReadSingleDataResponse[
                        data_model_cls, None
                    ].model_validate_json(redis_response_str)
                    operation = ReadSingleResourceOperation[data_model_cls, None](
                        application_context=self._application_context,
                        id=operation_id,
                        context=operation_context,
                        resource=self._resource,
                        timestamp=operation_timestamp,
                        summary=f"Successfully read single {granularity} {self._resource.aggregate(AggregateField.NAME, sep=" ").lower()} from cache",
                        connection_context=connection_context,
                        authentication=None,
                        authorization=authorization,
                        impersonation=impersonation,
                        response=response,
                    )
                    operation.log(self._logger, LogLevel.INFO)
                    operation.publish(self._logger, self._publishers)

                return response  # type: ignore

        operation_context = deepcopy(self._operation_context)
        operation_context.target.type = Target.MICROSERVICE

        async with self._http_client_manager.get() as http_client:
            base_headers = {
                Header.CONTENT_TYPE.value: "application/json",
                Header.X_OPERATION_ID.value: str(operation_id),
            }
            if impersonation is not None:
                base_headers[Header.X_USER_ID.value] = str(impersonation.user_id)
                if impersonation.organization_id is not None:
                    base_headers[Header.X_ORGANIZATION_ID.value] = str(
                        impersonation.organization_id
                    )

            if headers is not None:
                headers = merge_dicts(base_headers, headers)
            else:
                headers = base_headers

            auth = AuthorizationFactory.httpx_auth(
                scheme=authorization.scheme, authorization=authorization.credentials
            )

            base_url = f"{self._config.url}/v1/{self._resource.identifiers[-1].slug}/"
            if isinstance(parameters, ReadMultipleParameter):
                url = base_url
            elif isinstance(parameters, ReadSingleParameter):
                if is_id_identifier(parameters.identifier):
                    url = base_url + str(parameters.identifier.value)
                else:
                    url = (
                        base_url
                        + f"{parameters.identifier.type}/{parameters.identifier.value}"
                    )

            params = parameters.to_query_params()

            response = await http_client.get(
                url, params=params, headers=headers, auth=auth
            )

            operation_timestamp = Timestamp.completed_now(executed_at)

            if response.is_error:
                exc = MaleoExceptionFactory.from_httpx(
                    response,
                    operation_type=OperationType.REQUEST,
                    application_context=self._application_context,
                    operation_id=operation_id,
                    operation_context=operation_context,
                    operation_action=ReadResourceOperationAction(),
                    operation_timestamp=operation_timestamp,
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    logger=self._logger,
                )
                exc.log_and_publish_operation(self._logger, self._publishers)
                raise exc

            if isinstance(parameters, ReadMultipleParameter):
                validated_response = MultipleDataResponse[
                    data_model_cls, StrictPagination, None
                ].model_validate(response.json())
                service_response = ReadMultipleDataResponse[
                    data_model_cls, StrictPagination, None
                ].new(
                    data=validated_response.data,
                    pagination=validated_response.pagination,
                )
                operation = ReadMultipleResourceOperation[
                    data_model_cls, StrictPagination, None
                ](
                    application_context=self._application_context,
                    id=operation_id,
                    context=operation_context,
                    resource=self._resource,
                    timestamp=operation_timestamp,
                    summary=f"Successfully read multiple {granularity} {self._resource.aggregate(AggregateField.NAME, sep=" ").lower()} from microservice",
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=service_response,
                )
                operation.log(self._logger, LogLevel.INFO)
                operation.publish(self._logger, self._publishers)
            elif isinstance(parameters, ReadSingleParameter):
                validated_response = SingleDataResponse[
                    data_model_cls, None
                ].model_validate(response.json())
                service_response = ReadSingleDataResponse[data_model_cls, None].new(
                    data=validated_response.data,
                )
                operation = ReadSingleResourceOperation[data_model_cls, None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=operation_context,
                    resource=self._resource,
                    timestamp=operation_timestamp,
                    summary=f"Successfully read single {granularity} {self._resource.aggregate(AggregateField.NAME, sep=" ").lower()} from microservice",
                    connection_context=connection_context,
                    authentication=None,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=service_response,
                )
                operation.log(self._logger, LogLevel.INFO)
                operation.publish(self._logger, self._publishers)

            return service_response  # type: ignore
