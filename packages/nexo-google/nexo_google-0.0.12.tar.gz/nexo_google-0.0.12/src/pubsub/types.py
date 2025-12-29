from google.cloud.pubsub_v1.subscriber.message import Message
from typing import Awaitable, Callable, Concatenate, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R", bool, Awaitable[bool])
MessageController = Callable[Concatenate[str, Message, P], R]
