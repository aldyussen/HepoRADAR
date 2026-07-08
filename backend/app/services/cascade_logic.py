"""HCV care-cascade stage logic. Pure functions — no DB, no I/O, never throw.

Column reality (checked against loinc_map.py / etl.py before writing this):
ingest only recognizes a liver-function-test panel (AST, ALT, PLT, BILIRUBIN,
ALBUMIN) plus age/sex/date — there is no anti-HCV antibody, HCV RNA/PCR,
genotype, or treatment column anywhere in the CSV ingest path. None of those
LFT analytes are HCV-specific, so proxying cascade stage off them would mean
inventing a signal that isn't there.

The `cascade_event` table (B0) is the real, purpose-built home for this data —
one row per patient per stage transition. Nothing in the CSV ingest pipeline
writes to it yet (that's the honest gap, same spirit as the "lost" definition
falling back to no-repeat-lab): a patient with no cascade_event rows is
"indeterminate", not "unscreened", until an explicit event (manual entry, a
future EHR/FHIR feed, or a screening import) records one.
"""

from collections.abc import Iterable, Sequence

CASCADE_STAGES: tuple[str, ...] = (
    "screened",
    "anti_hcv_positive",
    "rna_tested",
    "treated",
    "svr",
)

INDETERMINATE = "indeterminate"

_STAGE_ORDER = {stage: index for index, stage in enumerate(CASCADE_STAGES)}


def hcv_stage(patient_stages: Iterable[str] | None) -> str:
    """Furthest cascade stage reached, from a patient's cascade_event stage values.

    Missing or unrecognized data -> "indeterminate" (earliest stage, never a throw).
    """
    if not patient_stages:
        return INDETERMINATE
    reached = [stage for stage in patient_stages if stage in _STAGE_ORDER]
    if not reached:
        return INDETERMINATE
    return max(reached, key=_STAGE_ORDER.get)


def reflex_flag(patient_stages: Iterable[str] | None) -> bool:
    """True iff anti-HCV positive with no RNA/PCR test on record — the cascade gap.

    A positive screen followed by treatment/SVR implies RNA testing happened,
    so those are excluded too even if a `rna_tested` event is missing/dirty.
    """
    if not patient_stages:
        return False
    stages = set(patient_stages)
    return "anti_hcv_positive" in stages and not stages.intersection({"rna_tested", "treated", "svr"})


def cascade_funnel(cohort_stages: Sequence[Iterable[str] | None]) -> dict[str, int]:
    """Cumulative funnel: count of patients who reached at least each stage.

    Monotonically non-increasing by construction — a later stage's count is
    always over a subset of the patients who reached an earlier one.
    """
    import pandas as pd

    furthest = pd.Series([hcv_stage(stages) for stages in cohort_stages])
    counts_by_stage = furthest.value_counts()

    funnel: dict[str, int] = {}
    for index, stage in enumerate(CASCADE_STAGES):
        at_or_beyond = CASCADE_STAGES[index:]
        funnel[stage] = int(sum(counts_by_stage.get(s, 0) for s in at_or_beyond))
    return funnel
