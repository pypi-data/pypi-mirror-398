from typing import Any

from kiarina.lib.cloudflare.auth import CloudflareAuthSettings

from ..._core.models.d1_context import D1Context
from ..._core.operations.query import query
from ..._core.views.result import Result
from ..._settings import D1Settings


class D1Client:
    def __init__(
        self, settings: D1Settings, *, auth_settings: CloudflareAuthSettings
    ) -> None:
        self.ctx: D1Context = D1Context(
            settings=settings,
            auth_settings=auth_settings,
        )

    async def query(self, sql: str, params: list[Any] | None = None) -> Result:
        return await query("async", self.ctx, sql, params)
