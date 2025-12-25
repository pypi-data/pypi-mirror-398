from collections.abc import Sequence

import pandas as pd

from ..models.core import TrialCore


def to_property_graph(trials: Sequence[TrialCore]) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes = []
    edges = []

    def node(node_id, label, **props):
        nodes.append({"node_id": node_id, "label": label, "props": props})

    def edge(src, rel, dst):
        edges.append({"src": src, "rel": rel, "dst": dst})

    for t in trials:
        tid = f"Trial:{t.nct_id}"
        node(tid, "Trial", **t.model_dump(exclude={"prov"}))

        for c in t.conditions:
            cid = f"Condition:{c.lower()}"
            node(cid, "Condition", name=c)
            edge(tid, "HAS_CONDITION", cid)

        for i in t.interventions:
            name = i.get("name")
            if not name:
                continue
            iid = f"Intervention:{name.lower()}"
            node(iid, "Intervention", **i)
            edge(tid, "HAS_INTERVENTION", iid)

        if t.sponsor:
            sid = f"Sponsor:{t.sponsor.lower()}"
            node(sid, "Sponsor", name=t.sponsor)
            edge(tid, "SPONSORED_BY", sid)

    nodes_df = pd.DataFrame(nodes).drop_duplicates("node_id")
    edges_df = pd.DataFrame(edges)

    return nodes_df, edges_df
