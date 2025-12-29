from abc import ABC, abstractmethod
from copy import deepcopy
from google.cloud.pubsub_v1 import PublisherClient
from typing import Generic
from nexo.logging.config import LogConfig
from nexo.schemas.application import OptApplicationContext
from nexo.schemas.google import PublisherHandler
from nexo.schemas.resource import AggregateField, ResourceIdentifier
from nexo.types.misc import OptPathOrStr
from ..base import GoogleClientManager
from ..types import OptionalCredentials
from .config.publisher import PublisherConfigT
from .constants import PUBSUB_RESOURCE


PUBLISHER_RESOURCE = deepcopy(PUBSUB_RESOURCE)
PUBLISHER_RESOURCE.identifiers.append(
    ResourceIdentifier(key="publisher", name="Publisher", slug="publisher")
)


class GooglePublisherManager(GoogleClientManager, Generic[PublisherConfigT], ABC):
    def __init__(
        self,
        config: PublisherConfigT,
        log_config: LogConfig,
        *,
        application_context: OptApplicationContext = None,
        credentials: OptionalCredentials = None,
        credentials_path: OptPathOrStr = None,
    ) -> None:
        super().__init__(
            PUBLISHER_RESOURCE.aggregate(),
            PUBLISHER_RESOURCE.aggregate(AggregateField.NAME),
            log_config,
            application_context,
            credentials,
            credentials_path,
        )
        self.config = config
        self.client = PublisherClient(credentials=self._credentials)

    def topic_path(self, topic) -> str:
        return self.client.topic_path(self.project_id, topic)

    @property
    @abstractmethod
    def heartbeat_publisher(self) -> PublisherHandler:
        "Declare heartbeat publisher"

    @property
    @abstractmethod
    def operation_publisher(self) -> PublisherHandler:
        "Declare operation publisher"

    @property
    @abstractmethod
    def resource_measurement_publisher(self) -> PublisherHandler:
        "Declare resource measurement publisher"
