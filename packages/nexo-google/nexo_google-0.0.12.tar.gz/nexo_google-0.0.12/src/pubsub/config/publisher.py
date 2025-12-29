from pydantic import BaseModel, Field
from typing import Annotated, Generic, TypeVar


class TopicConfig(BaseModel):
    id: str = Field(..., description="Topic's Id")


DEFAULT_HEARTBEAT_TOPIC_CONFIG = TopicConfig(id="heartbeat")
DEFAULT_GENERAL_OPERATION_TOPIC_CONFIG = TopicConfig(id="operation")
DEFAULT_DATABASE_OPERATION_TOPIC_CONFIG = TopicConfig(id="database-operation")
DEFAULT_REQUEST_OPERATION_TOPIC_CONFIG = TopicConfig(id="request-operation")
DEFAULT_RESOURCE_OPERATION_TOPIC_CONFIG = TopicConfig(id="resource-operation")
DEFAULT_SYSTEM_OPERATION_TOPIC_CONFIG = TopicConfig(id="system-operation")
DEFAULT_RESOURCE_MEASUREMENT_TOPIC_CONFIG = TopicConfig(id="resource-measurement")


class OperationTopicsConfig(BaseModel):
    general: Annotated[
        TopicConfig,
        Field(
            DEFAULT_GENERAL_OPERATION_TOPIC_CONFIG,
            description="Operation topic config",
        ),
    ] = DEFAULT_GENERAL_OPERATION_TOPIC_CONFIG
    database: Annotated[
        TopicConfig,
        Field(
            DEFAULT_DATABASE_OPERATION_TOPIC_CONFIG,
            description="Database operation topic config",
        ),
    ] = DEFAULT_DATABASE_OPERATION_TOPIC_CONFIG
    request: Annotated[
        TopicConfig,
        Field(
            DEFAULT_REQUEST_OPERATION_TOPIC_CONFIG,
            description="Request operation topic config",
        ),
    ] = DEFAULT_REQUEST_OPERATION_TOPIC_CONFIG
    resource: Annotated[
        TopicConfig,
        Field(
            DEFAULT_RESOURCE_OPERATION_TOPIC_CONFIG,
            description="Resource operation topic config",
        ),
    ] = DEFAULT_RESOURCE_OPERATION_TOPIC_CONFIG
    system: Annotated[
        TopicConfig,
        Field(
            DEFAULT_SYSTEM_OPERATION_TOPIC_CONFIG,
            description="System operation topic config",
        ),
    ] = DEFAULT_SYSTEM_OPERATION_TOPIC_CONFIG


class ResourceTopicsConfig(BaseModel):
    measurement: Annotated[
        TopicConfig,
        Field(
            DEFAULT_RESOURCE_MEASUREMENT_TOPIC_CONFIG,
            description="Resource measurement topics config",
        ),
    ] = DEFAULT_RESOURCE_MEASUREMENT_TOPIC_CONFIG


class InfraTopicsConfig(BaseModel):
    heartbeat: Annotated[
        TopicConfig,
        Field(
            DEFAULT_HEARTBEAT_TOPIC_CONFIG,
            description="Heartbeat topic config",
        ),
    ] = DEFAULT_HEARTBEAT_TOPIC_CONFIG
    resource: Annotated[
        ResourceTopicsConfig,
        Field(ResourceTopicsConfig(), description="Resource's topics config"),
    ] = ResourceTopicsConfig()


class TopicsConfig(BaseModel):
    infra: Annotated[
        InfraTopicsConfig,
        Field(InfraTopicsConfig(), description="Infra's topics config"),
    ] = InfraTopicsConfig()
    operation: Annotated[
        OperationTopicsConfig,
        Field(
            OperationTopicsConfig(),
            description="Operation's topics config",
        ),
    ] = OperationTopicsConfig()


TopicsConfigT = TypeVar("TopicsConfigT", bound=TopicsConfig)


class PublisherConfig(BaseModel, Generic[TopicsConfigT]):
    topics: TopicsConfigT = Field(..., description="Topics config")


PublisherConfigT = TypeVar("PublisherConfigT", bound=PublisherConfig)


class PublisherConfigMixin(BaseModel, Generic[PublisherConfigT]):
    publisher: PublisherConfigT = Field(..., description="Publisher config")
