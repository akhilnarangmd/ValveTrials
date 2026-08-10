#!/usr/bin/env python3
"""
pubmed_linker.py — find and confidence-score the PubMed paper(s) for a clinical trial.
It mirrors how a human decides whether a paper is *about* a trial vs merely *mentions* it.
STRATEGY (in order of reliability):
  1. Registry link (most reliable): PubMed indexes each paper's declared ClinicalTrials.gov
     number in the [si] field.  `NCT03904147[si]` returns exactly the papers whose authors
     linked that registration -- this works even when the acronym never appears in the
     title/abstract, and even when the paper has NO abstract.
  2. Acronym + author + year/journal + device queries, then score every candidate on
     transparent, weighted signals (title hit, author match, publication type, registry
     link, device/valve/procedure topic, sample-size fingerprint, ...).
  3. Classify each hit as PRIMARY / SUBANALYSIS-or-FOLLOWUP / MENTION and assign a
     0-100 confidence with a per-signal breakdown, so a human can audit every decision.
The scoring/classification logic is pure Python and unit-tested offline (`--selftest`).
Live queries need internet (PubMed E-utilities); run locally or in CI, not in a
network-restricted sandbox.  Be polite: set NCBI_API_KEY to raise the rate limit.

Revised (see change log): device matching strips the manufacturer so the model matches;
strong content evidence lifts the ambiguous-acronym cap; score_candidate returns
`nct_declared` so discover_updates.py can self-heal missing NCTs and route grey-zone hits
to a human-review bucket.
"""
from __future__ import annotations
import json
import re
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional
# --------------------------------------------------------------------------------------
# Domain knowledge -- the "how a human reads it" rules, made explicit and tunable.
# --------------------------------------------------------------------------------------
# Acronyms that are also ordinary words / very generic -> high false-positive risk.
# For these, an acronym hit alone is NOT enough; we require corroboration (NCT, author,
# or STRONG CONTENT — device-in-title / sample-size fingerprint / full topic match).
AMBIGUOUS_ACRONYMS = {
    "scout", "mitral", "hover", "summit", "tact", "travel", "active", "choice",
    "partner", "surtavi", "reprise", "restore", "encircle", "apollo", "tiara",
    "cephea", "intrepid", "sapien", "notion", "everest", "harpoon", "tandem",
}
# Publication types that mark a paper as a PRIMARY trial report.
PRIMARY_PUBTYPES = {
    "randomized controlled trial", "controlled clinical trial", "clinical trial",
    "clinical trial, phase i", "clinical trial, phase ii", "clinical trial, phase iii",
    "clinical trial, phase iv", "multicenter study", "pragmatic clinical trial",
    "observational study", "clinical trial protocol",
}
# Publication types that mark a paper as SECONDARY literature (about trials, not a trial).
SECONDARY_PUBTYPES = {
    "review", "systematic review", "meta-analysis", "editorial", "comment",
    "letter", "news", "guideline", "practice guideline", "published erratum",
    "case reports", "historical article",
}
# Title/abstract cues that a paper is a follow-up or subanalysis rather than the primary.
SUBSTUDY_CUES = [
    r"\b\d+[- ]year\b", r"\b\d+[- ]month\b", r"\bpost[- ]?hoc\b", r"\bsub[- ]?analysis\b",
    r"\bsub[- ]?study\b", r"\bsecondary analysis\b", r"\blanding\b", r"\bpredictors?\b",
    r"\bimaging substudy\b", r"\bechocardiograph", r"\bquality of life\b", r"\bkccq\b",
    r"\brenal\b", r"\bliver\b", r"\bhepatic\b", r"\bsex[- ]", r"\bgender\b",
    r"\bcost[- ]effective", r"\blong[- ]term\b", r"\bfinal\b", r"\bextended\b",
    r"\baccording to\b", r"\bstratified by\b", r"\bimpact of\b", r"\bassociation of\b",
]
# Phrases that signal the acronym is being used as a COMPARATOR / reference (a mention),
# e.g. "compared with COAPT", "as seen in MITRA-FR".
COMPARATOR_CUES = [
    r"compared (?:with|to)", r"\bversus\b", r"\bvs\.?\b", r"similar to", r"unlike",
    r"in line with", r"consistent with", r"as (?:seen|shown|reported) in",
    r"following (?:the )?", r"building on", r"after the",
]
# Manufacturer / filler words to strip so the *device model* is what we match on. Without
# this, "Jenscare LuX-Valve" reduced to "jenscare" and matched nothing (the TRAVEL miss).
VENDOR_WORDS = {
    "edwards", "lifesciences", "abbott", "medtronic", "boston", "scientific",
    "jenscare", "jc", "medical", "croivalve", "biotronik", "gore", "jena",
    "the", "system", "inc", "sas", "ltd", "co",
}
@dataclass
class Candidate:
    """A PubMed record, parsed to just the fields the scorer needs."""
    pmid: str = ""
    doi: str = ""
    title: str = ""
    abstract: str = ""
    authors: List[str] = field(default_factory=list)   # "Surname II"
    journal: str = ""
    year: str = ""
    pubtypes: List[str] = field(default_factory=list)   # lowercased
    nct_accessions: List[str] = field(default_factory=list)
    volume: str = ""
    issue: str = ""
    pages: str = ""
