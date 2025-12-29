from pydantic import BaseModel, Field
from typing import Generic
from .publisher import PublisherConfigT, PublisherConfigMixin
from .subscription import SubscriptionsConfigT, SubscriptionsConfigMixin


class PubSubConfig(
    SubscriptionsConfigMixin[SubscriptionsConfigT],
    PublisherConfigMixin[PublisherConfigT],
    BaseModel,
    Generic[PublisherConfigT, SubscriptionsConfigT],
):
    pass


class PubSubConfigMixin(BaseModel, Generic[PublisherConfigT, SubscriptionsConfigT]):
    pubsub: PubSubConfig[PublisherConfigT, SubscriptionsConfigT] = Field(
        ..., description="PubSub config"
    )
