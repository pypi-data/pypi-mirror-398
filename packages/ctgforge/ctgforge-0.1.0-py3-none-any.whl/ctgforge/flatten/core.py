from ..models.core import TrialCore
from ..models.provenance import ProvenancedValue


def flatten_core(raw: dict) -> TrialCore:
    p = raw.get("protocolSection", {})

    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    conds = p.get("conditionsModule", {})
    arms = p.get("armsInterventionsModule", {})
    sponsor = p.get("sponsorCollaboratorsModule", {})

    trial = TrialCore(
        nct_id=ident.get("nctId"),
        brief_title=ident.get("briefTitle"),
        official_title=ident.get("officialTitle"),
        overall_status=status.get("overallStatus"),
        study_type=design.get("studyType"),
        phase=design.get("phases", []),
        start_date=status.get("startDateStruct", {}).get("date"),
        completion_date=status.get("completionDateStruct", {}).get("date"),
        sponsor=sponsor.get("leadSponsor", {}).get("name"),
        conditions=conds.get("conditions", []),
        interventions=[
            {
                "type": i.get("type"),
                "name": i.get("name"),
            }
            for i in arms.get("interventions", [])
        ],
    )

    # Provenance information
    # TODO: add more fields as needed
    trial.prov["overall_status"] = ProvenancedValue(
        value=trial.overall_status,
        source_module="statusModule",
        source_path="protocolSection.statusModule.overallStatus",
    )

    return trial
