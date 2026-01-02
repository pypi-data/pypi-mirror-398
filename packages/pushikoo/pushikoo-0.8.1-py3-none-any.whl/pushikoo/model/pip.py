from pydantic import BaseModel


class PipCommandResult(BaseModel):
    target: str
    output: str
