#!/usr/bin/env python3
"""Fast, offline checks for the public trial catalog.

Run before deploying. Bibliographic identity is checked separately against
PubMed/ClinicalTrials.gov during editorial review; this catches local regressions.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from model import CATEGORIES, SIGNAL, STATUS, Trial

HERE = Path(__file__).resolve().parent


def validate() -> list[str]:
    errors = []
    records = []
    for path in sorted(HERE.glob("trials*.json")):
        rows = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            errors.append(f"{path.name}: expected a list")
            continue
        for number, row in enumerate(rows, 1):
            where = f"{path.name}[{number}]"
            if not isinstance(row, dict):
                errors.append(f"{where}: expected an object")
                continue
            records.append((where, row))
            for field in ("acronym", "full_name", "category", "valve"):
                if not row.get(field):
                    errors.append(f"{where}: missing {field}")
            if row.get("status") not in STATUS:
                errors.append(f"{where}: invalid status {row.get('status')!r}")
            if row.get("signal") not in SIGNAL:
                errors.append(f"{where}: invalid signal {row.get('signal')!r}")
            if row.get("category") not in CATEGORIES:
                errors.append(f"{where}: invalid category {row.get('category')!r}")
            if row.get("valve") not in ("Aortic", "Mitral", "Tricuspid"):
                errors.append(f"{where}: invalid valve {row.get('valve')!r}")
            if path.name == "trials_tricuspid.json" and row.get("valve") != "Tricuspid":
                errors.append(f"{where}: companion file must contain tricuspid trials")
            if path.name == "trials.json" and row.get("valve") == "Tricuspid":
                errors.append(f"{where}: tricuspid trial belongs in companion file")
            nct = row.get("nct", "")
            if nct and not re.fullmatch(r"(?:NCT\d{8}|ISRCTN\d{8})", nct):
                errors.append(f"{where}: malformed registry identifier {nct!r}")
            pmid = row.get("pmid", "")
            if pmid and not re.fullmatch(r"\d+", pmid):
                errors.append(f"{where}: malformed primary PMID {pmid!r}")
            if row.get("doi") and not re.match(r"^10\.\d{4,9}/\S+$", row["doi"], re.I):
                errors.append(f"{where}: malformed primary DOI {row['doi']!r}")
            if any("DRAFT" in str(row.get(k, "")).upper() for k in ("acronym", "quick_summary", "takeaway")):
                errors.append(f"{where}: draft placeholder in public data")
            paper_ids = []
            for p in row.get("key_papers", []):
                if not isinstance(p, dict):
                    errors.append(f"{where}: key paper is not an object")
                    continue
                if p.get("pmid"):
                    paper_ids.append(p["pmid"])
                if p.get("pmid") and p["pmid"] == pmid:
                    errors.append(f"{where}: primary paper duplicated in follow-ups")
            if len(paper_ids) != len(set(paper_ids)):
                errors.append(f"{where}: duplicate follow-up PMID")
    names = Counter(row.get("acronym", "").casefold() for _, row in records)
    slugs = Counter(Trial.from_dict(row).slug for _, row in records)
    for label, counts in (("acronym", names), ("slug", slugs)):
        for value, number in counts.items():
            if value and number > 1:
                errors.append(f"duplicate {label}: {value!r} ({number} entries)")
    primary_owner = {row.get("pmid"): row.get("acronym") for _, row in records if row.get("pmid")}
    for where, row in records:
        for paper in row.get("key_papers", []):
            if not isinstance(paper, dict):
                continue
            other = primary_owner.get(paper.get("pmid"))
            if other and other != row.get("acronym"):
                errors.append(f"{where}: follow-up PMID is the primary paper for {other}")
    return errors


if __name__ == "__main__":
    problems = validate()
    for problem in problems:
        print("ERROR:", problem)
    print(f"Data validation: {'FAILED' if problems else 'PASS'} ({len(problems)} issue(s))")
    raise SystemExit(bool(problems))
