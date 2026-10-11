#!/usr/bin/env python3
"""
proposer.py — turn a confidence-scored PubMed hit into a reviewable change proposal.

Pipeline:  pubmed_linker (find + score)  ->  proposer (route + generate fields)  ->
           GitHub Action opens a Pull Request  ->  you get an email  ->  Merge = approve.

Routing (registry link is ground truth):
  * paper's NCT matches an existing trial that has NO primary link yet  -> FILL_PRIMARY
  * paper's NCT matches an existing trial that already has a primary     -> SUBANALYSIS
  * paper's NCT is not in the database and it reads as a primary         -> NEW_TRIAL
  * anything ambiguous                                                   -> REVIEW (draft PR)

Field generation is deliberately split:
  * FACTUAL / bibliographic fields (nct, doi, pmid, authors, journal, year, citation,
    and a best-effort valve/category/sample-size guess) are auto-filled.
  * INTERPRETIVE / clinical fields (takeaway, quick_summary, why_matters, pearls,
    key_results ...) are emitted as explicit "DRAFT - review" placeholders. This tool
    never fabricates clinical conclusions; you write/confirm those in the PR.

Pure logic is unit-tested offline (`--selftest`). Live fetch needs internet (CI/local).
"""
from __future__ import annotations

import json
import re
import sys
from typing import Optional

from pubmed_linker import (Candidate, Trial, classify_kind, score_candidate,
                           _norm, PubMedClient, link_trial)

DRAFT = "DRAFT - review: "

# Clinical/interpretive fields an LLM may draft (from the abstract) for a NEW trial.
# Bibliographic/factual fields are never LLM-generated -- they come from the record.
CLINICAL_FIELDS = [
    "takeaway", "quick_summary", "device", "intervention", "comparator", "population",
    "risk_group", "disease", "procedure", "primary_endpoint", "secondary_endpoints",
    "key_results", "why_matters", "pearls", "limitations", "tags",
]


