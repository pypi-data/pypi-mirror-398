from dataclasses import dataclass
from typing import Literal, Optional

FieldKind = Literal["query", "filter_list", "filter_advanced"]


@dataclass(frozen=True)
class FieldSpec:
    key: str  # the DSL name (condition/sponsor/...)
    kind: FieldKind
    param: str  # e.g. "query.cond" or "filter.overallStatus"

    # for advanced filters (AREA[...]) or expert search:
    area: Optional[str] = None  # e.g. "Phase" (field) or "ConditionSearch" (area)
