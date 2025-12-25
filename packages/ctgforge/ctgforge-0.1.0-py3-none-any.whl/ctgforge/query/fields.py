from collections.abc import Iterable
from typing import Any

from .expr import Term
from .specs import FieldSpec


class Field:
    def __init__(self, spec: FieldSpec):
        self.spec = spec

    def eq(self, value: Any) -> Term:
        return Term(self.spec, "eq", value)

    def contains(self, value: str) -> Term:
        return Term(self.spec, "contains", value)

    def in_(self, values: Iterable[Any]) -> Term:
        return Term(self.spec, "in", list(values))


class Fields:
    """
    Core fields for clinical trial queries.
    """

    condition = Field(FieldSpec("condition", kind="query", param="query.cond"))
    sponsor = Field(FieldSpec("sponsor", kind="query", param="query.spons"))
    intervention = Field(FieldSpec("intervention", kind="query", param="query.intr"))
    title = Field(FieldSpec("title", kind="query", param="query.titles"))

    status = Field(FieldSpec("status", kind="filter_list", param="filter.overallStatus"))

    # Phase is not a dedicated filter param in the "key parameters" lists,
    # but CTG supports advanced filter query strings (AREA[...]) via filter.advanced.
    phase = Field(FieldSpec("phase", kind="filter_advanced", param="filter.advanced", area="Phase"))

    drug = Field(
        FieldSpec(
            "drug", kind="filter_advanced", param="filter.advanced", area="InterventionNameSearch"
        )
    )


F = Fields()
