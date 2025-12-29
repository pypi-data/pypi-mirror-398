from pydantic import BaseModel, Field
from typing import Annotated, TypeVar
from nexo.enums.expiration import Expiration


class BaseAdditionalConfig(BaseModel):
    """Base additional configuration class for database."""


OptBaseAdditionalConfig = BaseAdditionalConfig | None
AdditionalConfigT = TypeVar("AdditionalConfigT", bound=OptBaseAdditionalConfig)


class RedisAdditionalConfig(BaseAdditionalConfig):
    ttl: Annotated[
        float | int | Expiration,
        Field(Expiration.EXP_15MN.value, description="Time to live"),
    ] = Expiration.EXP_15MN.value
    base_namespace: Annotated[str, Field(..., description="Base namespace")]
