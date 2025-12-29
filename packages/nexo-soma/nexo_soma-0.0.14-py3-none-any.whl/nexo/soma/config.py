from pydantic import BaseModel
from typing import Generic, TypeVar
from nexo.client.config import OptClientConfigsT, ClientConfigsMixin
from nexo.database.config import (
    DatabaseConfigsT,
    DatabaseConfigsMixin,
)
from nexo.google.pubsub.config import PubSubConfigMixin
from nexo.google.pubsub.config.publisher import PublisherConfigT
from nexo.google.pubsub.config.subscription import SubscriptionsConfigT
from nexo.infra.config import InfraConfigMixin
from nexo.middlewares.config import MiddlewareConfigMixin


class ApplicationConfig(
    PubSubConfigMixin[PublisherConfigT, SubscriptionsConfigT],
    MiddlewareConfigMixin,
    InfraConfigMixin,
    DatabaseConfigsMixin[DatabaseConfigsT],
    ClientConfigsMixin[OptClientConfigsT],
    BaseModel,
    Generic[
        OptClientConfigsT, DatabaseConfigsT, PublisherConfigT, SubscriptionsConfigT
    ],
):
    pass


ApplicationConfigT = TypeVar("ApplicationConfigT", bound=ApplicationConfig)
