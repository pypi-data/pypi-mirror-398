import datetime
from typing import Any, Literal

from pydantic import BaseModel


class YASLBaseModel(BaseModel):
    def __repr__(self) -> str:
        fields = self.model_dump()  # For Pydantic v2; use self.dict() for v1
        return f"{self.__class__.__name__}({fields})"


# --- YASL Pydantic Models ---
class Enumeration(YASLBaseModel):
    # name: str
    description: str | None = None
    values: list[str]

    model_config = {"extra": "forbid"}


class Property(YASLBaseModel):
    # name: str
    type: str
    description: str | None = None
    presence: Literal["required", "preferred", "optional"] | None = "optional"
    unique: bool | None = False
    default: Any | None = None

    # list constraints
    list_min: int | None = None
    list_max: int | None = None

    # numeric constraints
    gt: float | None = None
    ge: float | None = None
    lt: float | None = None
    le: float | None = None
    exclude: list[float] | None = None
    multiple_of: float | None = None
    whole_number: bool | None = False

    # string constraints
    str_min: int | None = None
    str_max: int | None = None
    str_regex: str | None = None

    # date / time constraints
    before: datetime.date | datetime.datetime | datetime.time | None = None
    after: datetime.date | datetime.datetime | datetime.time | None = None

    # path constraints
    path_exists: bool | None = None
    is_dir: bool | None = None
    is_file: bool | None = None
    file_ext: list[str] | None = None

    # url constraints
    url_base: str | None = None
    url_protocols: list[str] | None = None
    url_reachable: bool | None = False

    # any constraints
    any_of: list[str] | None = None

    # ref constraints
    no_ref_check: bool | None = None

    model_config = {"extra": "forbid"}


class IfThen(YASLBaseModel):
    eval: str
    value: list[str]
    present: list[str]
    absent: list[str]

    model_config = {"extra": "forbid"}


class Validator(YASLBaseModel):
    only_one: list[str] | None = None
    at_least_one: list[str] | None = None
    if_then: list[IfThen] | None = None

    model_config = {"extra": "forbid"}


class TypeDef(YASLBaseModel):
    # name: str
    namespace: str | None = None
    description: str | None = None
    properties: dict[str, Property]
    validators: Validator | None = None

    model_config = {"extra": "forbid"}


class YaslItem(YASLBaseModel):
    description: str | None = None
    enums: dict[str, Enumeration] | None = None
    types: dict[str, TypeDef] | None = None
    model_config = {"extra": "forbid"}


class YaslRoot(YASLBaseModel):
    imports: list[str] | None = None
    metadata: dict[str, Any] | None = None
    definitions: dict[str, YaslItem] | None = None
    model_config = {"extra": "forbid"}
