#!/usr/bin/env python3
"""
discover_updates.py — monthly PubMed discovery + JSON updater for the valve-trials site.

Revised after four real misses (CLASP IID, PARTNER 3, the ahead-of-print lag, TRAVEL/LuX-Valve).
The through-line of every miss: the pipeline leaned on the NCT [si] link and silently dropped
anything that link didn't carry. This version reduces that single-point dependence and, crucially,
never silently drops a grey-zone hit.

What it does each run (GitHub Actions monthly; see the workflow):
  1. Scans EVERY published AND ongoing trial (not just ones missing a primary) — so follow-ups
     for established trials are discovered.
  2. Dedupes each candidate against what the trial already stores (top-level pmid/doi AND every
     key_papers entry), by normalized PMID and DOI.
  3. Decision, per candidate:
       * ADD  — MEDIUM-or-better, kind in {primary, subanalysis}: written to the record
                (a missing primary fills pmid/doi; everything else appends to key_papers).
       * REVIEW — near-miss (score in [review_low, MEDIUM)), OR the paper names an NCT this
                record doesn't have. Not written; listed in the PR/email for a human call.
                This is the bucket that catches the TRAVEL class of miss.
       * DROP — below review_low and nothing else notable.
  4. NCT self-heal: when a decent candidate names an NCT the record lacks, it proposes writing
     that NCT to the record (and, since the paper identifies itself with that registration,
     adds the paper). All of it lands in a PR, so a human still approves.
  5. Look-back window (--lookback-days) re-queries recent papers so ahead-of-print records that
     were unlinked last month get re-scored once their [si] link attaches.
  6. Emits a Markdown report (PR body) with Added / Needs-review / Proposed-NCT sections, and an
     audit of every record that still has no NCT (fix these first — they're invisible to [si]).

The merge logic is pure and offline-tested via `--selftest` (covers the TRAVEL case).
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from typing import Callable, List, Tuple

try:
    from pubmed_linker import Trial, Candidate, score_candidate, build_queries  # type: ignore
    _HAVE_LINKER = True
except Exception:  # sandbox / offline selftest
    from linker_core import Trial, Candidate, score_candidate, build_queries  # type: ignore
    _HAVE_LINKER = False

CONF_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# ---------------------------------------------------------------------------------------
# Citation + label formatting
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
    words = re.sub(r"[^a-zA-Z0-9 ]", "", cand.title or "").split()
    return " ".join(words[:5]) if words else "Follow-up"


def format_citation(cand: "Candidate") -> str:
    author = cand.authors[0].strip() if cand.authors else ""
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
# Identity / dedupe
# ---------------------------------------------------------------------------------------
def norm_pmid(p) -> str:
    return re.sub(r"\D", "", str(p or ""))


def norm_doi(d) -> str:
    d = str(d or "").strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


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
# Live candidate gathering (network). Injected so merge() is testable offline.
# ---------------------------------------------------------------------------------------
def make_live_gatherer(client, retmax: int = 25, reldate=None):
    """gather(trial) -> [(Candidate, scored_dict)]. reldate (days) enables the look-back window."""
    def gather(trial: "Trial"):
        seen, cands = set(), []
        for _strategy, term in build_queries(trial):
            try:
                pmids = [p for p in client.esearch(term, retmax=retmax, reldate=reldate, datetype="edat")
                         if p not in seen]
            except TypeError:
                pmids = [p for p in client.esearch(term, retmax=retmax) if p not in seen]
            except Exception as ex:
                sys.stderr.write(f"  ! esearch failed {trial.acronym} [{term}]: {ex}\n"); continue
            seen.update(pmids)
            try:
                cands += client.efetch(pmids)
            except Exception as ex:
                sys.stderr.write(f"  ! efetch failed {trial.acronym}: {ex}\n")
        return [(c, score_candidate(trial, c)) for c in cands]
    return gather


# ---------------------------------------------------------------------------------------
# The pure merge step. Returns (added, review, nct_fixes).
# ---------------------------------------------------------------------------------------
def merge_new_papers(
    data: List[dict],
    gather: Callable[["Trial"], List[Tuple["Candidate", dict]]],
    min_conf: str = "MEDIUM",
    kinds=("primary", "subanalysis"),
    statuses=("published", "ongoing"),
    review_low: float = 35.0,
) -> Tuple[List[dict], List[dict], List[dict]]:
    """Returns (added, review, field_updates).
    - added: new key_papers / primary references written to records.
    - review: grey-zone hits not written (a human decides in the PR).
    - field_updates: proposed changes to OTHER fields (status ongoing->published, NCT
      self-heal, primary citation backfill) — each is old->new, applied to the record so it
      shows as a plain JSON diff in the PR, which is where you approve it by merging.
    """
    added: List[dict] = []
    review: List[dict] = []
    field_updates: List[dict] = []
    min_rank = CONF_RANK[min_conf]

    for row in data:
        if row.get("status") not in statuses:
            continue
        trial = trial_from_row(row)
        pmids, dois = existing_ids(row)
        stored_nct = (row.get("nct") or "").upper()
        pairs = gather(trial)
        pairs.sort(key=lambda cs: cs[1].get("score", 0), reverse=True)

        for cand, sc in pairs:
            np_, nd_ = norm_pmid(cand.pmid), norm_doi(cand.doi)
            if (np_ and np_ in pmids) or (nd_ and nd_ in dois):
                continue  # already stored

            conf = sc.get("confidence", "LOW")
            rank = CONF_RANK.get(conf, 0)
            score = sc.get("score", 0) or 0
            kind = sc.get("kind", "mention")
            declared = list(dict.fromkeys(sc.get("nct_declared") or []))  # unique, ordered
            names_new_nct = (not stored_nct) and len(declared) == 1

            def propose(field, new, reason):
                field_updates.append({
                    "trial": row.get("acronym", ""), "field": field,
                    "old": row.get(field, ""), "new": new, "reason": reason,
                    "pmid": np_, "confidence": conf, "score": score,
                })
                row[field] = new

            # --- NCT self-heal: paper names an NCT this record lacks, with real content match ---
            healed = False
            if names_new_nct and score >= review_low:
                propose("nct", declared[0], "paper names an NCT the record was missing")
                stored_nct = declared[0].upper()
                healed = True  # a paper that self-identifies with our (now-known) NCT is add-worthy

            should_add = (rank >= min_rank and kind in kinds) or healed

            if should_add:
                entry = {
                    "label": derive_label(cand),
                    "citation": format_citation(cand),
                    "doi": nd_, "pmid": np_,
                }
                if (not row.get("pmid") and not row.get("doi")
                        and kind == "primary" and (conf == "HIGH" or healed)):
                    row["pmid"] = np_
                    if nd_:
                        row["doi"] = nd_
                    target = "primary"
                    # backfill citation fields from the primary paper when empty
                    if not row.get("year") and cand.year:
                        propose("year", cand.year, "from primary paper")
                    if not row.get("journal") and cand.journal:
                        propose("journal", cand.journal, "from primary paper")
                    if not row.get("authors") and cand.authors:
                        propose("authors", f"{cand.authors[0]}, et al.", "from primary paper")
                else:
                    row.setdefault("key_papers", [])
                    row["key_papers"].append(entry)
                    target = "key_papers"

                # STATUS TRANSITION: an ongoing trial whose primary result has published.
                if row.get("status") == "ongoing" and kind == "primary" and conf == "HIGH":
                    propose("status", "published", "primary result published (HIGH primary match)")

                if np_:
                    pmids.add(np_)
                if nd_:
                    dois.add(nd_)
                added.append({
                    "trial": row.get("acronym", ""), "target": target, "kind": kind,
                    "confidence": conf, "score": score, "pmid": np_, "doi": nd_,
                    "label": entry["label"], "citation": entry["citation"],
                    "healed_nct": healed, "title": cand.title,
                })
            elif score >= review_low or names_new_nct:
                # grey zone — never dropped silently; a human decides.
                review.append({
                    "trial": row.get("acronym", ""), "kind": kind, "confidence": conf,
                    "score": score, "pmid": np_, "doi": nd_,
                    "declares_nct": declared, "title": cand.title,
                    "citation": format_citation(cand),
                })
    return added, review, field_updates


# ---------------------------------------------------------------------------------------
# NCT-gap audit
# ---------------------------------------------------------------------------------------
def nctless_records(data: List[dict], statuses=("published", "ongoing")) -> List[dict]:
    out = []
    for row in data:
        if row.get("status") in statuses and not (row.get("nct") or "").strip():
            out.append({"acronym": row.get("acronym", ""), "valve": row.get("valve", ""),
                        "status": row.get("status", "")})
    return out


# ---------------------------------------------------------------------------------------
# Report (PR body)
# ---------------------------------------------------------------------------------------
def write_report(added, review, field_updates, nctless, path, files, run_stamp=""):
    from collections import defaultdict
    L = ["# Monthly trial-literature update\n"]
    if run_stamp:
        L.append(f"_Run: {run_stamp}_\n")
    if not (added or review or field_updates):
        L.append("No new papers, field changes, or review items this run. ✅\n")
    L.append(f"Scanned `{', '.join(files)}` — **{len(added)} papers added**, "
             f"**{len(field_updates)} field change(s)** proposed, **{len(review)} to review**.\n")
    L.append("Merge this PR to approve every change below; edit or close to reject.\n")

    if field_updates:
        by = defaultdict(list)
        for u in field_updates:
            by[u["trial"]].append(u)
        L.append("\n## Proposed field changes\n")
        L.append("Status flips, NCT fixes, and citation backfills — shown as old → new in the JSON diff.\n")
        for trial in sorted(by):
            L.append(f"\n**{trial}**")
            for u in by[trial]:
                old = u["old"] if u["old"] not in ("", None) else "—"
                L.append(f"- `{u['field']}`: {old} → **{u['new']}**  ({u['reason']}"
                         f"{'; PMID ' + u['pmid'] if u['pmid'] else ''})")

    if added:
        by = defaultdict(list)
        for a in added:
            by[a["trial"]].append(a)
        L.append("\n## Added\n")
        for trial in sorted(by):
            L.append(f"\n### {trial}")
            for a in sorted(by[trial], key=lambda x: -(x["score"] or 0)):
                tag = "**PRIMARY**" if a["target"] == "primary" else a["label"]
                heal = " · via self-healed NCT" if a.get("healed_nct") else ""
                L.append(f"- {tag} — {a['confidence']} ({a['score']}), {a['kind']}{heal} — "
                         f"PMID {a['pmid'] or '—'} · doi:{a['doi'] or '—'}  \n  {a['citation']}")

    if review:
        L.append("\n## Needs review (near-misses & NCT-declared)\n")
        L.append("Not written automatically — confirm (merge after editing) or ignore.\n")
        for r in sorted(review, key=lambda x: -(x["score"] or 0)):
            nctnote = f" · names {', '.join(r['declares_nct'])}" if r["declares_nct"] else ""
            L.append(f"- **{r['trial']}** — {r['confidence']} ({r['score']}), {r['kind']}{nctnote} — "
                     f"PMID {r['pmid'] or '—'}  \n  {r['citation']}")

    if nctless:
        L.append("\n## Records still missing an NCT (fix these first)\n")
        L.append("These are invisible to the registry `[si]` query — the strongest discovery signal.\n")
        for r in nctless:
            L.append(f"- {r['acronym']} ({r['valve']}, {r['status']})")

    open(path, "w").write("\n".join(L) + "\n")


# ---------------------------------------------------------------------------------------
# Offline selftest — covers dedupe, primary-fill, AND the TRAVEL case
# ---------------------------------------------------------------------------------------
def _selftest() -> int:
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS" if cond else "FAIL"), msg)
        ok = ok and cond

    # ---- Case A: dedupe + subanalysis add (CLASP IID) ----
    dataA = [{
        "acronym": "CLASP IID", "nct": "NCT03706833", "status": "published",
        "authors": "Lim DS, Smith RL, et al.", "journal": "JACC: Cardiovascular Interventions",
        "year": "2022", "device": "Edwards PASCAL", "valve": "Mitral", "procedure": "TEER",
        "sample_size": "180", "pmid": "36121247", "doi": "10.1016/j.jcin.2022.09.005",
        "key_papers": [{"label": "1-year", "citation": "Zahr F, et al. JACC Cardiovasc Interv 2023;16(23):2803-2816.",
                        "doi": "10.1016/j.jcin.2023.10.002", "pmid": ""}],
    }]
    newsub = Candidate(pmid="42233921", doi="10.1016/j.jcmg.2026.04.005",
                       title="Impact of Residual MR and Gradient After M-TEER: 1-Year Outcomes From the CLASP IID Trial",
                       abstract="One-year outcomes from the randomized CLASP IID trial.",
                       authors=["Narang A", "Lim DS"], journal="JACC Cardiovasc Imaging", year="2026",
                       volume="19", issue="6", pages="700-712",
                       pubtypes=["journal article", "multicenter study"], nct_accessions=["NCT03706833"])
    dupdoi = Candidate(pmid="", doi="10.1016/j.jcin.2023.10.002", title="dup", authors=["Zahr F"],
                       journal="JACC Cardiovasc Interv", year="2023", pubtypes=["journal article"],
                       nct_accessions=["NCT03706833"])
    addedA, revA, fuA = merge_new_papers(
        dataA, lambda t: [(c, score_candidate(t, c)) for c in (newsub, dupdoi)])
    check(len(addedA) == 1 and addedA[0]["pmid"] == "42233921", "CLASP IID: the 2026 subanalysis is added")
    check(len(dataA[0]["key_papers"]) == 2, "CLASP IID: no duplicate written (dup DOI skipped)")

    # ---- Case B: TRAVEL / LuX-Valve — no NCT stored, paper names one ----
    dataB = [{
        "acronym": "LuX-Valve", "nct": "", "status": "ongoing", "authors": "",
        "device": "Jenscare LuX-Valve / LuX-Valve Plus", "valve": "Tricuspid",
        "disease": "Tricuspid regurgitation", "procedure": "Transcatheter tricuspid replacement",
        "sample_size": "not fully extracted", "key_papers": [],
    }]
    travel = Candidate(
        pmid="40208152", doi="10.1016/j.jcin.2024.12.030",
        title="Transcatheter Tricuspid Valve Replacement With the Novel System: 1-Year Outcomes From the TRAVEL Study",
        abstract=("The TRAVEL (Transcatheter Right Atrial-Ventricular Valve Replacement With LuX-Valve) study "
                  "with the LuX-Valve system for severe TR. 126 patients with symptomatic severe TR underwent "
                  "TTVR using the LuX-Valve system."),
        authors=["Pan X", "von Bardeleben RS"], journal="JACC Cardiovasc Interv", year="2025",
        volume="18", issue="7", pages="900-912",
        pubtypes=["journal article", "multicenter study"], nct_accessions=["NCT04436653"])
    addedB, revB, fuB = merge_new_papers(
        dataB, lambda t: [(c, score_candidate(t, c)) for c in (travel,)])
    surfaced = any(a["pmid"] == "40208152" for a in addedB) or any(r["pmid"] == "40208152" for r in revB)
    check(surfaced, "TRAVEL: paper is surfaced, not silently dropped")
    check(any(u["field"] == "nct" and u["new"] == "NCT04436653" for u in fuB),
          "TRAVEL: NCT04436653 proposed as a field change")
    check(dataB[0]["nct"] == "NCT04436653", "TRAVEL: record self-healed with the NCT")
    check(any(a["pmid"] == "40208152" for a in addedB), "TRAVEL: paper added once the NCT is known")

    # ---- Case C: ongoing -> published status transition on a HIGH primary ----
    dataC = [{"acronym": "CLASP II TR", "nct": "NCT04097145", "status": "ongoing",
              "authors": "", "journal": "", "year": "", "device": "Edwards PASCAL",
              "valve": "Tricuspid", "procedure": "TEER", "sample_size": "825", "key_papers": []}]
    primaryC = Candidate(
        pmid="50000001", doi="10.1000/clasp2tr",
        title="Transcatheter Edge-to-Edge Repair vs Medical Therapy in Tricuspid Regurgitation: the CLASP II TR Trial",
        abstract="The randomized CLASP II TR trial evaluated the Edwards PASCAL system in tricuspid regurgitation.",
        authors=["Hahn RT"], journal="N Engl J Med", year="2027", volume="396", issue="1", pages="1-12",
        pubtypes=["randomized controlled trial", "multicenter study"], nct_accessions=["NCT04097145"])
    addedC, revC, fuC = merge_new_papers(dataC, lambda t: [(c, score_candidate(t, c)) for c in (primaryC,)])
    check(dataC[0]["status"] == "published", "CLASP II TR: status flipped ongoing -> published")
    check(any(u["field"] == "status" and u["new"] == "published" for u in fuC),
          "CLASP II TR: status change recorded as a field update")
    check(dataC[0]["pmid"] == "50000001", "CLASP II TR: primary reference filled")
    check(dataC[0]["year"] == "2027" and dataC[0]["journal"] == "N Engl J Med",
          "CLASP II TR: year/journal backfilled from the primary paper")

    # ---- Case D: unrelated ambiguous bare-word must NOT be added ----
    dataD = [{"acronym": "SCOUT", "nct": "NCT02574650", "status": "published",
              "authors": "Hahn RT, et al.", "journal": "J Am Coll Cardiol", "year": "2017",
              "device": "Trialign", "valve": "Tricuspid", "sample_size": "15", "key_papers": []}]
    junk = Candidate(pmid="999", title="A SCOUT imaging protocol for abdominal CT",
                     abstract="The scout view was used to plan acquisition.",
                     authors=["Smith A"], journal="Radiology", year="2015", pubtypes=["journal article"])
    addedD, revD, fuD = merge_new_papers(dataD, lambda t: [(c, score_candidate(t, c)) for c in (junk,)])
    check(not addedD, "SCOUT junk: not added")

    print("\nRESULT:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------
def _cli() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", nargs="+", default=["trials.json", "trials_tricuspid.json"])
    ap.add_argument("--threshold", choices=["LOW", "MEDIUM", "HIGH"], default="MEDIUM",
                    help="minimum confidence to auto-add (default MEDIUM)")
    ap.add_argument("--review-low", type=float, default=35.0,
                    help="scores at/above this (but below threshold) go to the review bucket")
    ap.add_argument("--kinds", nargs="+", default=["primary", "subanalysis"])
    ap.add_argument("--statuses", nargs="+", default=["published", "ongoing"])
    ap.add_argument("--lookback-days", type=int, default=0,
                    help="if >0, only consider papers indexed in the last N days (look-back window)")
    ap.add_argument("--report", default="discovery_report.md")
    ap.add_argument("--retmax", type=int, default=25)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not _HAVE_LINKER:
        sys.stderr.write("ERROR: pubmed_linker.py not importable — cannot run live discovery.\n")
        return 2

    from pubmed_linker import PubMedClient
    client = PubMedClient(api_key=os.environ.get("NCBI_API_KEY"), email=os.environ.get("NCBI_EMAIL", ""))
    reldate = args.lookback_days or None
    gather = make_live_gatherer(client, retmax=args.retmax, reldate=reldate)

    all_added, all_review, all_fu, all_nctless = [], [], [], []
    for path in args.files:
        if not os.path.exists(path):
            sys.stderr.write(f"skip (not found): {path}\n"); continue
        data = json.load(open(path, encoding="utf-8"))
        added, review, field_updates = merge_new_papers(
            data, gather, min_conf=args.threshold, kinds=tuple(args.kinds),
            statuses=tuple(args.statuses), review_low=args.review_low)
        if added or field_updates:  # any of these mutate the data
            json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        all_added += added
        all_review += review
        all_fu += field_updates
        all_nctless += nctless_records(data, statuses=tuple(args.statuses))
        print(f"{path}: +{len(added)} added, {len(field_updates)} field-change, {len(review)} review")

    run_stamp = os.environ.get("RUN_STAMP", "")
    write_report(all_added, all_review, all_fu, all_nctless, args.report, args.files, run_stamp)
    print(f"::notice::added {len(all_added)}, field-changes {len(all_fu)}, review {len(all_review)}")
    open("discovery_count.txt", "w").write(str(len(all_added) + len(all_fu)))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