def _extract_json(text: str):
    """Pull a JSON object out of a model reply, tolerating ```json fences / prose."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, flags=re.S)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                return None
    return None


def _anthropic_draft(cand: "Candidate"):
    """Draft clinical fields from the abstract via the Anthropic API. Needs ANTHROPIC_API_KEY.
    Returns a dict of fields, or None if unavailable/failed. Never fabricates: the prompt
    forbids using anything not in the abstract and asks for '' when unknown."""
    import os
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not cand.abstract:
        return None
    import urllib.request
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    schema = ("takeaway (<=1 sentence), quick_summary (<=3 sentences), device, intervention, "
              "comparator, population, risk_group, disease, procedure, primary_endpoint, "
              "secondary_endpoints (array), key_results (array of short strings with the numbers), "
              "why_matters (<=2 sentences), pearls (array), limitations (array), tags (array)")
    prompt = (
        "You are drafting a structured summary of ONE clinical trial for a cardiology reference, "
        "using ONLY the title and abstract provided. Rules: paraphrase in your own words (do NOT "
        "quote the abstract verbatim); use ONLY facts stated in the abstract; if a field is not "
        "stated, return an empty string or empty array; be concise and neutral; do not infer "
        "guideline or FDA status. Return ONLY a JSON object with these keys: " + schema + ".\n\n"
        f"TITLE: {cand.title}\nJOURNAL/YEAR: {cand.journal} {cand.year}\n"
        f"ABSTRACT: {cand.abstract}\n"
    )
    body = json.dumps({"model": model, "max_tokens": 1200,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read())
        text = "".join(b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text")
        return _extract_json(text)
    except Exception as e:
        print("  (AI draft skipped:", e, ")")
        return None


def draft_clinical_fields(cand: "Candidate", trial: dict) -> dict:
    """Fill the DRAFT placeholders with AI-drafted content when available; else leave them.
    AI output is marked with a caveat so it is obviously review-required."""
    data = _anthropic_draft(cand)
    if not data:
        return trial
    for k in CLINICAL_FIELDS:
        v = data.get(k)
        if v in (None, "", []):
            continue
        if isinstance(trial.get(k), list) and not isinstance(v, list):
            v = [v]
        trial[k] = v
    trial["caveat"] = ((trial.get("caveat") + " ") if trial.get("caveat") else "") + \
        "Clinical fields AI-drafted from the abstract - verify before publishing."
    return trial


# --------------------------------------------------------------------------------------
# Small generators
# --------------------------------------------------------------------------------------

def derive_label(title: str) -> str:
    """A short human label for a follow-up/subanalysis, from its title."""
    t = _norm(title)
    m = re.search(r"\b(\d+)[- ]year", t)
    if m:
        return f"{m.group(1)}-year"
    m = re.search(r"\b(\d+)[- ]month", t)
    if m:
        return f"{m.group(1)}-month"
    for cue, label in [
        ("renal", "renal & liver function"), ("liver", "renal & liver function"),
        ("hepatic", "renal & liver function"), ("imaging", "imaging substudy"),
        ("echocardiograph", "echocardiographic outcomes"),
        ("quality of life", "quality of life"), ("kccq", "quality of life"),
        ("sex", "sex-specific outcomes"), ("gender", "sex-specific outcomes"),
        ("cost", "cost-effectiveness"), ("pacemaker", "CIED / lead subanalysis"),
        ("lead", "CIED / lead subanalysis"), ("design", "trial design"),
        ("rationale", "trial design"), ("predictor", "predictors of outcome"),
        ("baseline", "baseline characteristics"),
    ]:
        if cue in t:
            return label
    return "follow-up"


def build_citation(cand: Candidate) -> str:
    """'Author et al. Journal Year;vol(issue):pages.'"""
    first = cand.authors[0] if cand.authors else ""
    who = f"{first}, et al." if first else ""
    vol = cand.volume + (f"({cand.issue})" if cand.issue else "")
    tail = f"{cand.year}" + (f";{vol}" if vol else "") + (f":{cand.pages}" if cand.pages else "")
    return " ".join(p for p in [who, cand.journal, tail] if p).strip() + ("." if tail else "")


def candidate_to_keypaper(cand: Candidate) -> dict:
    return {
        "label": derive_label(cand.title),
        "citation": build_citation(cand),
        "doi": cand.doi or "",
        "pmid": cand.pmid or "",
    }


def guess_valve_and_category(cand: Candidate) -> tuple:
    t = _norm(cand.title + " " + cand.abstract)
    valve = next((v.title() for v in ("tricuspid", "mitral", "aortic") if v in t), "")
    proc = ("TEER" if ("edge-to-edge" in t or "teer" in t) else
            "Annuloplasty" if "annuloplasty" in t else
            "Replacement" if ("replacement" in t or "tmvr" in t or "ttvr" in t or "tavr" in t
                              or "tavi" in t) else
            "Repair" if "repair" in t else "")
    cat_guess = f"{valve} {proc}".strip()
    return valve, (cat_guess or DRAFT + "set category")


def extract_sample_size(cand: Candidate) -> str:
    m = (re.search(r"\b(?:included|enrolled|treated)\b[^.]{0,20}?\b(\d{2,4})\b", _norm(cand.abstract))
         or re.search(r"\b(\d{2,4})\b[^.]{0,20}?\b(?:patients|subjects|participants)\b", _norm(cand.abstract)))
    return m.group(1) if m else ""


def candidate_to_trial(cand: Candidate) -> dict:
    """Full site-schema Trial dict: factual fields filled, clinical fields as DRAFT."""
    valve, category = guess_valve_and_category(cand)
    return {
        "acronym": DRAFT + "set acronym",
        "full_name": cand.title,
        "nct": cand.nct_accessions[0] if cand.nct_accessions else "",
        "category": category,
        "valve": valve,
        "procedure": "",
        "disease": "",
        "tags": [],
        "status": "published",
        "signal": "descriptive",
        "practice_changing": False,
        "landmark": False,
        "evidence_stars": 0,
        "caveat": "",
        "quick_summary": DRAFT + "one-paragraph plain summary",
        "takeaway": DRAFT + "one-line headline",
        "device": "",
        "intervention": "",
        "comparator": "",
        "population": "",
        "risk_group": "",
        "sample_size": extract_sample_size(cand),
        "enrollment": "",
        "follow_up": "",
        "trial_type": ("Randomized controlled trial"
                       if "randomized controlled trial" in cand.pubtypes else
                       "Observational / single-arm" if "observational study" in cand.pubtypes else ""),
        "inclusion": [],
        "primary_endpoint": DRAFT + "state the primary endpoint",
        "secondary_endpoints": [],
        "key_results": [DRAFT + "list the key numeric results"],
        "why_matters": DRAFT + "why this trial matters",
        "pearls": [],
        "limitations": [],
        "guideline_acc": "",
        "guideline_esc": "",
        "fda_impact": "",
        "timeline": [f"Published: {cand.journal} {cand.year}".strip()],
        "authors": ", ".join(cand.authors[:3]) + (", et al." if len(cand.authors) > 3 else ""),
        "journal": cand.journal,
        "year": cand.year,
        "doi": cand.doi or "",
        "pmid": cand.pmid or "",
        "key_papers": [],
    }


# --------------------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------------------

def route(cand: Candidate, trials: list) -> dict:
    """Decide what to do with a candidate against the current trial list.

    Returns {action, parent_acronym, reason}. action in:
      FILL_PRIMARY | SUBANALYSIS | NEW_TRIAL | DUPLICATE | REVIEW
    """
    by_nct = {}
    for t in trials:
        if t.get("nct"):
            by_nct.setdefault(t["nct"].upper(), []).append(t)
    if cand.pmid and any(cand.pmid == t.get("pmid") or
                         cand.pmid in {p.get("pmid") for p in t.get("key_papers", [])}
                         for t in trials):
        return {"action": "DUPLICATE", "parent": None, "reason": "PMID already stored"}
    for nct in cand.nct_accessions:
        parents = by_nct.get(nct.upper(), [])
        if not parents:
            continue
        if len(parents) > 1:
            return {"action": "REVIEW", "parent": None,
                    "reason": "NCT belongs to multiple cohorts; select the correct trial manually"}
        parent = parents[0]
        acr = parent.get("acronym", "")
        if cand.pmid and cand.pmid == parent.get("pmid"):
            return {"action": "DUPLICATE", "parent": acr, "reason": "already the trial's primary"}
        if cand.pmid in {p.get("pmid") for p in parent.get("key_papers", [])}:
            return {"action": "DUPLICATE", "parent": acr, "reason": "already attached as a follow-up"}
        has_primary = bool(parent.get("doi") or parent.get("pmid"))
        kind = classify_kind(cand, acr)
        if not has_primary and kind == "primary":
            return {"action": "FILL_PRIMARY", "parent": acr, "reason": "NCT match; parent had no primary link"}
        return {"action": "SUBANALYSIS", "parent": acr,
                "reason": f"NCT match; parent already has a primary ({kind})"}
    # No NCT match in the database.
    kind = classify_kind(cand, "")
    if kind == "primary" and cand.nct_accessions:
        return {"action": "REVIEW", "parent": None,
                "reason": "new registered trial candidate; verify registry and cohort before adding"}
    return {"action": "REVIEW", "parent": None,
            "reason": "no NCT match and not a clear primary - needs a human decision"}


def apply_proposal(cand: Candidate, decision: dict, trials: list, use_ai: bool = False) -> dict:
    """Mutate `trials` in place per the decision. Returns a summary of what changed.
    (Used on a PR branch only; approval = merging that PR.)"""
    action, parent = decision["action"], decision.get("parent")
    if action == "DUPLICATE":
        return {"changed": False, "note": "no change - " + decision["reason"]}

    if action == "NEW_TRIAL":
        trial = candidate_to_trial(cand)
        drafted = False
        if use_ai:
            before = trial.get("takeaway")
            trial = draft_clinical_fields(cand, trial)
            drafted = trial.get("takeaway") != before
        trials.append(trial)
        return {"changed": True,
                "note": "appended NEW trial " + ("(clinical fields AI-drafted; review in PR)"
                        if drafted else "(clinical fields are DRAFT placeholders)")}

    idx = next((i for i, t in enumerate(trials) if t.get("acronym") == parent), None)
    if idx is None:
        return {"changed": False, "note": f"parent '{parent}' not found"}

    if action == "FILL_PRIMARY":
        t = trials[idx]
        if cand.doi:
            t["doi"] = cand.doi
        if cand.pmid:
            t["pmid"] = cand.pmid
        if not t.get("authors") and cand.authors:
            t["authors"] = ", ".join(cand.authors[:3]) + (", et al." if len(cand.authors) > 3 else "")
        return {"changed": True, "note": f"filled primary DOI/PMID on '{parent}'"}

    if action in ("SUBANALYSIS", "REVIEW"):
        trials[idx].setdefault("key_papers", []).append(candidate_to_keypaper(cand))
        tag = "" if action == "SUBANALYSIS" else " (REVIEW: confirm this belongs here)"
        return {"changed": True, "note": f"attached follow-up to '{parent}'{tag}"}
    return {"changed": False, "note": "no matching action"}


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def _load_all(files):
    store = {}
    for f in files:
        try:
            store[f] = json.load(open(f, encoding="utf-8"))
        except FileNotFoundError:
            pass
    return store


def _propose_for_candidate(cand, store, write=False, use_ai=False):
    all_trials = [t for rows in store.values() for t in rows]
    decision = route(cand, all_trials)
    print(f"  action   : {decision['action']}")
    print(f"  parent   : {decision.get('parent') or '-'}")
    print(f"  reason   : {decision['reason']}")
    # Which file to write into: the file that holds the parent, else the valve's file.
    target = None
    if decision.get("parent"):
        for f, rows in store.items():
            if any(t.get("acronym") == decision["parent"] for t in rows):
                target = f
                break
    else:
        valve, _ = guess_valve_and_category(cand)
        target = ("trials_tricuspid.json" if valve == "Tricuspid" and "trials_tricuspid.json" in store
                  else next((f for f in store if f != "trials.json"), None) if valve == "Tricuspid"
                  else "trials.json")
    print(f"  target   : {target}")
    if decision["action"] == "NEW_TRIAL":
        preview = candidate_to_trial(cand)
        if use_ai:
            preview = draft_clinical_fields(cand, preview)
        print("  proposed trial (%s):" % ("AI-drafted" if use_ai else "placeholders"))
        print("    takeaway: " + str(preview.get("takeaway"))[:160])
    elif decision["action"] in ("SUBANALYSIS", "REVIEW"):
        print("  proposed key_paper:", json.dumps(candidate_to_keypaper(cand), ensure_ascii=False))
    if write and target in store:
        summary = apply_proposal(cand, decision, store[target], use_ai=use_ai)
        if summary["changed"]:
            json.dump(store[target], open(target, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
        print("  applied  :", summary["note"])
    return decision


def _cli():
    import argparse
    import os
    ap = argparse.ArgumentParser(description="Propose a trial/subanalysis add from a PubMed hit.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pmid", help="PubMed ID to fetch and propose")
    ap.add_argument("--files", nargs="*", default=["trials.json", "trials_tricuspid.json"])
    ap.add_argument("--write", action="store_true", help="apply to the target JSON (use on a PR branch)")
    ap.add_argument("--ai", action="store_true", help="AI-draft clinical fields for new trials")
    ap.add_argument("--no-ai", action="store_true", help="never AI-draft (override auto-detect)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.pmid:
        ap.print_help()
        return 0

    # AI drafting is OFF by default (free mode). Turn it on only with --ai AND a key.
    use_ai = args.ai and bool(os.environ.get("ANTHROPIC_API_KEY")) and not args.no_ai
    client = PubMedClient(api_key=os.environ.get("NCBI_API_KEY"))
    cands = client.efetch([args.pmid])
    if not cands:
        print("No record for PMID", args.pmid)
        return 1
    store = _load_all(args.files)
    print(f"PMID {args.pmid}: {cands[0].title}  (AI drafting: {'on' if use_ai else 'off'})")
    _propose_for_candidate(cands[0], store, write=args.write, use_ai=use_ai)
    return 0


# --------------------------------------------------------------------------------------
# Offline tests: routing + generation on the exact cases that matter
# --------------------------------------------------------------------------------------

def _selftest() -> int:
    trials = [
        {"acronym": "TRILUMINATE Pivotal", "nct": "NCT03904147",
         "doi": "10.1056/NEJMoa2300525", "pmid": "36876753", "key_papers": []},
        {"acronym": "CLASP II TR", "nct": "NCT04097145", "doi": "", "pmid": "", "key_papers": []},
    ]
    tests = []

    # A) NCT matches a trial that already has a primary -> SUBANALYSIS, labeled
    tests.append((
        "renal/liver subanalysis of TRILUMINATE Pivotal",
        Candidate(pmid="39222896", doi="10.1016/j.jacc.2024.08.044",
                  title="Impact of Renal and Liver Function on Outcomes: the TRILUMINATE Pivotal Trial",
                  authors=["Jorde UP"], journal="J Am Coll Cardiol", year="2024",
                  volume="84", issue="25", pages="2446-2456",
                  pubtypes=["multicenter study"], nct_accessions=["NCT03904147"]),
        "SUBANALYSIS", "TRILUMINATE Pivotal",
    ))
    # B) NCT matches a trial with NO primary yet, and it's a primary -> FILL_PRIMARY
    tests.append((
        "primary results for CLASP II TR",
        Candidate(pmid="55555551", doi="10.1000/clasp2tr",
                  title="Transcatheter Repair vs Medical Therapy in Tricuspid Regurgitation: CLASP II TR",
                  authors=["Hahn RT"], journal="JACC Cardiovasc Interv", year="2026",
                  pubtypes=["randomized controlled trial"], nct_accessions=["NCT04097145"]),
        "FILL_PRIMARY", "CLASP II TR",
    ))
    # C) NCT not in DB needs a registry/cohort review before adding a card.
    tests.append((
        "a brand-new device trial",
        Candidate(pmid="55555552", doi="10.1000/newdevice",
                  title="First-in-Human Transcatheter Tricuspid Replacement With the NovaValve System",
                  authors=["Smith A", "Doe B"], journal="JACC Cardiovasc Interv", year="2026",
                  pubtypes=["clinical trial"], nct_accessions=["NCT09999999"]),
        "REVIEW", None,
    ))
    # D) already attached -> DUPLICATE
    trials[0]["key_papers"].append({"pmid": "40159089"})
    tests.append((
        "already-attached follow-up",
        Candidate(pmid="40159089", title="Two-Year Outcomes: TRILUMINATE Pivotal",
                  authors=["Kar S"], journal="Circulation", year="2025",
                  pubtypes=["multicenter study"], nct_accessions=["NCT03904147"]),
        "DUPLICATE", None,
    ))
    # E) One registration can hold multiple named cohorts; never choose the last one.
    shared = trials + [{"acronym": "TRILUMINATE Registry", "nct": "NCT03904147",
                        "pmid": "", "doi": "", "key_papers": []}]
    ambiguous = Candidate(pmid="55555553", title="Tricuspid Valve Outcomes",
                          nct_accessions=["NCT03904147"])
    shared_route = route(ambiguous, shared)
    shared_passed = shared_route["action"] == "REVIEW"
    print(f"[{'PASS' if shared_passed else 'FAIL'}] shared NCT held for review")

    ok = int(shared_passed)
    for name, cand, exp_action, exp_parent in tests:
        d = route(cand, trials)
        passed = d["action"] == exp_action and (d.get("parent") or None) == (exp_parent or None)
        ok += passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        print(f"        action={d['action']}  parent={d.get('parent')}  "
              f"(expected {exp_action}/{exp_parent})")
        if cand.nct_accessions and d["action"] in ("SUBANALYSIS", "REVIEW"):
            print("        key_paper ->", json.dumps(candidate_to_keypaper(cand), ensure_ascii=False))
        if d["action"] == "NEW_TRIAL":
            tr = candidate_to_trial(cand)
            print(f"        new trial -> valve={tr['valve']!r} category={tr['category']!r} "
                  f"doi={tr['doi']} (clinical fields are DRAFT placeholders)")
        print()
    # E) JSON extraction tolerates fences/prose; no-key drafting is a safe no-op.
    extra_ok = 0
    fenced = "Here you go:\n```json\n{\"takeaway\": \"x\", \"key_results\": [\"a\", \"b\"]}\n```"
    got = _extract_json(fenced)
    if got == {"takeaway": "x", "key_results": ["a", "b"]}:
        extra_ok += 1
        print("[PASS] _extract_json handles fenced/prose replies")
    else:
        print("[FAIL] _extract_json ->", got)
    import os as _os
    had = _os.environ.pop("ANTHROPIC_API_KEY", None)   # ensure no key
    skel = candidate_to_trial(Candidate(title="T", abstract="A"))
    same = draft_clinical_fields(Candidate(title="T", abstract="A"), dict(skel))
    if same["takeaway"] == skel["takeaway"]:
        extra_ok += 1
        print("[PASS] draft_clinical_fields is a no-op without an API key (placeholders kept)")
    else:
        print("[FAIL] drafting changed fields without a key")
    if had:
        _os.environ["ANTHROPIC_API_KEY"] = had

    total = ok + extra_ok
    print(f"{total}/{len(tests) + 3} cases passed")
    return 0 if total == len(tests) + 3 else 1


if __name__ == "__main__":
    sys.exit(_cli())
