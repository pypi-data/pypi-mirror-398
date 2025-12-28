from pydantic import BaseModel, ConfigDict

from .query_result import QueryResult
from .response_info import ResponseInfo


class Result(BaseModel):
    model_config = ConfigDict(extra="allow")

    success: bool

    result: list[QueryResult]

    errors: list[ResponseInfo]

    messages: list[ResponseInfo]

    @property
    def first(self) -> QueryResult:
        if not self.result:
            raise ValueError("No results available")

        return self.result[0]

    def raise_for_status(self) -> None:
        if not self.success:
            error_messages = "; ".join(str(error) for error in self.errors)
            raise RuntimeError(f"Query failed: {error_messages}")
