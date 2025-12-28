from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QueryResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool = False

    meta: dict[str, Any] = Field(default_factory=dict)

    results: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self.results
