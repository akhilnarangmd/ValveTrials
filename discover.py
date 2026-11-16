#!/usr/bin/env python3
"""
discover.py — monthly PubMed sweep for NEW transcatheter valve-trial papers.

Flow:  broad PubMed search (recent window)  ->  fetch + score with pubmed_linker  ->
        drop anything already in the database / LOW confidence / reviews & mentions  ->
        for each surviving HIGH hit, route + apply with proposer and print its PMID.

The GitHub Action then opens ONE pull request PER surviving PMID (capped), so you review
and Merge=approve.  A hard --max cap means a noisy PubMed month can never flood you.

Free: uses only PubMed E-utilities (no keys required; NCBI_API_KEY optional for speed).
Live fetch needs internet -> runs in CI, not in a network-restricted sandbox.
The selection/dedupe logic is pure-Python and unit-tested (`--selftest`).
"""
from __future__ import annotations

import json
import os
import sys

from pubmed_linker import PubMedClient, Trial, score_candidate
from proposer import route, apply_proposal, _load_all

# Broad but targeted: valve + transcatheter context.  Tuned to favour trial reports.
DEFAULT_QUERY = (
    '("tricuspid valve"[tiab] OR "mitral valve"[tiab] OR "aortic valve"[tiab]) '
    'AND (transcatheter[tiab] OR "edge-to-edge"[tiab] OR TEER[tiab] OR TAVR[tiab] '
    'OR TAVI[tiab] OR TMVR[tiab] OR TTVR[tiab] OR annuloplasty[tiab]) '
    'AND (trial[tiab] OR "single-arm"[tiab] OR feasibility[tiab] OR pivotal[tiab] '
    'OR randomized[tiab] OR registry[tiab] OR outcomes[tiab]) '
    'AND hasabstract '
    'NOT (review[pt] OR editorial[pt] OR comment[pt] OR "meta-analysis"[pt] '
    'OR "systematic review"[pt] OR "case reports"[pt])'
)


def _trial_from_row(row: dict) -> Trial:
    return Trial(acronym=row.get("acronym", ""), nct=row.get("nct", ""),
                 authors=row.get("authors", ""), journal=row.get("journal", ""),
                 year=row.get("year", ""), device=row.get("device", ""),
                 valve=row.get("valve", ""), disease=row.get("disease", ""),
                 procedure=row.get("procedure", ""), sample_size=row.get("sample_size", ""))


def known_pmids(store: dict) -> set:
    """Every PMID already represented -- as a trial primary or an attached follow-up."""
    out = set()
    for rows in store.values():
        for t in rows:
            if t.get("pmid"):
                out.add(t["pmid"])
            for p in t.get("key_papers", []):
                if p.get("pmid"):
                    out.add(p["pmid"])
    return out


def best_score_for(cand, store: dict) -> dict:
    """Score a candidate against the closest existing trial (by NCT) if any, else generically.
    This lets an ambiguous acronym be corroborated by a matching trial's author/device."""
    parent = None
    by_nct = {t["nct"].upper(): t for rows in store.values() for t in rows if t.get("nct")}
    for nct in cand.nct_accessions:
        if nct.upper() in by_nct:
            parent = by_nct[nct.upper()]
            break
    trial = _trial_from_row(parent) if parent else Trial(
        acronym=(cand.title.split(":")[0][:24] if cand.title else ""),
        nct=cand.nct_accessions[0] if cand.nct_accessions else "")
    return score_candidate(trial, cand)


def select(cands, store: dict, min_conf="HIGH") -> list:
    """Return (pmid, decision, score) for hits worth proposing, newest-strongest first."""
    known = known_pmids(store)
    all_trials = [t for rows in store.values() for t in rows]
    order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    keep = []
    for c in cands:
        if not c.pmid or c.pmid in known:
            continue
        s = best_score_for(c, store)
        if order[s["confidence"]] < order[min_conf]:
            continue
        if s["kind"] == "mention":
            continue
        decision = route(c, all_trials)
        if decision["action"] == "DUPLICATE":
            continue
        keep.append({"pmid": c.pmid, "score": s["score"], "confidence": s["confidence"],
                     "kind": s["kind"], "action": decision["action"],
                     "parent": decision.get("parent"), "title": c.title})
    keep.sort(key=lambda r: r["score"], reverse=True)
    return keep


