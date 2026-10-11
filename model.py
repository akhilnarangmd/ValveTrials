"""
model.py — Data model for the Late-Breaking Valve Trials card system.

A single `Trial` dataclass captures every field in the standardized card
template. Lists default to empty so that ongoing trials (which have no
results yet) can omit them cleanly. Nothing here renders HTML; see
valve_trials.py for the renderer.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


# --- Controlled vocabularies -------------------------------------------------
# Kept as plain strings (not Enums) so the data file reads naturally and a
# clinician editing it doesn't need to import anything.

STATUS = {"published", "results_posted", "ongoing", "terminated", "withdrawn"}

# Result "signal" drives the tone badge (positive / neutral / negative / etc.)
SIGNAL = {"positive", "neutral", "negative", "descriptive", "pending"}

# Primary category drives the coloured spine + grouping. One per trial.
CATEGORIES = [
    "Inoperable / High-Risk AS",
    "Intermediate-Risk AS",
    "Low-Risk AS",
    "Platform Comparison",
    "Asymptomatic / Timing",
    "Moderate AS",
    "Valve-in-Valve / Redo",
    "Bicuspid",
    "Aortic Regurgitation",
    "Frontier / Next-Gen Device",
    # --- Mitral ---
    "Mitral TEER — Primary / Degenerative MR",
    "Mitral TEER — Mixed-Etiology / Feasibility",
    "Mitral TEER — Secondary / Functional MR",
    "Secondary MR — Direct Annuloplasty",
    "Secondary MR — Indirect Annuloplasty",
    "Mitral Chordal Repair",
    "Transcatheter Mitral Replacement (TMVR)",
    "Mitral Valve-in-Valve / Ring / MAC",
    # --- Tricuspid ---
    "Tricuspid TEER",
    "Tricuspid Transcatheter Replacement (TTVR)",
    "Tricuspid Annuloplasty",
    "Tricuspid Heterotopic / Caval",
    "Tricuspid Frontier / Next-Gen Device",
]


@dataclass
class Trial:
    # --- Identity ---
    acronym: str
    full_name: str
    nct: str                       # NCT/ISRCTN id, or "" if none / registry
    category: str                  # one of CATEGORIES (drives colour + filter)
    related_ncts: List[str] = field(default_factory=list)  # other registered cohorts used by a report
    registry_results_posted: bool = False  # independent of peer-reviewed publication status
    tags: List[str] = field(default_factory=list)  # extra chips shown on card

    # --- Status flags (drive badges) ---
    status: str = "published"      # published | results_posted | ongoing | terminated | withdrawn
    signal: str = "descriptive"    # positive | neutral | negative | descriptive | pending
    practice_changing: bool = False
    landmark: bool = False
    evidence_stars: int = 3        # 1..5, 0 = pending/NA

    # --- Headline copy ---
    quick_summary: str = ""        # one-sentence plain-language summary
    takeaway: str = ""             # the big pull-quote / bottom line

    # --- Study overview table ---
    device: str = ""
    intervention: str = "TAVI"
    comparator: str = ""
    population: str = ""
    risk_group: str = ""
    sample_size: str = ""
    enrollment: str = ""
    follow_up: str = ""
    trial_type: str = "Randomized"

    # --- Sidebar quick facts ---
    valve: str = "Aortic"
    disease: str = ""
    procedure: str = "TAVR"

    # --- Detail sections (lists render as bullets) ---
    inclusion: List[str] = field(default_factory=list)
    primary_endpoint: str = ""
    secondary_endpoints: List[str] = field(default_factory=list)
    key_results: List[str] = field(default_factory=list)
    why_matters: str = ""
    pearls: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    # --- Regulatory / guideline / timeline ---
    guideline_acc: str = ""
    guideline_esc: str = ""
    fda_impact: str = ""
    timeline: List[str] = field(default_factory=list)  # "Label: value" strings

    # --- Citation ---
    authors: str = ""
    journal: str = ""
    year: str = ""
    doi: str = ""
    pmid: str = ""
    # Serial follow-ups & subanalyses: list of {"label","citation","doi","pmid"}
    key_papers: List[dict] = field(default_factory=list)

    # --- Curator flag (shown as a caution ribbon when set) ---
    caveat: str = ""               # e.g. "Not a TAVR trial", "Provisional NCT"

    @property
    def slug(self) -> str:
        keep = [c.lower() if c.isalnum() else "-" for c in self.acronym]
        s = "".join(keep)
        while "--" in s:
            s = s.replace("--", "-")
        return s.strip("-") or "trial"

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Trial":
        fields = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in d.items() if k in fields})