@dataclass
class Trial:
    """Only the fields the linker reasons over (a subset of the site's Trial)."""
    acronym: str = ""
    nct: str = ""
    authors: str = ""            # "Sorajja P, Whisenant B, et al."
    journal: str = ""
    year: str = ""
    device: str = ""
    valve: str = ""              # Aortic / Mitral / Tricuspid
    disease: str = ""
    procedure: str = ""
    sample_size: str = ""
# --------------------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------------------
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()
def _acronym_variants(acr: str) -> List[str]:
    """'TRI-FR' -> ['tri-fr','tri fr','trifr']; strip parentheticals."""
    a = re.sub(r"\(.*?\)", " ", acr or "").strip().lower()
    a = re.sub(r"\s+", " ", a)
    if not a:
        return []
    v = {a, a.replace("-", " "), a.replace("-", ""), a.replace(" ", "")}
    return [x for x in v if x]
def _whole_word_hit(text: str, needle: str) -> bool:
    if not needle:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", text) is not None
def _first_author_surname(authors_str: str) -> str:
    """'Sorajja P, Whisenant B, et al.' -> 'sorajja'."""
    first = (authors_str or "").split(",")[0].strip()
    first = re.sub(r"\b(et al\.?)\b", "", first, flags=re.I).strip()
    # 'Sorajja P' -> surname is everything except a trailing initials token
    parts = first.split()
    if len(parts) >= 2 and re.fullmatch(r"[A-Za-z]{1,3}\.?", parts[-1]):
        parts = parts[:-1]
    return _norm(" ".join(parts))
def _all_surnames(authors_str: str) -> List[str]:
    out = []
    for chunk in (authors_str or "").split(","):
        chunk = re.sub(r"\b(et al\.?)\b", "", chunk, flags=re.I).strip()
        if not chunk:
            continue
        parts = chunk.split()
        if len(parts) >= 2 and re.fullmatch(r"[A-Za-z]{1,3}\.?", parts[-1]):
            parts = parts[:-1]
        s = _norm(" ".join(parts))
        if s:
            out.append(s)
    return out
def _year_int(y) -> Optional[int]:
    m = re.search(r"\d{4}", str(y or ""))
    return int(m.group()) if m else None
def _device_token(device: str) -> str:
    """Vendor-stripped device model, e.g. 'Jenscare LuX-Valve / ...' -> 'lux-valve'."""
    dev = _norm(re.split(r"[/(]", device or "")[0])
    toks = [t for t in dev.split() if t not in VENDOR_WORDS]
    return " ".join(toks).strip() or (dev.split()[0] if dev else "")
