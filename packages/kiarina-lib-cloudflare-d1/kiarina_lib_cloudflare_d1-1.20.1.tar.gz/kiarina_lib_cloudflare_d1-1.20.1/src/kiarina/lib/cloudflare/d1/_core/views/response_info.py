from pydantic import BaseModel, ConfigDict


class ResponseInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: int

    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
