from __future__ import annotations
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, PrivateAttr

from breezeway.breezeway_client import BaseBreezewayClient

if TYPE_CHECKING:
    from breezeway import BreezewayClient


class BaseBreezewayModel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
        frozen=True
    )
    _client: BreezewayClient | None = PrivateAttr()

    def attach_client(self, client: BaseBreezewayClient) -> Self:
        """
        Attach the BreezewayClient instance to the model.
        """
        self.__setattr__('_client', client)
        return self