# --------------------------------------------------------------------------------------
# Classification: primary vs subanalysis/follow-up vs mention
# --------------------------------------------------------------------------------------
def _concept_terms(trial: Trial):
    """Extract (device, valve, procedure) keywords a human would look for together."""
    dev = _device_token(trial.device)
    dev = dev.split()[0] if dev else ""                       # e.g. 'mitraclip', 'pascal', 'lux-valve'
    valve = _norm(trial.valve) or ""
    if not valve:                                            # fall back to disease text
        for v in ("tricuspid", "mitral", "aortic"):
            if v in _norm(trial.disease):
                valve = v
                break
    proc = ""
    p = _norm(trial.procedure) + " " + _norm(trial.acronym)
    if "edge-to-edge" in p or "teer" in p:
        proc = "edge-to-edge"
    elif "annuloplasty" in p:
        proc = "annuloplasty"
    elif "valve-in-valve" in p or "viv" in p:
        proc = "valve-in-valve"
    elif "replacement" in p or "tmvr" in p or "ttvr" in p:
        proc = "replacement"
    elif "repair" in p:
        proc = "repair"
    return dev, valve, proc
def topic_signal(trial: Trial, cand: Candidate):
    """+points when device + valve (+procedure) co-occur -> the paper is ABOUT this concept."""
    dev, valve, proc = _concept_terms(trial)
    title = _norm(cand.title)
    both = title + " . " + _norm(cand.abstract)
    if not (dev and valve):
        return 0, None
    dev_hit, valve_hit = dev in both, valve in both
    if dev_hit and valve_hit:
        in_title = dev in title and valve in title
        pts = 15 if in_title else 9
        note = f"device+valve co-occur ('{dev}'+'{valve}')" + (" in title" if in_title else "")
        if proc and proc in both:
            pts += 3
            note += f" + procedure ('{proc}')"
        return pts, f"+{pts} topic match: {note} — paper is about this intervention"
    if dev_hit or valve_hit:
        return 5, f"+5 partial topic match ({'device' if dev_hit else 'valve'} only)"
    return 0, None
def fingerprint_signal(trial: Trial, cand: Candidate):
    """+points when the trial's own sample size shows up as the study's N in the abstract."""
    m = re.search(r"\d{2,4}", trial.sample_size or "")
    if not m:
        return 0, None
    n = m.group()
    abst = _norm(cand.abstract)
    if re.search(rf"\b{n}\b[^.]{{0,30}}\b(patient|subject|consecutive|participant)", abst) or \
       re.search(rf"\b(included|enrolled|treated|total of)\b[^.]{{0,20}}\b{n}\b", abst):
        return 10, f"+10 content fingerprint: study N ({n}) matches the abstract"
    return 0, None
def classify_kind(cand: Candidate, acronym: str) -> str:
    pts = set(cand.pubtypes)
    text = _norm(cand.title + " . " + cand.abstract)
    title = _norm(cand.title)
    variants = _acronym_variants(acronym)
    in_title = any(_whole_word_hit(title, v) for v in variants)
    if pts & SECONDARY_PUBTYPES and not (pts & PRIMARY_PUBTYPES):
        return "mention"                    # review/editorial/meta -> secondary literature
    if in_title and any(re.search(c, title) for c in SUBSTUDY_CUES):
        return "subanalysis"
    if in_title and any(re.search(c, text) for c in SUBSTUDY_CUES) and (pts & PRIMARY_PUBTYPES):
        return "subanalysis"
    if (pts & PRIMARY_PUBTYPES) and in_title:
        return "primary"
    if (pts & PRIMARY_PUBTYPES):
        return "primary"                    # trial pubtype but acronym elsewhere/absent
    return "mention"