def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Monthly PubMed discovery of new valve-trial papers.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--files", nargs="*", default=["trials.json", "trials_tricuspid.json"])
    ap.add_argument("--query", default=DEFAULT_QUERY)
    ap.add_argument("--days", type=int, default=45, help="PubMed recency window")
    ap.add_argument("--retmax", type=int, default=80)
    ap.add_argument("--min-confidence", default="HIGH", choices=["HIGH", "MEDIUM", "LOW"])
    ap.add_argument("--max", type=int, default=8, help="hard cap on proposals per run")
    ap.add_argument("--emit", help="write surviving PMIDs (one per line) to this file for CI")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    store = _load_all(args.files)
    client = PubMedClient(api_key=os.environ.get("NCBI_API_KEY"))
    # Correct recency filter: PubMed's reldate (last N days by publication date).
    pmids = client.esearch(args.query, retmax=args.retmax, reldate=args.days, datetype="pdat")
    print(f"PubMed returned {len(pmids)} records in the last {args.days} days; scoring...")
    cands = client.efetch(pmids) if pmids else []
    picks = select(cands, store, min_conf=args.min_confidence)[: args.max]

    print(f"\n{len(picks)} candidate(s) pass the filter (cap {args.max}):")
    for p in picks:
        print(f"  {p['confidence']:6s} {p['score']:5.1f} [{p['action']:12s}"
              + (f"->{p['parent']}" if p['parent'] else "") + f"] PMID {p['pmid']}  {p['title'][:70]}")
    if args.emit:
        with open(args.emit, "w") as fh:
            fh.write("\n".join(p["pmid"] for p in picks))
        print(f"\nWrote {len(picks)} PMID(s) to {args.emit}")
    return 0


def _selftest() -> int:
    from pubmed_linker import Candidate
    store = {"trials.json": [
        {"acronym": "TRILUMINATE Pivotal", "nct": "NCT03904147",
         "doi": "10.1056/NEJMoa2300525", "pmid": "36876753",
         "key_papers": [{"pmid": "40159089"}]},
    ]}
    cands = [
        # already the primary -> dropped (known)
        Candidate(pmid="36876753", title="primary", nct_accessions=["NCT03904147"],
                  pubtypes=["randomized controlled trial"]),
        # already an attached follow-up -> dropped (known)
        Candidate(pmid="40159089", title="2-year", nct_accessions=["NCT03904147"],
                  pubtypes=["multicenter study"]),
        # a new primary with its own NCT -> kept for registry/cohort REVIEW
        Candidate(pmid="55550001", doi="10.1/x",
                  title="First-in-Human Transcatheter Mitral Replacement: the NovaMitral Trial",
                  authors=["Roe J"], journal="JACC Cardiovasc Interv", year="2026",
                  pubtypes=["clinical trial"], nct_accessions=["NCT08880001"]),
        # a subanalysis of an existing trial -> kept, SUBANALYSIS
        Candidate(pmid="55550002", doi="10.1/y",
                  title="Imaging Substudy of the TRILUMINATE Pivotal Trial",
                  authors=["Cavalcante J"], journal="JACC", year="2025",
                  pubtypes=["multicenter study"], nct_accessions=["NCT03904147"]),
        # a review that merely mentions trials -> dropped (mention/LOW)
        Candidate(pmid="55550003", title="Transcatheter valve therapy: a review",
                  abstract="We discuss TRILUMINATE and others.", pubtypes=["review"]),
    ]
    picks = select(cands, store, min_conf="MEDIUM")
    got = {(p["pmid"], p["action"]) for p in picks}
    want = {("55550001", "REVIEW"), ("55550002", "SUBANALYSIS")}
    dropped_known = "36876753" not in {p["pmid"] for p in picks} and \
                    "40159089" not in {p["pmid"] for p in picks}
    dropped_review = "55550003" not in {p["pmid"] for p in picks}
    ok = (got == want) and dropped_known and dropped_review
    for p in picks:
        print(f"  kept {p['confidence']:6s} [{p['action']:12s}] PMID {p['pmid']}  {p['title'][:55]}")
    print(f"\nnew primary + subanalysis kept: {got == want}")
    print(f"already-known dropped: {dropped_known}")
    print(f"review/mention dropped: {dropped_review}")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_cli())
