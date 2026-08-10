#!/usr/bin/env python3
"""
discover_updates.py — monthly PubMed discovery + JSON updater for the valve-trials site.

WHAT IT DOES (run monthly by GitHub Actions; see .github/workflows/monthly-trial-discovery.yml):
  1. For EVERY published trial in the JSON data files it runs the confidence-scored linker
     (pubmed_linker.py) — including trials that ALREADY have a primary, so follow-up /
     subanalysis papers are discovered, not just missing primaries.
  2. It dedupes each candidate against what the trial already stores (top-level pmid/doi
     AND every key_papers entry), by normalized PMID and DOI.
  3. Anything new at MEDIUM-or-better confidence (any kind: primary, subanalysis; mentions
     optional) is added:
        - a genuinely-missing PRIMARY (HIGH + kind=primary) fills the trial's pmid/doi
        - everything else is appended to key_papers with a real citation + label
  4. It writes the JSON back in place and emits a Markdown report (the PR body).

The heavy PubMed logic lives in pubmed_linker.py (the file you already have); this script
only orchestrates discovery, dedupe, citation formatting, and write-back. The merge logic
is pure and offline-tested via `--selftest` (no network needed).

Design note — the two bugs this fixes vs. the old flow:
  * old batch mode skipped any trial that already had a primary -> follow-ups were never
    discovered.  Here we scan every published trial.
  * old action gate was HIGH + kind==primary only -> subanalyses never surfaced.  Here the
    threshold is MEDIUM+ and every kind is eligible (tune with --threshold / --kinds).
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from typing import Callable, List, Tuple

# Reuse the user's tested scoring/query logic.  Fall back to linker_core (scoring-only,
# used for the offline selftest) when pubmed_linker isn't importable.
try:
    from pubmed_linker import Trial, Candidate, score_candidate, build_queries  # type: ignore
    _HAVE_LINKER = True
except Exception:  # pragma: no cover - exercised only in the sandbox selftest
    from linker_core import Trial, Candidate, score_candidate, build_queries  # type: ignore
    _HAVE_LINKER = False

CONF_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# ---------------------------------------------------------------------------------------
# Citation + label formatting (matches the house style already in key_papers)
# ---------------------------------------------------------------------------------------
_LABEL_RULES = [
    (r"\b(\d+)[- ]year\b", lambda m: f"{m.group(1)}-year"),
    (r"\b(\d+)[- ]month\b", lambda m: f"{m.group(1)}-month"),
    (r"\b(\d+)[- ]day\b", lambda m: f"{m.group(1)}-day"),
    (r"\bcost[- ]effective", lambda m: "Cost-effectiveness"),
    (r"\bquality of life\b|\bkccq\b", lambda m: "Quality of life"),
    (r"\bechocardiograph", lambda m: "Echocardiographic outcomes"),
    (r"\brenal\b|\bliver\b|\bhepatic\b", lambda m: "Renal/liver function"),
    (r"\bsex[- ]|\bgender\b", lambda m: "Sex differences"),
    (r"\bpacemaker\b|\bconduction\b", lambda m: "Conduction/pacemaker"),
    (r"\bbicuspid\b", lambda m: "Bicuspid"),
    (r"\bdurability\b|\bstructural valve\b", lambda m: "Durability"),
    (r"\bendocarditis\b", lambda m: "Endocarditis"),
]


def derive_label(cand: "Candidate") -> str:
    t = (cand.title or "").lower()
    for pat, fn in _LABEL_RULES:
        m = re.search(pat, t)
        if m:
            return fn(m)
    # fall back to a short slug of the title
    words = re.sub(r"[^a-zA-Z0-9 ]", "", cand.title or "").split()
    return " ".join(words[:5]) if words else "Follow-up"


def _first_author_display(cand: "Candidate") -> str:
    if not cand.authors:
        return ""
    a = cand.authors[0].strip()
    return a  # already "Surname II" from efetch


def format_citation(cand: "Candidate") -> str:
    """Build 'Surname II, et al. Journal Year;Vol(Issue):Pages.' — omit empty parts."""
    author = _first_author_display(cand)
    lead = f"{author}, et al." if author else ""
    journal = (cand.journal or "").strip()
    year = (cand.year or "").strip()
    vip = ""
    if cand.volume:
        vip = cand.volume
        if cand.issue:
            vip += f"({cand.issue})"
        if cand.pages:
            vip += f":{cand.pages}"
    tail = journal
    if year:
        tail = f"{tail} {year}".strip()
    if vip:
        tail = f"{tail};{vip}"
    cite = " ".join(x for x in [lead, tail] if x).strip()
    if cite and not cite.endswith("."):
        cite += "."
    return cite or (cand.title or "").strip()


# ---------------------------------------------------------------------------------------
# Identity / dedupe helpers
# ---------------------------------------------------------------------------------------
def norm_pmid(p) -> str:
    return re.sub(r"\D", "", str(p or ""))


def norm_doi(d) -> str:
    d = str(d or "").strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d


def existing_ids(row: dict) -> Tuple[set, set]:
    pmids, dois = set(), set()
    if row.get("pmid"):
        pmids.add(norm_pmid(row["pmid"]))
    if row.get("doi"):
        dois.add(norm_doi(row["doi"]))
    for kp in row.get("key_papers", []) or []:
        if kp.get("pmid"):
            pmids.add(norm_pmid(kp["pmid"]))
        if kp.get("doi"):
            dois.add(norm_doi(kp["doi"]))
    pmids.discard("")
    dois.discard("")
    return pmids, dois


def trial_from_row(row: dict) -> "Trial":
    return Trial(
        acronym=row.get("acronym", ""), nct=row.get("nct", "") or "",
        authors=row.get("authors", ""), journal=row.get("journal", ""),
        year=row.get("year", ""), device=row.get("device", ""),
        valve=row.get("valve", ""), disease=row.get("disease", ""),
        procedure=row.get("procedure", ""), sample_size=row.get("sample_size", ""),
    )


# ---------------------------------------------------------------------------------------
# Live candidate gathering (network).  Injected as a function so merge() is testable.
# ---------------------------------------------------------------------------------------
def make_live_gatherer(client, retmax: int = 25):
    """Return gather(trial) -> list[(Candidate, scored_dict)] using PubMed E-utilities."""
    def gather(trial: "Trial"):
        seen, cands = set(), []
        for _strategy, term in build_queries(trial):
            try:
                pmids = [p for p in client.esearch(term, retmax=retmax) if p not in seen]
            except Exception as e:  # keep going on a single-query failure
                sys.stderr.write(f"  ! esearch failed for {trial.acronym} [{term}]: {e}\n")
                continue
            seen.update(pmids)
            try:
                cands += client.efetch(pmids)
            except Exception as e:
                sys.stderr.write(f"  ! efetch failed for {trial.acronym}: {e}\n")
        return [(c, score_candidate(trial, c)) for c in cands]
    return gather


# ---------------------------------------------------------------------------------------
# The pure merge step: decide what to add.  Returns list of change records.
# ---------------------------------------------------------------------------------------
def merge_new_papers(
    data: List[dict],
    gather: Callable[["Trial"], List[Tuple["Candidate", dict]]],
    min_conf: str = "MEDIUM",
    kinds=("primary", "subanalysis"),
    published_only: bool = True,
) -> List[dict]:
    changes: List[dict] = []
    min_rank = CONF_RANK[min_conf]
    for row in data:
        if published_only and row.get("status") != "published":
            continue
        trial = trial_from_row(row)
        pmids, dois = existing_ids(row)
        pairs = gather(trial)
        # rank best-first so a primary fill uses the strongest candidate
        pairs.sort(key=lambda cs: cs[1].get("score", 0), reverse=True)
        for cand, sc in pairs:
            if CONF_RANK.get(sc.get("confidence", "LOW"), 0) < min_rank:
                continue
            if sc.get("kind") not in kinds:
                continue
            np_, nd_ = norm_pmid(cand.pmid), norm_doi(cand.doi)
            if (np_ and np_ in pmids) or (nd_ and nd_ in dois):
                continue  # already have it
            # record + mutate
            is_missing_primary = (not row.get("pmid") and not row.get("doi")
                                  and sc.get("kind") == "primary" and sc.get("confidence") == "HIGH")
            entry = {
                "label": derive_label(cand),
                "citation": format_citation(cand),
                "doi": norm_doi(cand.doi),
                "pmid": norm_pmid(cand.pmid),
            }
            if is_missing_primary:
                row["pmid"] = norm_pmid(cand.pmid)
                if cand.doi:
                    row["doi"] = norm_doi(cand.doi)
                target = "primary"
            else:
                row.setdefault("key_papers", [])
                row["key_papers"].append(entry)
                target = "key_papers"
            if np_:
                pmids.add(np_)
            if nd_:
                dois.add(nd_)
            changes.append({
                "trial": row.get("acronym", ""), "nct": row.get("nct", ""),
                "target": target, "kind": sc.get("kind"),
                "confidence": sc.get("confidence"), "score": sc.get("score"),
                "pmid": entry["pmid"], "doi": entry["doi"],
                "label": entry["label"], "citation": entry["citation"],
                "title": cand.title,
            })
    return changes


# ---------------------------------------------------------------------------------------
# Report (PR body)
# ---------------------------------------------------------------------------------------
def write_report(changes: List[dict], path: str, files: List[str]) -> None:
    lines = ["# Monthly trial-literature update\n"]
    if not changes:
        lines.append("No new papers found this run. ✅\n")
        open(path, "w").write("\n".join(lines))
        return
    from collections import defaultdict
    by_trial = defaultdict(list)
    for c in changes:
        by_trial[c["trial"]].append(c)
    n_prim = sum(1 for c in changes if c["target"] == "primary")
    lines.append(f"**{len(changes)} new paper(s)** across **{len(by_trial)} trial(s)** "
                 f"from `{', '.join(files)}`.\n")
    if n_prim:
        lines.append(f"- {n_prim} filled a missing **primary** reference\n")
    lines.append(f"- {len(changes) - n_prim} added to **key_papers** (follow-ups / subanalyses)\n")
    lines.append("\nReview the entries below, then **merge to publish** (or edit/close to reject).\n")
    for trial in sorted(by_trial):
        lines.append(f"\n## {trial}")
        for c in sorted(by_trial[trial], key=lambda x: -(x["score"] or 0)):
            tgt = "**PRIMARY**" if c["target"] == "primary" else c["label"]
            lines.append(
                f"- {tgt} — {c['confidence']} ({c['score']}), {c['kind']} — "
                f"PMID {c['pmid'] or '—'} · doi:{c['doi'] or '—'}  \n"
                f"  {c['citation']}"
            )
    open(path, "w").write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------------------
# Offline selftest — proves dedupe, primary-fill, citation & label without network
# ---------------------------------------------------------------------------------------
def _selftest() -> int:
    # a trial that already has a primary + one existing follow-up (by DOI, empty pmid)
    data = [{
        "acronym": "CLASP IID", "nct": "NCT03706833", "status": "published",
        "authors": "Lim DS, Smith RL, Gillam LD, et al.",
        "journal": "JACC: Cardiovascular Interventions", "year": "2022",
        "device": "Edwards PASCAL", "valve": "Mitral", "procedure": "TEER",
        "disease": "Primary (degenerative) mitral regurgitation",
        "sample_size": "180 (117 PASCAL / 63 MitraClip)",
        "pmid": "36121247", "doi": "10.1016/j.jcin.2022.09.005",
        "key_papers": [
            {"label": "1-year", "citation": "Zahr F, et al. JACC Cardiovasc Interv 2023;16(23):2803-2816.",
             "doi": "10.1016/j.jcin.2023.10.002", "pmid": ""},
        ],
    }]
    new_sub = Candidate(
        pmid="42233921", doi="10.1016/j.jcmg.2026.04.005",
        title="Impact of Residual Mitral Regurgitation and Gradient After M-TEER: 1-Year Outcomes From the CLASP IID Trial",
        abstract="One-year outcomes from the randomized CLASP IID trial were analyzed.",
        authors=["Narang A", "Hausleiter J", "Lim DS"],
        journal="JACC Cardiovasc Imaging", year="2026", volume="19", issue="6", pages="700-712",
        pubtypes=["journal article", "multicenter study"], nct_accessions=["NCT03706833"])
    dup_by_doi = Candidate(  # same as existing 1-year follow-up -> must be skipped
        pmid="", doi="10.1016/j.jcin.2023.10.002", title="Should be skipped (dup DOI)",
        authors=["Zahr F"], journal="JACC Cardiovasc Interv", year="2023",
        pubtypes=["journal article"], nct_accessions=["NCT03706833"])
    dup_by_pmid = Candidate(  # same as stored primary -> must be skipped
        pmid="36121247", doi="", title="Should be skipped (dup PMID)",
        authors=["Lim DS"], journal="JACC Cardiovasc Interv", year="2022",
        pubtypes=["randomized controlled trial"], nct_accessions=["NCT03706833"])

    def fake_gather(trial):
        return [(c, score_candidate(trial, c)) for c in (new_sub, dup_by_doi, dup_by_pmid)]

    changes = merge_new_papers(data, fake_gather, min_conf="MEDIUM")
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS" if cond else "FAIL"), msg)
        ok = ok and cond

    check(len(changes) == 1, f"exactly one new paper added (got {len(changes)})")
    if changes:
        c = changes[0]
        check(c["pmid"] == "42233921", "the new 2026 subanalysis is the one added")
        check(c["target"] == "key_papers", "added to key_papers (not primary — trial already had one)")
        check(c["label"] == "1-year", f"label derived as '1-year' (got '{c['label']}')")
        check(c["citation"].startswith("Narang A, et al. JACC Cardiovasc Imaging 2026;19(6):700-712"),
              f"citation formatted correctly (got '{c['citation']}')")
    check(len(data[0]["key_papers"]) == 2, "no duplicates written (still 2 key_papers)")
    print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------
def _cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", nargs="+", default=["trials_1.json", "trials_tricuspid_1.json"],
                    help="trials JSON data files to scan and update in place")
    ap.add_argument("--threshold", choices=["LOW", "MEDIUM", "HIGH"], default="MEDIUM",
                    help="minimum confidence to add/notify (default MEDIUM)")
    ap.add_argument("--kinds", nargs="+", default=["primary", "subanalysis"],
                    help="candidate kinds to add (default: primary subanalysis; add 'mention' to include)")
    ap.add_argument("--report", default="discovery_report.md", help="PR-body markdown output path")
    ap.add_argument("--retmax", type=int, default=25, help="max PubMed hits per query strategy")
    ap.add_argument("--selftest", action="store_true", help="run offline logic tests (no network)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if not _HAVE_LINKER:
        sys.stderr.write("ERROR: pubmed_linker.py not importable — cannot run live discovery.\n")
        return 2

    from pubmed_linker import PubMedClient  # noqa: import here so selftest needs no network deps
    client = PubMedClient(api_key=os.environ.get("NCBI_API_KEY"),
                          email=os.environ.get("NCBI_EMAIL", ""))
    gather = make_live_gatherer(client, retmax=args.retmax)

    all_changes: List[dict] = []
    for path in args.files:
        if not os.path.exists(path):
            sys.stderr.write(f"skip (not found): {path}\n")
            continue
        data = json.load(open(path, encoding="utf-8"))
        changes = merge_new_papers(data, gather, min_conf=args.threshold, kinds=tuple(args.kinds))
        if changes:
            json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        for c in changes:
            c["_file"] = path
        all_changes += changes
        print(f"{path}: {len(changes)} new paper(s)")

    write_report(all_changes, args.report, args.files)
    # emit a machine-readable count for the workflow
    print(f"::notice::discovery added {len(all_changes)} new paper(s)")
    open("discovery_count.txt", "w").write(str(len(all_changes)))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())