# --------------------------------------------------------------------------------------
# The scorer: transparent, weighted, auditable.  Returns 0-100 + per-signal reasons.
# --------------------------------------------------------------------------------------
def score_candidate(trial: Trial, cand: Candidate) -> dict:
    reasons: List[str] = []
    score = 0.0
    acr = _norm(trial.acronym)
    variants = _acronym_variants(trial.acronym)
    title = _norm(cand.title)
    abstract = _norm(cand.abstract)
    pts = set(cand.pubtypes)
    ambiguous = acr in AMBIGUOUS_ACRONYMS or len(acr.replace(" ", "")) <= 4
    # --- 1. Registry link: the single most reliable signal ---------------------------
    nct_match = bool(trial.nct) and trial.nct.upper() in {a.upper() for a in cand.nct_accessions}
    if nct_match:
        score += 55
        reasons.append("+55 registry link: paper declares this trial's NCT ([si] match)")
    # --- 2. Acronym location ----------------------------------------------------------
    in_title = any(_whole_word_hit(title, v) for v in variants)
    in_abstract = any(_whole_word_hit(abstract, v) for v in variants)
    # Is the abstract hit a *named study* usage or a *comparator* usage?
    named_ctx = comparator_ctx = False
    if in_abstract:
        for v in variants:
            for m in re.finditer(re.escape(v), abstract):
                window = abstract[max(0, m.start() - 40): m.end() + 40]
                if re.search(r"\b(trial|study|investigators|registry|cohort)\b", window) or \
                   re.search(r"\b(the|in|of)\s+" + re.escape(v), window):
                    named_ctx = True
                if any(re.search(c, window) for c in COMPARATOR_CUES):
                    comparator_ctx = True
    title_pts = 30
    abs_pts = 12 if named_ctx else (3 if in_abstract else 0)
    if ambiguous and not (nct_match):
        # Guilty until corroborated: heavily discount bare acronym hits for common words.
        title_pts *= 0.4
        abs_pts *= 0.35
        reasons.append(f"(acronym '{trial.acronym}' is ambiguous -> acronym hits discounted)")
    if in_title:
        score += title_pts
        reasons.append(f"+{title_pts:.0f} acronym in TITLE")
    if in_abstract and abs_pts:
        score += abs_pts
        reasons.append(f"+{abs_pts:.0f} acronym in abstract"
                       + (" (named-study context)" if named_ctx else ""))
    if comparator_ctx and not in_title and not nct_match:
        score -= 18
        reasons.append("-18 acronym used only as a comparator/reference (a mention)")
    # --- 3. Author match --------------------------------------------------------------
    t_first = _first_author_surname(trial.authors)
    c_surnames = _all_surnames(", ".join(cand.authors)) or [_first_author_surname(a) for a in cand.authors]
    c_surnames = [s for s in c_surnames if s]
    if t_first and cand.authors:
        cand_first = _first_author_surname(cand.authors[0]) if cand.authors else ""
        if cand_first and cand_first == t_first:
            score += 18
            reasons.append(f"+18 first author matches ({t_first.title()})")
        elif t_first in c_surnames:
            score += 8
            reasons.append(f"+8 known trial author present ({t_first.title()})")
    # --- 4. Publication type ----------------------------------------------------------
    if pts & PRIMARY_PUBTYPES:
        score += 12
        reasons.append("+12 publication type is a trial report (RCT/clinical/multicenter)")
    if pts & SECONDARY_PUBTYPES and not (pts & PRIMARY_PUBTYPES):
        score -= 25
        reasons.append("-25 publication type is secondary literature (review/editorial/meta)")
    # --- 5. Journal & year fit --------------------------------------------------------
    if trial.journal and cand.journal:
        tj, cj = _norm(trial.journal), _norm(cand.journal)
        if tj == cj or tj in cj or cj in tj:
            score += 8
            reasons.append("+8 journal matches expected")
    ty, cy = _year_int(trial.year), _year_int(cand.year)
    if ty and cy:
        if abs(ty - cy) <= 1:
            score += 6
            reasons.append("+6 year within +/-1 of expected")
        elif abs(ty - cy) >= 6:
            score -= 6
            reasons.append("-6 year far from expected")
    # --- 6. Device name (vendor-stripped) --------------------------------------------
    device_in_title = False
    if trial.device:
        dev = _device_token(trial.device)
        if dev and (dev in title or dev in abstract):
            score += 8
            reasons.append(f"+8 device name present ('{dev}')")
            device_in_title = dev in title
    # --- 7. Topic match (device+valve+procedure) and content fingerprint (N) ---------
    tpts, tnote = topic_signal(trial, cand)
    if tpts:
        score += tpts
        reasons.append(tnote)
    fpts, fnote = fingerprint_signal(trial, cand)
    if fpts:
        score += fpts
        reasons.append(fnote)
    score = max(0.0, min(100.0, score))
    # Ambiguous bare-word acronyms (TRAVEL, SCOUT, HOVER...) need corroboration. STRONG
    # CONTENT evidence — device name in the title, an exact sample-size fingerprint, or a
    # full device+valve+procedure topic match — now counts too, not only NCT/author. This
    # surfaces papers like the TRAVEL/LuX-Valve study the bare acronym would otherwise cap.
    author_match = bool(t_first) and t_first in c_surnames
    strong_content = device_in_title or (fpts > 0) or (tpts >= 12)
    if ambiguous and not (nct_match or author_match or strong_content) and score > 40:
        score = 40.0
        reasons.append("(capped at 40: ambiguous acronym without corroboration)")
    elif ambiguous and not (nct_match or author_match) and strong_content:
        reasons.append("(ambiguous acronym, but strong content corroboration — cap lifted)")
    label = "HIGH" if score >= 75 else ("MEDIUM" if score >= 45 else "LOW")
    return {
        "pmid": cand.pmid, "doi": cand.doi, "title": cand.title,
        "score": round(score, 1), "confidence": label,
        "kind": classify_kind(cand, trial.acronym),
        "nct_declared": list(cand.nct_accessions),   # discover_updates uses this to self-heal/review
        "reasons": reasons,
    }
