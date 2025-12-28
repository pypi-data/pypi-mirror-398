from pydantic import BaseModel
from typing import ClassVar

class OutputSpec(BaseModel):
    OUTPUT_FORMATS: ClassVar[list]
    output_format: str | None
    callback: str | None
    def check_output_format(cls, values): ...
    def to_url_path(self) -> str: ...
    @classmethod
    def from_url_path(cls, path: str) -> OutputSpec: ...
