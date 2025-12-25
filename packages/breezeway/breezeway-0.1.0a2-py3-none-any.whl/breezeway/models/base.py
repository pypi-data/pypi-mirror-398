from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, PrivateAttr


if TYPE_CHECKING:
    from breezeway.breezeway_client import BreezewayClient, BaseBreezewayClient


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

class Paginated[T: BaseBreezewayModel](BaseBreezewayModel):
    limit: int
    page: int
    results: list[T]
    total_pages: int
    total_results: int

    def attach_client(self, client: BaseBreezewayClient) -> Self:
        """
        Attach the BreezewayClient instance to the paginated model.
        """
        super().attach_client(client)
        for result in self.results:
            result.attach_client(client)
        return self