# --------------------------------------------------------------------------------------
# Query construction
# --------------------------------------------------------------------------------------
def build_queries(trial: Trial) -> List[tuple]:
    """Ordered (strategy, query) pairs; the caller runs them until it has enough."""
    q = []
    if trial.nct:
        q.append(("registry", f"{trial.nct}[si]"))          # most reliable
    acr = re.sub(r"\(.*?\)", " ", trial.acronym or "").strip()
    first = _first_author_surname(trial.authors)
    if acr and first:
        q.append(("acronym+author", f'"{acr}" AND {first}[Author]'))
    if acr:
        q.append(("acronym", f'"{acr}"'))
    # Device query: catches trials with no NCT and a title that hides the acronym
    # (e.g. TRAVEL's "the Novel System") by anchoring on the device model + valve.
    dev = _device_token(trial.device)
    if dev and trial.valve:
        q.append(("device", f'"{dev}" AND {trial.valve.lower()}[tiab]'))
    return q
# --------------------------------------------------------------------------------------
# Live PubMed client (E-utilities).  Needs internet; parses just what the scorer needs.
# --------------------------------------------------------------------------------------
class PubMedClient:
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    def __init__(self, api_key: Optional[str] = None, tool="valvetrials", email=""):
        self.api_key, self.tool, self.email = api_key, tool, email
    def _get(self, endpoint: str, params: dict) -> bytes:
        import urllib.parse
        import urllib.request
        params = {**params, "tool": self.tool, "email": self.email}
        if self.api_key:
            params["api_key"] = self.api_key
        url = f"{self.BASE}/{endpoint}?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
        time.sleep(0.11 if self.api_key else 0.34)   # respect NCBI rate limits
        return data
    def esearch(self, term: str, retmax=20, reldate=None, datetype=None) -> List[str]:
        import xml.etree.ElementTree as ET
        params = {"db": "pubmed", "term": term, "retmax": retmax}
        if reldate:                       # e.g. reldate=45 -> last 45 days
            params["reldate"] = int(reldate)
            params["datetype"] = datetype or "pdat"   # pdat=publication, edat=entrez
        xml = self._get("esearch.fcgi", params)
        root = ET.fromstring(xml)
        return [e.text for e in root.findall(".//IdList/Id")]
    def efetch(self, pmids: List[str]) -> List[Candidate]:
        import xml.etree.ElementTree as ET
        if not pmids:
            return []
        xml = self._get("efetch.fcgi", {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
        root = ET.fromstring(xml)
        out = []
        for art in root.findall(".//PubmedArticle"):
            c = Candidate()
            c.pmid = (art.findtext(".//PMID") or "").strip()
            c.title = (art.findtext(".//ArticleTitle") or "").strip()
            c.abstract = " ".join(t.text or "" for t in art.findall(".//AbstractText")).strip()
            c.journal = (art.findtext(".//Journal/Title") or "").strip()
            c.year = (art.findtext(".//JournalIssue/PubDate/Year")
                      or art.findtext(".//JournalIssue/PubDate/MedlineDate") or "").strip()
            c.volume = (art.findtext(".//JournalIssue/Volume") or "").strip()
            c.issue = (art.findtext(".//JournalIssue/Issue") or "").strip()
            c.pages = (art.findtext(".//Pagination/MedlinePgn") or "").strip()
            for a in art.findall(".//AuthorList/Author"):
                ln, ini = a.findtext("LastName"), a.findtext("Initials")
                if ln:
                    c.authors.append(f"{ln} {ini or ''}".strip())
            c.pubtypes = [_norm(p.text) for p in art.findall(".//PublicationTypeList/PublicationType")]
            for db in art.findall(".//DataBankList/DataBank"):
                if _norm(db.findtext("DataBankName")) in ("clinicaltrials.gov", "clinicaltrials"):
                    c.nct_accessions += [ (x.text or "").strip()
                                          for x in db.findall(".//AccessionNumber") ]
            for aid in art.findall(".//ArticleIdList/ArticleId"):
                if aid.get("IdType") == "doi":
                    c.doi = (aid.text or "").strip()
            out.append(c)
        return out
def link_trial(trial: Trial, client: PubMedClient, retmax=15) -> List[dict]:
    """Run the strategies, dedupe by PMID, score, and return ranked results."""
    seen, cands = set(), []
    for _strategy, term in build_queries(trial):
        pmids = [p for p in client.esearch(term, retmax=retmax) if p not in seen]
        seen.update(pmids)
        cands += client.efetch(pmids)
        if len([c for c in cands]) >= retmax:
            pass  # keep gathering across strategies; dedupe already handled
    scored = [score_candidate(trial, c) for c in cands]
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored
# --------------------------------------------------------------------------------------
# Offline self-test: proves the logic on the exact cases the user described.
# --------------------------------------------------------------------------------------
def _selftest() -> int:
    cases = []
    # 1) Primary RCT, acronym in title, NCT linked -> HIGH / primary
    cases.append((
        "TRILUMINATE Pivotal primary",
        Trial(acronym="TRILUMINATE Pivotal", nct="NCT03904147",
              authors="Sorajja P, Whisenant B, et al.", journal="N Engl J Med", year="2023"),
        Candidate(pmid="36876753", title="Transcatheter Repair for Patients with Tricuspid Regurgitation",
                  abstract="In this randomized TRILUMINATE Pivotal trial ...",
                  authors=["Sorajja P", "Whisenant B"], journal="The New England journal of medicine",
                  year="2023", pubtypes=["randomized controlled trial", "multicenter study"],
                  nct_accessions=["NCT03904147"]),
        ("HIGH", "primary"),
    ))
    # 2) Review that merely MENTIONS TRILUMINATE, no NCT -> LOW / mention
    cases.append((
        "Review mentioning TRILUMINATE",
        Trial(acronym="TRILUMINATE Pivotal", nct="NCT03904147",
              authors="Sorajja P, et al.", journal="N Engl J Med", year="2023"),
        Candidate(pmid="99999991", title="Transcatheter therapies for tricuspid regurgitation: a review",
                  abstract="We review devices; compared with TRILUMINATE, other systems ...",
                  authors=["Doe J"], journal="Reviews in Cardiology", year="2024",
                  pubtypes=["review"], nct_accessions=[]),
        ("LOW", "mention"),
    ))
    # 3) Ambiguous acronym SCOUT but registry + author corroborate -> HIGH / primary
    cases.append((
        "SCOUT (ambiguous) with NCT + author",
        Trial(acronym="SCOUT", nct="NCT02574650",
              authors="Hahn RT, Meduri CU, et al.", journal="J Am Coll Cardiol", year="2017"),
        Candidate(pmid="28385308", title="Early Feasibility Study of a Transcatheter Tricuspid Valve Annuloplasty: SCOUT Trial 30-Day Results",
                  abstract="The SCOUT trial evaluated the Trialign system ...",
                  authors=["Hahn RT", "Meduri CU"], journal="Journal of the American College of Cardiology",
                  year="2017", pubtypes=["clinical trial", "multicenter study"],
                  nct_accessions=["NCT02574650"]),
        ("HIGH", "primary"),
    ))
    # 4) Ambiguous acronym SCOUT matched only by the word, unrelated paper -> LOW
    cases.append((
        "SCOUT bare word, unrelated",
        Trial(acronym="SCOUT", nct="NCT02574650",
              authors="Hahn RT, et al.", journal="J Am Coll Cardiol", year="2017"),
        Candidate(pmid="99999992", title="A SCOUT imaging protocol for abdominal CT",
                  abstract="The scout view was used to plan acquisition ...",
                  authors=["Smith A"], journal="Radiology", year="2015",
                  pubtypes=["journal article"], nct_accessions=[]),
        ("LOW", "mention"),
    ))
    # 5) Subanalysis: acronym in title + substudy cue + trial pubtype -> HIGH / subanalysis
    cases.append((
        "TRILUMINATE renal/liver subanalysis",
        Trial(acronym="TRILUMINATE Pivotal", nct="NCT03904147",
              authors="Jorde UP, et al.", journal="J Am Coll Cardiol", year="2024"),
        Candidate(pmid="39222896", title="Impact of Renal and Liver Function on Outcomes Following Tricuspid TEER: the TRILUMINATE Pivotal Trial",
                  abstract="This secondary analysis of the TRILUMINATE Pivotal trial ...",
                  authors=["Jorde UP"], journal="Journal of the American College of Cardiology",
                  year="2024", pubtypes=["journal article", "multicenter study"],
                  nct_accessions=["NCT03904147"]),
        ("HIGH", "subanalysis"),
    ))
    # 6) No abstract, acronym NOT in title, but NCT + author + RCT -> HIGH / primary
    cases.append((
        "No abstract, name absent, NCT carries it",
        Trial(acronym="CLASP II TR", nct="NCT04097145",
              authors="Hahn RT, et al.", journal="JACC Cardiovasc Interv", year="2025"),
        Candidate(pmid="99999993", title="Transcatheter valve repair in tricuspid regurgitation: a pivotal randomized trial",
                  abstract="", authors=["Hahn RT"], journal="JACC: Cardiovascular Interventions",
                  year="2025", pubtypes=["randomized controlled trial"],
                  nct_accessions=["NCT04097145"]),
        ("HIGH", "primary"),
    ))
    # 7) No name, no NCT, weak pubtype -- resolved by topic + fingerprint + author
    cases.append((
        "MitraClip-in-TR (no acronym, no NCT)",
        Trial(acronym="MitraClip in TR (early)", nct="", authors="Nickenig G, Kowalski M, et al.",
              journal="Circulation", year="2017", device="Abbott MitraClip",
              valve="Tricuspid", procedure="TEER (off-label MitraClip)", sample_size="64"),
        Candidate(pmid="28336788", doi="10.1161/CIRCULATIONAHA.116.024848",
                  title="Transcatheter Treatment of Severe Tricuspid Regurgitation With the Edge-to-Edge MitraClip Technique",
                  abstract=("In the present observational study the safety and feasibility of transcatheter repair of "
                            "chronic severe TR with the MitraClip system were evaluated. We included 64 consecutive "
                            "patients deemed unsuitable for surgery."),
                  authors=["Nickenig G", "Kowalski M"], journal="Circulation", year="2017",
                  pubtypes=["observational study"], nct_accessions=[]),
        ("HIGH", "primary"),
    ))
    # 8) TRAVEL/LuX-Valve: ambiguous bare word, title hides device, NO NCT match, but strong
    #    content (device+valve+procedure topic) lifts the cap -> MEDIUM instead of capped LOW.
    cases.append((
        "TRAVEL/LuX-Valve (ambiguous, no NCT, strong content)",
        Trial(acronym="TRAVEL", nct="", authors="", device="Jenscare LuX-Valve / LuX-Valve Plus",
              valve="Tricuspid", procedure="Transcatheter tricuspid replacement", sample_size="126"),
        Candidate(pmid="40208152", doi="10.1016/j.jcin.2024.12.030",
                  title="Transcatheter Tricuspid Valve Replacement With the Novel System: 1-Year Outcomes From the TRAVEL Study",
                  abstract=("The TRAVEL study with the LuX-Valve system for severe TR. 126 patients underwent "
                            "TTVR using the LuX-Valve system."),
                  authors=["Pan X"], journal="JACC Cardiovasc Interv", year="2025",
                  pubtypes=["journal article", "multicenter study"], nct_accessions=["NCT04436653"]),
        ("MEDIUM", "subanalysis"),
    ))
    ok = 0
    for name, trial, cand, (exp_label, exp_kind) in cases:
        r = score_candidate(trial, cand)
        passed = r["confidence"] == exp_label and r["kind"] == exp_kind
        ok += passed
        flag = "PASS" if passed else "FAIL"
        print(f"[{flag}] {name}")
        print(f"        score={r['score']:5.1f}  confidence={r['confidence']:6s}  "
              f"kind={r['kind']:11s}  (expected {exp_label}/{exp_kind})")
        for why in r["reasons"]:
            print(f"           {why}")
        print()
    print(f"{ok}/{len(cases)} cases passed")
    return 0 if ok == len(cases) else 1
def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Link trials to PubMed papers with confidence.")
    ap.add_argument("--selftest", action="store_true", help="run offline logic tests (no network)")
    ap.add_argument("--file", help="a trials_*.json file to scan for trials missing a pmid")
    ap.add_argument("--acronym"); ap.add_argument("--nct"); ap.add_argument("--authors", default="")
    ap.add_argument("--journal", default=""); ap.add_argument("--year", default="")
    ap.add_argument("--apply-high", action="store_true",
                    help="write back doi/pmid for HIGH-confidence PRIMARY hits (with --file)")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    client = PubMedClient(api_key=__import__("os").environ.get("NCBI_API_KEY"))
    if args.acronym:
        t = Trial(acronym=args.acronym, nct=args.nct or "", authors=args.authors,
                  journal=args.journal, year=args.year)
        for r in link_trial(t, client)[:8]:
            print(f"{r['confidence']:6s} {r['score']:5.1f} [{r['kind']:11s}] "
                  f"PMID {r['pmid']:>9} doi:{r['doi'] or '-'}\n        {r['title']}")
        return 0
    if args.file:
        data = json.load(open(args.file, encoding="utf-8"))
        changed = 0
        for row in data:
            if row.get("status") != "published" or row.get("doi") or row.get("pmid"):
                continue
            t = Trial(acronym=row.get("acronym", ""), nct=row.get("nct", ""),
                      authors=row.get("authors", ""), journal=row.get("journal", ""),
                      year=row.get("year", ""), device=row.get("device", ""),
                      valve=row.get("valve", ""), disease=row.get("disease", ""),
                      procedure=row.get("procedure", ""), sample_size=row.get("sample_size", ""))
            ranked = link_trial(t, client)
            top = ranked[0] if ranked else None
            print(f"\n### {row['acronym']}  (NCT {t.nct or '-'})")
            for r in ranked[:5]:
                print(f"  {r['confidence']:6s} {r['score']:5.1f} [{r['kind']:11s}] "
                      f"PMID {r['pmid']:>9}  {r['title'][:70]}")
            if args.apply_high and top and top["confidence"] == "HIGH" and top["kind"] == "primary":
                row["pmid"] = top["pmid"]
                if top["doi"]:
                    row["doi"] = top["doi"]
                changed += 1
                print(f"  -> applied PMID {top['pmid']}")
        if args.apply_high and changed:
            json.dump(data, open(args.file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"\nWrote {changed} high-confidence links to {args.file}")
        return 0
    ap.print_help()
    return 0
if __name__ == "__main__":
    sys.exit(_cli())
