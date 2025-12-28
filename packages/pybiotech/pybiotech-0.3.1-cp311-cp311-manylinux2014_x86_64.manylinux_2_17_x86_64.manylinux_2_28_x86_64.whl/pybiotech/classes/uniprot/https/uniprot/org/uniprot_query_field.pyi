from pydantic import BaseModel
from typing import Literal

class QueryField(BaseModel):
    id: str
    itemType: Literal['single', 'group', 'sibling_group']
    label: str | None
    term: str | None
    dataType: str | None
    fieldType: str | None
    example: str | None
    regex: str | None
    values: list[dict] | None
    siblings: list['QueryField'] | None
    items: list['QueryField'] | None
    autoComplete: str | None
    autoCompleteQueryTerm: str | None
