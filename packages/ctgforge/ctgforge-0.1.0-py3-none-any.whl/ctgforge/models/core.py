from typing import Any, Union

from pydantic import BaseModel, Field

from .provenance import ProvenancedValue


class TrialCore(BaseModel):
    nct_id: str

    brief_title: Union[str, None] = None
    official_title: Union[str, None] = None

    overall_status: Union[str, None] = None
    phase: list[str] = Field(default_factory=list)
    study_type: Union[str, None] = None

    start_date: Union[str, None] = None
    completion_date: Union[str, None] = None

    sponsor: Union[str, None] = None
    conditions: list[str] = Field(default_factory=list)
    interventions: list[dict[str, Any]] = Field(default_factory=list)

    prov: dict[str, ProvenancedValue] = Field(default_factory=dict)
