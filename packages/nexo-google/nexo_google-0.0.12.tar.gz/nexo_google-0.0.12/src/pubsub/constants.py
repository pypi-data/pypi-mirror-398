from copy import deepcopy
from nexo.schemas.resource import ResourceIdentifier
from ..base import GOOGLE_RESOURCE


PUBSUB_RESOURCE = deepcopy(GOOGLE_RESOURCE)
PUBSUB_RESOURCE.identifiers.append(
    ResourceIdentifier(key="pubsub", name="Pub/Sub", slug="pubsub")
)
