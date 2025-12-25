from collections.abc import Sequence

import pandas as pd

from ..models.core import TrialCore


def to_dataframe(trials: Sequence[TrialCore]) -> pd.DataFrame:
    rows = []
    for t in trials:
        row = t.model_dump(exclude={"prov"})
        # Flatten interventions list of dicts into a string representation
        row["interventions"] = "; ".join(f"{i['type']}: {i['name']}" for i in t.interventions)
        rows.append(row)
    return pd.DataFrame(rows)
