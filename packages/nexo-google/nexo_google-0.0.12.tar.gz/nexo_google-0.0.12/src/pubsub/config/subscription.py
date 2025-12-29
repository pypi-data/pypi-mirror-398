from pydantic import BaseModel, Field
from typing import Annotated, Generic, TypeVar


class SubscriptionConfig(BaseModel):
    id: Annotated[str, Field(..., description="Subscription's ID")]
    max_messages: Annotated[
        int, Field(10, description="Subscription's Max messages")
    ] = 10
    ack_deadline: Annotated[
        int, Field(10, description="Subscription's ACK deadline")
    ] = 10


SubscriptionConfigT = TypeVar("SubscriptionConfigT", bound=SubscriptionConfig)


class SubscriptionsConfig(BaseModel):
    pass


OptSubscriptionsConfig = SubscriptionsConfig | None
SubscriptionsConfigT = TypeVar("SubscriptionsConfigT", bound=OptSubscriptionsConfig)


class SubscriptionsConfigMixin(BaseModel, Generic[SubscriptionsConfigT]):
    subscriptions: SubscriptionsConfigT = Field(..., description="Subscriptions config")
