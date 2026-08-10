#!/usr/bin/env python3
"""
valve_trials.py — Build ValveTrials.org (multi-page static site).
"""
from __future__ import annotations
import html
import math
import os
import re
import sys
from urllib.parse import quote
from typing import List, Tuple
from model import Trial, CATEGORIES
from data import TRIALS
EXCLUDE_SIGNALS = {"negative"}
# --- Valves (home tiles + pages) --------------------------------------------
VALVES = [
    ("aortic", "Aortic", "#146C7A", 3, ""),
    ("mitral", "Mitral", "#B23A5B", 2, ""),
    ("tricuspid", "Tricuspid", "#6D5AB6", 3, ""),
]
VALVE_LABEL = {k: lbl for k, lbl, _, _, _ in VALVES}
VALVE_HUE = {k: h for k, _, h, _, _ in VALVES}
PLANNED_SECTIONS = {
    "mitral": ["Secondary MR — TEER", "Primary / degenerative MR",
               "Transcatheter mitral replacement (TMVR)",
               "Mitral valve-in-valve / valve-in-ring", "Frontier / next-gen devices"],
    "tricuspid": ["Functional TR — TEER", "Orthotopic transcatheter replacement",
                  "Heterotopic / caval valve implantation",
                  "Annuloplasty & repair devices", "Frontier / next-gen devices"],
}
CATEGORY_HUE = {
    "Inoperable / High-Risk AS":  "#B03A2E",
    "Intermediate-Risk AS":       "#B9770E",
    "Low-Risk AS":                "#1F7A5A",
    "Platform Comparison":        "#4A5D75",
    "Asymptomatic / Timing":      "#7A57C4",
    "Moderate AS":                "#0E7C86",
    "Valve-in-Valve / Redo":      "#A6572B",
    "Bicuspid":                   "#8E44AD",
    "Aortic Regurgitation":       "#B0344B",
    "Frontier / Next-Gen Device": "#2C6E8F",
    "Mitral TEER — Primary / Degenerative MR":   "#C0392B",
    "Mitral TEER — Secondary / Functional MR":   "#B23A5B",
    "Secondary MR — Direct Annuloplasty":        "#A6572B",
    "Secondary MR — Indirect Annuloplasty":      "#C77A2B",
    "Mitral Chordal Repair":                     "#1F7A5A",
    "Transcatheter Mitral Replacement (TMVR)":   "#2C6E8F",
    "Mitral Valve-in-Valve / Ring / MAC":        "#6D5AB6",
    "Tricuspid TEER":                            "#6D5AB6",
    "Tricuspid Transcatheter Replacement (TTVR)":"#4E63B6",
    "Tricuspid Annuloplasty":                    "#8E5AB6",
    "Tricuspid Heterotopic / Caval":             "#B65AA0",
    "Tricuspid Frontier / Next-Gen Device":      "#5A78B6",
}
VALVE_CATEGORIES = {
    "Aortic": [c for c in CATEGORIES if c in {
        "Inoperable / High-Risk AS", "Intermediate-Risk AS", "Low-Risk AS",
        "Platform Comparison", "Asymptomatic / Timing", "Moderate AS",
        "Valve-in-Valve / Redo", "Bicuspid", "Aortic Regurgitation",
        "Frontier / Next-Gen Device"}],
    "Mitral": [c for c in CATEGORIES if c.startswith("Mitral") or c.startswith("Secondary MR")],
    "Tricuspid": [c for c in CATEGORIES if c.startswith("Tricuspid")],
}
STATUS_META = {
    "published":  ("🟢", "Published"),
    "ongoing":    ("🔵", "Ongoing"),
    "terminated": ("⛔", "Terminated"),
}
def e(text) -> str:
    return html.escape(str(text), quote=True)
def link_nct(nct: str) -> str:
    if not nct:
        return ""
    if nct.upper().startswith("ISRCTN"):
        return f"https://www.isrctn.com/{e(nct)}"
    return f"https://clinicaltrials.gov/study/{e(nct)}"
def trials_for(valve_key: str) -> List[Trial]:
    label = VALVE_LABEL[valve_key].lower()
    return [t for t in TRIALS
            if t.signal not in EXCLUDE_SIGNALS and (t.valve or "aortic").lower() == label]
def sort_year(t: Trial) -> int:
    for src in (t.year, t.enrollment):
        if src:
            m = re.search(r"\d{4}", src)
            if m:
                return int(m.group())
    return 9999
# --- paper links -------------------------------------------------------------
def _pubmed_query(t) -> str:
    acr = re.sub(r"\s+", " ", re.sub(r"[()]", " ", t.acronym or "")).strip()
    first_author = t.authors.split(",")[0].strip() if t.authors else ""
    if first_author:
        return f'{acr} AND "{first_author}"[Author]'
    title = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]", " ", t.full_name or acr)).strip()
    return " ".join(b for b in [title, (t.valve or ""), (t.year or "")] if b)
def paper_links(t: Trial) -> List[Tuple[str, str, str]]:
    out: List[Tuple[str, str, str]] = []
    if t.doi:
        out.append(("Read paper (DOI)", f"https://doi.org/{e(t.doi)}", "primary"))
    if t.pmid:
        out.append(("PubMed", f"https://pubmed.ncbi.nlm.nih.gov/{e(t.pmid)}/", "primary"))
    if t.status == "published" and not t.doi and not t.pmid:
        out.append(("Find on PubMed",
                    f"https://pubmed.ncbi.nlm.nih.gov/?term={quote(_pubmed_query(t))}", "search"))
    if t.nct:
        label = "ISRCTN" if t.nct.upper().startswith("ISRCTN") else "ClinicalTrials.gov"
        out.append((label, link_nct(t.nct), "registry"))
    return out
# --- small HTML helpers ------------------------------------------------------
def bullets(items: List[str]) -> str:
    if not items:
        return "<p class='empty'>—</p>"
    return "<ul class='bul'>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"
def result_bullets(items: List[str]) -> str:
    if not items:
        return "<p class='empty'>No results yet — trial ongoing.</p>"
    return "<ul class='results'>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"
def status_badge(t: Trial) -> str:
    icon, label = STATUS_META.get(t.status, ("•", t.status.title()))
    return f"<span class='badge status-{t.status}'>{icon} {e(label)}</span>"
def row_dates(t: Trial) -> str:
    bits = []
    if t.enrollment:
        bits.append(f"<span class='d-enr'>Enrolled {e(t.enrollment)}</span>")
    if t.year:
        bits.append(f"<span class='d-pub'>Published {e(t.year)}</span>")
    elif t.status == "ongoing":
        bits.append("<span class='d-pub'>Not yet published</span>")
    return "<span class='dates'>" + "".join(bits) + "</span>"
def overview_table(t: Trial) -> str:
    rows = [
        ("Device", t.device), ("Intervention", t.intervention), ("Comparator", t.comparator),
        ("Population", t.population), ("Risk group", t.risk_group), ("Sample size", t.sample_size),
        ("Enrollment", t.enrollment), ("Follow-up", t.follow_up), ("Trial type", t.trial_type),
    ]
    body = "".join(f"<tr><th>{e(k)}</th><td>{e(v) if v else '—'}</td></tr>" for k, v in rows)
    return f"<table class='overview'><tbody>{body}</tbody></table>"
def paper_bar(t: Trial) -> str:
    links = paper_links(t)
    if not links:
        return "<div class='paperbar none'>Not yet published — trial ongoing.</div>"
    a = [f"<a class='plink {kind}' href='{url}' target='_blank' rel='noopener'>{e(label)} ↗</a>"
         for label, url, kind in links]
    cite = []
    if t.authors: cite.append(e(t.authors))
    if t.journal: cite.append(f"<em>{e(t.journal)}</em>")
    if t.year: cite.append(e(t.year))
    cite_line = f"<span class='paper-cite'>{' · '.join(cite)}</span>" if cite else ""
    return f"<div class='paperbar'><div class='plinks'>{''.join(a)}</div>{cite_line}</div>"
def _followup_sort_key(p: dict):
    """Order follow-ups sequentially: by publication year, then by the follow-up
    duration named in the label (30-day < 6-month < 1-year < 2-year ...)."""
    cite = p.get("citation", "") or ""
    ym = re.search(r"(?:19|20)\d{2}", cite)
    year = int(ym.group()) if ym else 9999
    label = (p.get("label", "") or "").lower()
    dur = 10 ** 9
    m = re.search(r"(\d+)\s*[- ]?\s*(day|week|month|year|yr|mo|d)\b", label)
    if m:
        mult = {"day": 1, "d": 1, "week": 7, "month": 30, "mo": 30, "year": 365, "yr": 365}
        dur = int(m.group(1)) * mult.get(m.group(2), 365)
    return (year, dur)

def key_papers_section(t: Trial) -> str:
    if not t.key_papers:
        return ""
    papers = sorted(t.key_papers, key=_followup_sort_key)   # sequential order
    rows = []
    for p in papers:
        links = []
        if p.get("doi"):
            links.append(f"<a class='plink primary' href='https://doi.org/{p['doi']}' "
                         f"target='_blank' rel='noopener'>DOI ↗</a>")
        if p.get("pmid"):
            links.append(f"<a class='plink primary' href='https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/' "
                         f"target='_blank' rel='noopener'>PubMed ↗</a>")
        if not links:
            links.append("<span class='pc-nolink'>No direct link on file</span>")
        label = f"<b class='pc-label'>{e(p.get('label',''))}</b> " if p.get("label") else ""
        # Each follow-up is collapsed; click to reveal its paper links.
        rows.append(
            f"<details class='pc'><summary><span class='pc-chev' aria-hidden='true'></span>"
            f"{label}<span class='pc-cite'>{e(p.get('citation',''))}</span></summary>"
            f"<div class='pc-body'>{''.join(links)}</div></details>"
        )
    return (f"<section><h3>Serial follow-ups &amp; subanalyses "
            f"<span class='pc-count'>{len(papers)}</span></h3>"
            f"<p class='pc-hint'>Click a follow-up to reveal its paper links.</p>"
            f"<div class='papers'>{''.join(rows)}</div></section>")
def detail_body(t: Trial) -> str:
    caveat = f"<div class='d-caveat'>⚠ {e(t.caveat)}</div>" if t.caveat else ""
    return f"""
<div class="body-inner">
  {paper_bar(t)}
  {caveat}
  <p class="d-summary">{e(t.quick_summary)}</p>
  <div class="d-grid">
    <div class="d-main">
      <section><h3>Study overview</h3>{overview_table(t)}</section>
      <section><h3>Inclusion criteria</h3>{bullets(t.inclusion)}</section>
      <section><h3>Primary endpoint</h3><p>{e(t.primary_endpoint) or '—'}</p></section>
      <section><h3>Secondary endpoints</h3>{bullets(t.secondary_endpoints)}</section>
      <section><h3>Key results</h3>{result_bullets(t.key_results)}</section>
      <section><h3>Why this trial matters</h3><p>{e(t.why_matters) or '—'}</p></section>
      <section><h3>Clinical pearls</h3>{bullets(t.pearls)}</section>
      <section><h3>Limitations</h3>{bullets(t.limitations)}</section>
      {key_papers_section(t)}
    </div>
    <aside class="d-side">
      <div class="qf"><h4>Quick facts</h4>
        <dl>
          <dt>Valve</dt><dd>{e(t.valve) or '—'}</dd>
          <dt>Disease</dt><dd>{e(t.disease) or '—'}</dd>
          <dt>Procedure</dt><dd>{e(t.procedure) or '—'}</dd>
          <dt>Sample</dt><dd>{e(t.sample_size) or '—'}</dd>
          <dt>Follow-up</dt><dd>{e(t.follow_up) or '—'}</dd>
        </dl>
      </div>
      <div class="qf"><h4>Guidelines</h4>
        <p class="lab">ACC / AHA</p><p>{e(t.guideline_acc) or '—'}</p>
        <p class="lab">ESC / EACTS</p><p>{e(t.guideline_esc) or '—'}</p>
      </div>
      <div class="qf"><h4>FDA / regulatory</h4><p>{e(t.fda_impact) or '—'}</p></div>
      <div class="qf"><h4>Timeline</h4>{bullets(t.timeline)}</div>
    </aside>
  </div>
</div>
""".strip()
def render_row(t: Trial) -> str:
    hue = CATEGORY_HUE.get(t.category, "#4A5D75")
    haystack = " ".join([t.acronym, t.full_name, t.device, t.comparator, t.population,
                         t.nct, t.category, " ".join(t.tags)]).lower()
    caveat_dot = "<span class='cav-dot' title='See caveat inside'>⚠</span>" if t.caveat else ""
    nfu = len(t.key_papers or [])
    fu_badge = (f"<span class='badge fu' title='Has {nfu} follow-up / subanalysis paper(s)'>"
                f"{nfu} follow-up{'s' if nfu != 1 else ''}</span>") if nfu else ""
    return f"""
<details class="row" style="--hue:{hue}" data-cat="{e(t.category)}"
         data-status="{e(t.status)}" data-signal="{e(t.signal)}"
         data-pc="{'1' if t.practice_changing else '0'}" data-fu="{'1' if nfu else '0'}"
         data-search="{e(haystack)}">
  <summary>
    <span class="chev" aria-hidden="true"></span>
    <span class="row-id">
      <span class="row-acr">{e(t.acronym)} {caveat_dot}</span>
      <span class="row-name">{e(t.full_name)}</span>
    </span>
    <span class="row-take">{e(t.takeaway or t.quick_summary)}</span>
    <span class="row-meta">{status_badge(t)}{fu_badge}{row_dates(t)}</span>
  </summary>
  {detail_body(t)}
</details>
""".strip()
def category_chips(trials: List[Trial]) -> str:
    present = [c for c in CATEGORIES if any(t.category == c for t in trials)]
    out = ["<button class='fchip active' data-filter='all'>All</button>"]
    for c in present:
        hue = CATEGORY_HUE.get(c, "#4A5D75")
        n = sum(1 for t in trials if t.category == c)
        out.append(f"<button class='fchip' data-filter='cat' data-value=\"{e(c)}\" "
                   f"style='--hue:{hue}'>{e(c)} <span class='fn'>{n}</span></button>")
    return "".join(out)
def render_list(trials: List[Trial]) -> str:
    present = [c for c in CATEGORIES if any(t.category == c for t in trials)]
    blocks = []
    for c in present:
        hue = CATEGORY_HUE.get(c, "#4A5D75")
        members = sorted([t for t in trials if t.category == c], key=sort_year)
        rows = "".join(render_row(t) for t in members)
        blocks.append(
            f"<details class='group' data-cat=\"{e(c)}\" style='--hue:{hue}' open>"
            f"<summary class='grouphead'><span class='gchev' aria-hidden='true'></span>"
            f"<span class='dot'></span>{e(c)}<span class='gcount'>{len(members)}</span></summary>"
            f"<div class='rows'>{rows}</div></details>"
        )
    return "".join(blocks)
def valve_glyph(n_leaflets: int, hue: str) -> str:
    cx, cy, r = 50, 50, 38
    parts = [f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{hue}' fill-opacity='0.08' "
             f"stroke='{hue}' stroke-width='2.5'/>"]
    if n_leaflets == 2:
        parts.append(f"<path d='M{cx-r+4},{cy-3} Q{cx},{cy+10} {cx+r-4},{cy-3}' fill='none' "
                     f"stroke='{hue}' stroke-width='2.5' stroke-linecap='round'/>")
    else:
        for a in (90, 210, 330):
            rad = math.radians(a)
            x = cx + r * math.cos(rad)
            y = cy + r * math.sin(rad)
            parts.append(f"<line x1='{cx}' y1='{cy}' x2='{x:.1f}' y2='{y:.1f}' "
                         f"stroke='{hue}' stroke-width='2.5' stroke-linecap='round'/>")
    parts.append(f"<circle cx='{cx}' cy='{cy}' r='2.6' fill='{hue}'/>")
    return f"<svg viewBox='0 0 100 100' class='vglyph' aria-hidden='true'>{''.join(parts)}</svg>"
# --- shared shell ------------------------------------------------------------
def site_header(active: str) -> str:
    nav = "".join(
        f"<a href='{k}.html' class='{'active' if k == active else ''}'>{e(lbl)}</a>"
        for k, lbl, _, _, _ in VALVES
    )
    return f"""
<header class="site">
  <a class="brand" href="index.html">Valve<span>Trials</span>.org</a>
  <nav class="site-nav">{nav}</nav>
</header>""".strip()
def page_shell(title: str, active: str, body: str, script: str = "") -> str:
    js = f"<script>{script}</script>" if script else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
{site_header(active)}
{body}
<footer class="pagefoot">
  ValveTrials.org — a cardiology valve-trial reference. ⚠ flags provisional or context items. A reference aid, not clinical advice.
</footer>
{js}
</body>
</html>
"""
# --- home --------------------------------------------------------------------
def build_home() -> str:
    cards = []
    for k, lbl, hue, leaflets, desc in VALVES:
        ts = trials_for(k)
        n = len(ts)
        if n:
            pub = sum(1 for t in ts if t.status == "published")
            ong = sum(1 for t in ts if t.status == "ongoing")
            term = sum(1 for t in ts if t.status == "terminated")
            seg = [f"{pub} published"]
            if ong:
                seg.append(f"{ong} ongoing")
            if term:
                seg.append(f"{term} terminated")
            analyses = sum(len(getattr(t, "key_papers", []) or []) for t in ts)
            pill = f"<span class='pill'>{' · '.join(seg)}</span>"
            an_txt = f" · {analyses} analyses" if analyses else ""
            go = f"<span class='go'>{n} trials{an_txt} →</span>"
            soon = ""
        else:
            pill = "<span class='pill'>In progress</span>"
            go = "<span class='go'>Coming soon →</span>"
            soon = " soon"
        cards.append(
            f"<a class='vcard{soon}' href='{k}.html' style='--vhue:{hue}'>"
            f"{valve_glyph(leaflets, hue)}"
            f"<h2>{e(lbl)}</h2><p>{e(desc)}</p>{pill}{go}</a>"
        )
    body = f"""
<main class="home">
  <p class="kicker">Cardiology · Valvular Heart Disease · Trial Reference</p>
  <h1 class="home-h1">Every landmark valve trial, in one place.</h1>
  <p class="home-lede">Choose a valve to browse its trials — grouped by category, ordered oldest to newest.</p>
  <div class="valve-cards">{''.join(cards)}</div>
</main>
"""
    return page_shell("ValveTrials.org — Valve Trial Reference", "home", body)
# --- aortic (full list) ------------------------------------------------------
def build_valve_list_page(valve_key: str) -> str:
    lbl = VALVE_LABEL[valve_key]
    trials = sorted(trials_for(valve_key), key=sort_year)
    n = len(trials)
    n_pub = sum(1 for t in trials if t.status == "published")
    n_ongoing = sum(1 for t in trials if t.status == "ongoing")
    n_excluded = sum(1 for t in TRIALS
                     if (t.valve or "aortic").lower() == lbl.lower() and t.signal in EXCLUDE_SIGNALS)
    n_analyses = sum(len(t.key_papers or []) for t in trials)
    body = f"""
<header class="mast">
  <p class="kicker"><a class="crumb" href="index.html">ValveTrials.org</a> · {e(lbl)}</p>
  <h1>{e(lbl)} Valve Trials</h1>
  <p class="lede">Major transcatheter (and key comparator) {e(lbl.lower())}-valve trials, grouped into
     collapsible categories and ordered oldest to newest. Click any trial to read the full entry and open the paper.</p>
  <p class="meta">{n} trials · {n_pub} published · {n_ongoing} ongoing · {n_analyses} linked analyses · {n_excluded} negative-result trials excluded · antiplatelet/anticoagulant trials excluded by design</p>
  <div class="legend">
    <span>🟢 Published</span><span>🔵 Ongoing</span>
    <span>Sorted oldest → newest within each category</span><span>⚠ Caveat inside</span>
  </div>
</header>
<div class="controls">
  <div class="controls-inner">
    <div class="searchbar">
      <input id="search" type="search" placeholder="Search trial, device, NCT, population…" aria-label="Search trials">
      <div class="seg" data-group="status">
        <button class="active" data-value="all">All</button>
        <button data-value="published">Published</button>
        <button data-value="ongoing">Ongoing</button>
      </div>
      <div class="seg" data-group="pc">
        <button class="active" data-value="0">All</button>

      </div>
      <div class="actions">
        <button id="expandAll">Expand all</button>
        <button id="collapseAll">Collapse all</button>
      </div>
    </div>
    <div class="fchips">{category_chips(trials)}</div>
    <div class="countline"><span id="count">{n} / {n} trials shown</span></div>
  </div>
</div>
<main class="list">
  {render_list(trials)}
  <p id="noresults" class="noresults">No trials match those filters. Clear the search or pick “All”.</p>
</main>
"""
    return page_shell(f"{lbl} Valve Trials — ValveTrials.org", valve_key, body, LIST_JS)
# --- coming-soon page --------------------------------------------------------
def build_coming_soon_page(valve_key: str) -> str:
    lbl = VALVE_LABEL[valve_key]
    hue = VALVE_HUE[valve_key]
    planned = PLANNED_SECTIONS.get(valve_key, [])
    sections = "".join(
        f"<div class='soon-sec'><span class='dot'></span>{e(s)}<span class='soon-tag'>coming soon</span></div>"
        for s in planned
    )
    body = f"""
<header class="mast">
  <p class="kicker"><a class="crumb" href="index.html">ValveTrials.org
  </a> · {e(lbl)}</p>
  <h1>{e(lbl)} Valve Trials</h1>
  <p class="lede">This section is being built. The structure below is reserved — trials will populate
     these categories as we add them.</p>
</header>
<main class="list" style="--hue:{hue}">
  <div class="soon-box">
    <h2>Trials coming soon</h2>
    <p>We’re curating the {e(lbl.lower())} evidence base with the same standardized entries and verified
       paper links as the aortic section.</p>
    <a class="back" href="index.html">← Back to all valves</a>
  </div>
  <h3 class="soon-head">Planned sections</h3>
  <div class="soon-sections">{sections}</div>
</main>
"""
    return page_shell(f"{lbl} Valve Trials — Coming soon — ValveTrials.org", valve_key, body)
# ---------------------------------------------------------------------------
# Editor page — add / edit / delete trials via a form; exports trials.json
# ---------------------------------------------------------------------------
# (key, label, kind). kind: text | textarea | list | select | bool | num
EDITOR_FIELDS = [
    ("__section__", "Identity", None),
    ("acronym", "Acronym *", "text"),
    ("full_name", "Full name", "text"),
    ("nct", "NCT / ISRCTN id", "text"),
    ("__section__", "Classification", None),
    ("valve", "Valve", "select"),
    ("category", "Category", "select"),
    ("status", "Status", "select"),
    ("signal", "Result signal", "select"),
    ("practice_changing", "Practice changing", "bool"),
    ("landmark", "Landmark", "bool"),
    ("caveat", "Caveat (⚠ shown if set)", "text"),
    ("__section__", "One-liners", None),
    ("takeaway", "Takeaway (headline)", "textarea"),
    ("quick_summary", "Quick summary", "textarea"),
    ("__section__", "Study overview", None),
    ("device", "Device", "text"),
    ("intervention", "Intervention", "text"),
    ("comparator", "Comparator", "text"),
    ("population", "Population", "text"),
    ("risk_group", "Risk group", "text"),
    ("sample_size", "Sample size", "text"),
    ("enrollment", "Enrollment years", "text"),
    ("follow_up", "Follow-up", "text"),
    ("trial_type", "Trial type", "text"),
    ("disease", "Disease", "text"),
    ("procedure", "Procedure", "text"),
    ("__section__", "Clinical detail (one item per line)", None),
    ("inclusion", "Inclusion criteria", "list"),
    ("primary_endpoint", "Primary endpoint", "textarea"),
    ("secondary_endpoints", "Secondary endpoints", "list"),
    ("key_results", "Key results", "list"),
    ("why_matters", "Why this trial matters", "textarea"),
    ("pearls", "Clinical pearls", "list"),
    ("limitations", "Limitations", "list"),
    ("tags", "Tags (chips)", "list"),
    ("__section__", "Guidelines / regulatory / timeline", None),
    ("guideline_acc", "ACC / AHA", "textarea"),
    ("guideline_esc", "ESC / EACTS", "textarea"),
    ("fda_impact", "FDA / regulatory", "textarea"),
    ("timeline", "Timeline (one item per line)", "list"),
    ("__section__", "Citation", None),
    ("authors", "Authors", "text"),
    ("journal", "Journal", "text"),
    ("year", "Year", "text"),
    ("doi", "DOI", "text"),
    ("pmid", "PubMed ID", "text"),
]
SELECT_OPTIONS = {
    "valve": ["Aortic", "Mitral", "Tricuspid"],
    "status": ["published", "ongoing", "terminated"],
    "signal": ["positive", "neutral", "negative", "descriptive", "pending"],
    "category": [],  # populated dynamically from valve
}
def _editor_field_html(key: str, label: str, kind: str) -> str:
    if key == "__section__":
        return f"<h3 class='ed-sec'>{e(label)}</h3>"
    fid = f"f_{key}"
    if kind == "text":
        return (f"<label class='ed-field'><span>{e(label)}</span>"
                f"<input id='{fid}' data-key='{key}' type='text'></label>")
    if kind == "textarea":
        return (f"<label class='ed-field wide'><span>{e(label)}</span>"
                f"<textarea id='{fid}' data-key='{key}' rows='2'></textarea></label>")
    if kind == "list":
        return (f"<label class='ed-field wide'><span>{e(label)}</span>"
                f"<textarea id='{fid}' data-key='{key}' rows='3' "
                f"placeholder='One item per line'></textarea></label>")
    if kind == "bool":
        return (f"<label class='ed-check'><input id='{fid}' data-key='{key}' type='checkbox'>"
                f"<span>{e(label)}</span></label>")
    if kind == "select":
        opts = "".join(f"<option value='{e(o)}'>{e(o)}</option>" for o in SELECT_OPTIONS.get(key, []))
        return (f"<label class='ed-field'><span>{e(label)}</span>"
                f"<select id='{fid}' data-key='{key}'>{opts}</select></label>")
    return ""
def build_editor_page() -> str:
    import json as _json
    fields_html = "".join(_editor_field_html(k, lbl, kind) for k, lbl, kind in EDITOR_FIELDS)
    trials_json = _json.dumps([t.to_dict() for t in TRIALS], ensure_ascii=False)
    cats_by_valve = _json.dumps(VALVE_CATEGORIES, ensure_ascii=False)
    text_keys = [k for k, _, kind in EDITOR_FIELDS if kind == "text"]
    ta_keys = [k for k, _, kind in EDITOR_FIELDS if kind == "textarea"]
    list_keys = [k for k, _, kind in EDITOR_FIELDS if kind == "list"]
    sel_keys = [k for k, _, kind in EDITOR_FIELDS if kind == "select"]
    bool_keys = [k for k, _, kind in EDITOR_FIELDS if kind == "bool"]
    body = f"""
<main class="editor">
  <div class="ed-intro">
    <p class="kicker"><a class="crumb" href="index.html">ValveTrials.org</a> · Editor</p>
    <h1>Trial editor</h1>
    <p class="lede">Add, edit, or delete trials with the form — no code. Changes stay in your browser
      until you <b>export</b>. Then commit the downloaded <span class="mono">trials.json</span> to your
      repository and the site rebuilds automatically (see the README).</p>
    <div class="ed-actions">
      <button id="btnNew" class="ed-btn primary">＋ New trial</button>
      <button id="btnExport" class="ed-btn">⬇ Export trials.json</button>
      <button id="btnCopyPy" class="ed-btn">⧉ Copy this trial as Python</button>
      <span id="edCount" class="ed-count"></span>
      <span id="edDirty" class="ed-dirty" hidden>● unsaved changes (not yet exported)</span>
    </div>
  </div>
  <div class="ed-cols">
    <aside class="ed-side">
      <input id="edSearch" class="ed-search" type="search" placeholder="Filter trials…">
      <div id="edList" class="ed-listbox"></div>
    </aside>
    <section class="ed-form">
      <div class="ed-formhead">
        <h2 id="edFormTitle">New trial</h2>
        <div class="ed-formbtns">
          <button id="btnApply" class="ed-btn primary">Save to list</button>
          <button id="btnDelete" class="ed-btn danger" hidden>Delete</button>
        </div>
      </div>
      <div class="ed-grid">{fields_html}</div>
    </section>
  </div>
  <dialog id="exportDlg" class="ed-dialog">
    <form method="dialog"><button class="ed-x" aria-label="Close">✕</button></form>
    <h3>Export</h3>
    <p>Your trials were downloaded as <span class="mono">trials.json</span>. Commit that file to the
       repo root; the GitHub Action rebuilds and republishes the site. You can also copy the JSON below.</p>
    <textarea id="exportText" rows="12" readonly></textarea>
    <div class="ed-dialog-actions"><button id="btnCopyJson" class="ed-btn">⧉ Copy JSON</button></div>
  </dialog>
</main>
<script>
const TRIALS = {trials_json};
const CATS_BY_VALVE = {cats_by_valve};
const TEXT = {_json.dumps(text_keys)};
const TA = {_json.dumps(ta_keys)};
const LISTF = {_json.dumps(list_keys)};
const SEL = {_json.dumps(sel_keys)};
const BOOLF = {_json.dumps(bool_keys)};
let editIndex = -1;
let dirty = false;
const $ = s => document.querySelector(s);
const listEl = $('#edList');
const searchEl = $('#edSearch');
function markDirty(v){{ dirty = v; $('#edDirty').hidden = !v; }}
function setCount(){{ $('#edCount').textContent = TRIALS.length + ' trials in memory'; }}
function catOptions(valve, selected){{
  const cats = CATS_BY_VALVE[valve] || [];
  const sel = $('#f_category');
  sel.innerHTML = '<option value=""></option>' +
    cats.map(c => `<option value="${{c.replace(/"/g,'&quot;')}}" ${{c===selected?'selected':''}}>${{c}}</option>`).join('');
}}
function renderList(){{
  const q = (searchEl.value||'').toLowerCase();
  const groups = {{}};
  TRIALS.forEach((t,i)=>{{
    const hay = [t.acronym,t.full_name,t.nct,t.category,t.valve].join(' ').toLowerCase();
    if(q && !hay.includes(q)) return;
    const v = t.valve || 'Aortic';
    (groups[v] = groups[v] || []).push([t,i]);
  }});
  let html='';
  ['Aortic','Mitral','Tricuspid'].forEach(v=>{{
    if(!groups[v]) return;
    html += `<div class="ed-group">${{v}} <span>${{groups[v].length}}</span></div>`;
    groups[v].forEach(([t,i])=>{{
      html += `<button class="ed-item ${{i===editIndex?'active':''}}" data-i="${{i}}">
        <b>${{t.acronym||'(no acronym)'}}</b><span>${{t.category||''}}</span></button>`;
    }});
  }});
  listEl.innerHTML = html || '<p class="ed-empty">No matches.</p>';
  listEl.querySelectorAll('.ed-item').forEach(b=>b.addEventListener('click',()=>loadTrial(+b.dataset.i)));
}}
function blank(){{
  const o = {{practice_changing:false, landmark:false, evidence_stars:0, intervention:'', valve:'Aortic'}};
  return o;
}}
function populate(t){{
  TEXT.forEach(k=> {{ const el=$('#f_'+k); if(el) el.value = t[k]||''; }});
  TA.forEach(k=> {{ const el=$('#f_'+k); if(el) el.value = t[k]||''; }});
  LISTF.forEach(k=> {{ const el=$('#f_'+k); if(el) el.value = Array.isArray(t[k])?t[k].join('\\n'):''; }});
  BOOLF.forEach(k=> {{ const el=$('#f_'+k); if(el) el.checked = !!t[k]; }});
  $('#f_valve').value = t.valve||'Aortic';
  $('#f_status').value = t.status||'published';
  $('#f_signal').value = t.signal||'descriptive';
  catOptions(t.valve||'Aortic', t.category||'');
}}
function readForm(){{
  const o = {{}};
  TEXT.forEach(k=> o[k] = $('#f_'+k).value.trim());
  TA.forEach(k=> o[k] = $('#f_'+k).value.trim());
  LISTF.forEach(k=> o[k] = $('#f_'+k).value.split('\\n').map(s=>s.trim()).filter(Boolean));
  BOOLF.forEach(k=> o[k] = $('#f_'+k).checked);
  o.valve = $('#f_valve').value;
  o.status = $('#f_status').value;
  o.signal = $('#f_signal').value;
  o.category = $('#f_category').value;
  o.evidence_stars = 0;
  return o;
}}
function loadTrial(i){{
  if(dirty && !confirm('Discard unsaved changes to the current trial?')) return;
  editIndex = i;
  populate(TRIALS[i]);
  $('#edFormTitle').textContent = 'Editing: ' + (TRIALS[i].acronym||'(trial)');
  $('#btnDelete').hidden = false;
  markDirty(false);
  renderList();
}}
function newTrial(){{
  if(dirty && !confirm('Discard unsaved changes to the current trial?')) return;
  editIndex = -1;
  populate(blank());
  $('#edFormTitle').textContent = 'New trial';
  $('#btnDelete').hidden = true;
  markDirty(false);
  renderList();
}}
function apply(){{
  const o = readForm();
  if(!o.acronym){{ alert('Acronym is required.'); return; }}
  if(editIndex === -1){{ TRIALS.push(o); editIndex = TRIALS.length-1; }}
  else {{ TRIALS[editIndex] = o; }}
  $('#edFormTitle').textContent = 'Editing: ' + o.acronym;
  $('#btnDelete').hidden = false;
  markDirty(false); setCount(); renderList();
}}
function del(){{
  if(editIndex === -1) return;
  if(!confirm('Delete "'+(TRIALS[editIndex].acronym||'this trial')+'" from the list?')) return;
  TRIALS.splice(editIndex,1);
  newTrial(); setCount();
}}
function download(name, text){{
  const blob = new Blob([text], {{type:'application/json'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=name; a.click();
  URL.revokeObjectURL(url);
}}
function exportJson(){{
  const text = JSON.stringify(TRIALS, null, 2);
  download('trials.json', text);
  $('#exportText').value = text;
  $('#exportDlg').showModal();
  markDirty(false);
}}
function pyStr(s){{ return '"' + String(s).replace(/\\\\/g,'\\\\\\\\').replace(/"/g,'\\\\"') + '"'; }}
function toPython(o){{
  const lines = ['Trial('];
  const order = ['acronym','full_name','nct','category','valve','procedure','disease','tags',
    'status','signal','practice_changing','landmark','caveat','quick_summary','takeaway',
    'device','intervention','comparator','population','risk_group','sample_size','enrollment',
    'follow_up','trial_type','inclusion','primary_endpoint','secondary_endpoints','key_results',
    'why_matters','pearls','limitations','guideline_acc','guideline_esc','fda_impact','timeline',
    'authors','journal','year','doi','pmid'];
  order.forEach(k=>{{
    let v = o[k];
    if(v===undefined || v==='' || (Array.isArray(v)&&v.length===0)) return;
    if(Array.isArray(v)) v = '[' + v.map(pyStr).join(', ') + ']';
    else if(typeof v === 'boolean') v = v?'True':'False';
    else v = pyStr(v);
    lines.push('    '+k+'='+v+',');
  }});
  lines.push(')');
  return lines.join('\\n');
}}
$('#btnNew').addEventListener('click', newTrial);
$('#btnApply').addEventListener('click', apply);
$('#btnDelete').addEventListener('click', del);
$('#btnExport').addEventListener('click', exportJson);
$('#btnCopyPy').addEventListener('click', ()=>{{
  navigator.clipboard.writeText(toPython(readForm())).then(()=>alert('Python Trial(...) block copied.'));
}});
$('#btnCopyJson').addEventListener('click', ()=>{{
  navigator.clipboard.writeText($('#exportText').value).then(()=>alert('JSON copied.'));
}});
searchEl.addEventListener('input', renderList);
document.querySelectorAll('.ed-grid [data-key]').forEach(el=>{{
  const ev = (el.type==='checkbox'||el.tagName==='SELECT') ? 'change':'input';
  el.addEventListener(ev, ()=>markDirty(true));
}});
$('#f_valve').addEventListener('change', ()=> catOptions($('#f_valve').value, ''));
setCount(); newTrial();
</script>
"""
    return page_shell("Trial editor — ValveTrials.org", "editor", body)
# ---------------------------------------------------------------------------
CSS = r"""
:root{--ink:#0E262B;--page:#EAEFEE;--card:#FFFFFF;--line:#D2DEDB;--muted:#5B6E6B;
--accent:#C7402F;--r:12px;}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--page);color:var(--ink);
font-family:"Inter",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
.mono{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace}
.site{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:13px 24px;background:var(--ink);color:#fff;flex-wrap:wrap}
.brand{font-family:"Archivo",sans-serif;font-weight:800;font-size:19px;letter-spacing:-.01em;color:#fff;text-decoration:none}
.brand span{color:#E8846F}
.site-nav{display:flex;gap:4px;flex-wrap:wrap}
.site-nav a{color:#c7d3d1;text-decoration:none;font-size:14px;padding:7px 13px;border-radius:8px;transition:background .15s,color .15s}
.site-nav a:hover{background:rgba(255,255,255,.12);color:#fff}
.site-nav a.active{background:#fff;color:var(--ink);font-weight:600}
.mast{padding:40px 24px 20px;max-width:1080px;margin:0 auto;border-bottom:1px solid var(--line)}
.kicker{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
.crumb{color:var(--muted);text-decoration:none}.crumb:hover{color:var(--accent)}
.mast h1{font-family:"Archivo",sans-serif;font-weight:800;font-size:clamp(28px,5vw,46px);line-height:1.02;letter-spacing:-.02em;margin:0 0 12px;max-width:16ch}
.mast .lede{max-width:64ch;color:#33474a;margin:0;font-size:16px}
.mast .meta{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--muted);margin-top:14px}
.legend{display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:16px;font-size:12.5px;color:var(--muted)}
.legend span{display:inline-flex;align-items:center;gap:5px}
.home{max-width:1080px;margin:0 auto;padding:56px 24px 90px}
.home .kicker{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}
.home-h1{font-family:"Archivo",sans-serif;font-weight:800;font-size:clamp(32px,5.5vw,54px);line-height:1.02;letter-spacing:-.025em;margin:0 0 14px;max-width:17ch}
.home-lede{max-width:60ch;color:#33474a;font-size:17px;margin:0 0 42px}
.valve-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.vcard{display:flex;flex-direction:column;gap:14px;padding:28px 26px;background:var(--card);border:1px solid var(--line);border-left:6px solid var(--vhue);border-radius:16px;text-decoration:none;color:var(--ink);transition:transform .16s,box-shadow .16s;min-height:250px}
.vcard:hover{transform:translateY(-4px);box-shadow:0 16px 40px rgba(14,38,43,.12)}
.vcard:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.vglyph{width:66px;height:66px}
.vcard h2{font-family:"Archivo",sans-serif;font-weight:800;font-size:27px;margin:0;letter-spacing:-.01em}
.vcard p{color:var(--muted);font-size:14px;margin:0;line-height:1.5;flex:1}
.vcard .pill{align-self:flex-start;font-size:11px;padding:4px 10px;border-radius:999px;background:#eef1f4;color:#455568;font-family:"IBM Plex Mono",monospace}
.vcard .go{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--vhue);font-weight:600}
.vcard.soon{opacity:.96}
.vcard.soon .go{color:var(--muted)}
.controls{position:sticky;top:0;z-index:20;background:rgba(234,239,238,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:12px 24px}
.controls-inner{max-width:1080px;margin:0 auto;display:flex;flex-direction:column;gap:11px}
.searchbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.searchbar input{flex:1;min-width:220px;padding:11px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);font-size:15px;color:var(--ink)}
.searchbar input:focus{outline:2px solid var(--accent);outline-offset:1px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--card)}
.seg button{border:0;background:transparent;padding:9px 13px;font-size:13px;cursor:pointer;color:var(--muted);font-family:inherit}
.seg button.active{background:var(--ink);color:#fff}
.actions{display:flex;gap:8px}
.actions button{border:1px solid var(--line);background:var(--card);color:#33474a;padding:9px 13px;border-radius:10px;font-size:13px;cursor:pointer;font-family:inherit}
.actions button:hover{border-color:var(--accent);color:var(--accent)}
.fchips{display:flex;flex-wrap:wrap;gap:8px}
.fchip{border:1px solid var(--line);background:var(--card);color:#33474a;padding:7px 12px;border-radius:999px;font-size:13px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:7px}
.fchip .fn{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted)}
.fchip[data-filter="cat"]{border-left:4px solid var(--hue)}
.fchip.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.fchip.active .fn{color:#cdd8d6}
.countline{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted)}
.list{max-width:1080px;margin:22px auto 80px;padding:0 24px}
details.group{margin-bottom:20px}
summary.grouphead{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;margin:0;padding:8px 4px;font-family:"Archivo",sans-serif;font-weight:700;font-size:15px;letter-spacing:.02em;text-transform:uppercase;color:var(--hue);border-bottom:2px solid var(--hue)}
summary.grouphead::-webkit-details-marker{display:none}
summary.grouphead:hover{opacity:.85}
summary.grouphead:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.grouphead .dot{width:9px;height:9px;border-radius:50%;background:var(--hue)}
.gcount{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted);font-weight:400;letter-spacing:0}
.gchev{width:9px;height:9px;border-right:2px solid var(--hue);border-bottom:2px solid var(--hue);transform:rotate(-45deg);transition:transform .18s}
details.group[open] > summary .gchev{transform:rotate(45deg)}
.rows{display:flex;flex-direction:column;gap:8px;margin-top:12px}
details.row{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--hue);border-radius:var(--r);overflow:hidden}
details.row[open]{box-shadow:0 8px 26px rgba(14,38,43,.09)}
summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:20px minmax(190px,1.05fr) 1.5fr auto;gap:14px;align-items:center;padding:14px 18px}
summary::-webkit-details-marker{display:none}
summary:hover{background:#f6f9f8}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.chev{width:9px;height:9px;border-right:2px solid var(--muted);border-bottom:2px solid var(--muted);transform:rotate(-45deg);transition:transform .18s;margin-left:4px}
details.row[open] > summary .chev{transform:rotate(45deg)}
.row-acr{font-family:"Archivo",sans-serif;font-weight:800;font-size:17px;letter-spacing:-.01em;display:block;line-height:1.15}
.row-name{font-size:12px;color:var(--muted);display:block;line-height:1.3;margin-top:1px}
.cav-dot{color:#B03A2E;font-size:12px}
.row-take{font-size:13.5px;color:#243b3e;line-height:1.4}
.row-meta{display:flex;flex-direction:column;align-items:flex-end;gap:5px;text-align:right}
.badge{font-size:10.5px;padding:3px 9px;border-radius:999px;border:1px solid transparent;white-space:nowrap;font-weight:500}
.status-published{background:#e6f4ec;color:#1c6b45;border-color:#c7e6d5}
.status-ongoing{background:#e7f0fa;color:#1f5c92;border-color:#cbe0f3}
.status-terminated{background:#f4e7e6;color:#9c3a2f;border-color:#eccdc9}
.dates{display:flex;flex-direction:column;align-items:flex-end;gap:1px;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--muted);line-height:1.35}
.dates .d-pub{color:#33474a}
.body-inner{padding:2px 18px 20px;border-top:1px solid var(--line)}
.paperbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;margin:14px 0 6px;padding:12px 14px;background:#f5f8f7;border:1px solid var(--line);border-radius:10px}
.paperbar.none{color:var(--muted);font-style:italic}
ul.papers{list-style:none;margin:6px 0 0;padding:0}
ul.papers li{padding:8px 0;border-top:1px solid #eef2f1;font-size:13.5px;line-height:1.5}
ul.papers li:first-child{border-top:0}
ul.papers .pc-cite{color:#33474a}
ul.papers .pc-links{white-space:nowrap}
ul.papers .plink{font-size:11.5px;padding:2px 8px;margin-left:4px}
/* follow-up "has follow-ups" badge on each row */
.badge.fu{background:#eef1f4;color:#3f5164;border-color:#d7dee7;font-family:"IBM Plex Mono",monospace;font-size:10px}
/* collapsible follow-ups: click each to reveal its links */
.papers{margin:6px 0 0}
.pc-hint{font-size:12px;color:var(--muted);margin:0 0 8px}
details.pc{border-top:1px solid #eef2f1}
details.pc:first-of-type{border-top:0}
details.pc > summary{list-style:none;cursor:pointer;display:flex;align-items:baseline;gap:8px;padding:9px 0;grid-template-columns:none}
details.pc > summary::-webkit-details-marker{display:none}
details.pc > summary:hover{color:var(--accent)}
.pc-chev{flex:0 0 auto;width:7px;height:7px;border-right:2px solid var(--muted);border-bottom:2px solid var(--muted);transform:rotate(-45deg);transition:transform .16s;position:relative;top:-1px}
details.pc[open] > summary .pc-chev{transform:rotate(45deg)}
.pc-label{font-family:"Archivo",sans-serif;font-size:13px;white-space:nowrap}
details.pc .pc-cite{color:#33474a;font-size:13px;line-height:1.4}
.pc-body{padding:2px 0 10px 15px;display:flex;flex-wrap:wrap;gap:8px}
.pc-nolink{font-size:12px;color:var(--muted);font-style:italic}
h3 .pc-count{display:inline-block;min-width:18px;text-align:center;font-size:11px;font-family:"IBM Plex Mono",monospace;color:#fff;background:var(--hue,#2C6E8F);border-radius:9px;padding:1px 6px;margin-left:6px;vertical-align:middle}
.plinks{display:flex;flex-wrap:wrap;gap:8px}
.plink{font-family:"IBM Plex Mono",monospace;font-size:12px;text-decoration:none;padding:6px 11px;border-radius:8px;border:1px solid var(--line);color:var(--accent);background:#fff}
.plink.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.plink.search{color:#33474a}
.plink:hover{filter:brightness(.96)}
.paper-cite{font-size:12.5px;color:#33474a;margin-left:auto}.paper-cite em{font-style:italic}
.d-caveat{margin:8px 0;font-size:13px;color:#9c3a2f;background:#faeeec;border:1px dashed #e6c3bd;border-radius:8px;padding:9px 12px}
.d-summary{color:#33474a;margin:8px 0 4px;font-size:14.5px}
.d-grid{display:grid;grid-template-columns:1fr 290px;gap:26px;padding-top:8px}
.d-main section{margin-bottom:18px}
.d-main h3{font-family:"Archivo",sans-serif;font-size:12.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--hue);margin:0 0 7px;padding-bottom:5px;border-bottom:1px solid var(--line)}
.d-main p{margin:0}
.overview{width:100%;border-collapse:collapse;font-size:13.5px}
.overview th{text-align:left;width:38%;color:var(--muted);font-weight:500;padding:6px 10px 6px 0;vertical-align:top;border-bottom:1px solid #edf2f1}
.overview td{padding:6px 0;border-bottom:1px solid #edf2f1;vertical-align:top}
.bul{margin:0;padding-left:18px}.bul li{margin:3px 0}
.results{list-style:none;margin:0;padding:0}
.results li{position:relative;padding-left:22px;margin:6px 0}
.results li::before{content:"✔";position:absolute;left:0;color:var(--hue);font-size:12px;top:2px}
.empty{color:var(--muted);font-style:italic;margin:0}
.d-side{border-left:1px solid var(--line);padding-left:22px}
.qf{margin-bottom:18px}
.qf h4{font-family:"Archivo",sans-serif;font-size:11.5px;text-transform:uppercase;letter-spacing:.08em;margin:0 0 8px}
.qf dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:5px 12px;font-size:13px}
.qf dt{color:var(--muted)}.qf dd{margin:0;text-align:right}
.qf .lab{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:8px 0 2px}
.qf p{margin:0 0 2px;font-size:13px}
.qf .bul{font-size:13px}
.noresults{text-align:center;color:var(--muted);padding:50px 20px;font-size:16px;display:none}
.soon-box{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--hue);border-radius:16px;padding:28px 26px;max-width:640px}
.soon-box h2{font-family:"Archivo",sans-serif;font-weight:800;font-size:24px;margin:0 0 8px}
.soon-box p{color:#33474a;margin:0 0 16px}
.back{font-family:"IBM Plex Mono",monospace;font-size:13px;text-decoration:none}
.soon-head{font-family:"Archivo",sans-serif;font-size:12.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:34px 0 12px}
.soon-sections{display:flex;flex-direction:column;gap:8px;max-width:640px}
.soon-sec{display:flex;align-items:center;gap:10px;background:var(--card);border:1px dashed var(--line);border-radius:10px;padding:13px 16px;font-family:"Archivo",sans-serif;font-weight:700;font-size:14px;text-transform:uppercase;letter-spacing:.02em;color:#7c8b89}
.soon-sec .dot{width:9px;height:9px;border-radius:50%;background:var(--hue);opacity:.5}
.soon-tag{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:400;letter-spacing:0;color:var(--muted);text-transform:none}
footer.pagefoot{max-width:1080px;margin:0 auto;padding:22px 24px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
/* editor */
.site-nav a.editlink{border:1px solid rgba(255,255,255,.25)}
.editor{max-width:1180px;margin:0 auto;padding:30px 24px 80px}
.editor .kicker{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
.editor h1{font-family:"Archivo",sans-serif;font-weight:800;font-size:clamp(26px,4vw,40px);margin:0 0 10px}
.editor .lede{max-width:70ch;color:#33474a;margin:0 0 16px}
.ed-actions{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:8px}
.ed-btn{border:1px solid var(--line);background:var(--card);color:#243b3e;padding:9px 14px;border-radius:9px;font-size:13px;cursor:pointer;font-family:inherit}
.ed-btn:hover{border-color:var(--accent);color:var(--accent)}
.ed-btn.primary{background:var(--ink);color:#fff;border-color:var(--ink)}
.ed-btn.primary:hover{filter:brightness(1.1);color:#fff}
.ed-btn.danger{color:#9c3a2f;border-color:#e6c3bd}
.ed-count{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--muted)}
.ed-dirty{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--accent)}
.ed-cols{display:grid;grid-template-columns:290px 1fr;gap:22px;margin-top:14px}
.ed-side{position:sticky;top:14px;align-self:start}
.ed-search{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:9px;background:var(--card);font-size:14px;margin-bottom:10px}
.ed-listbox{max-height:70vh;overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--card);padding:6px}
.ed-group{font-family:"Archivo",sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:10px 8px 4px;display:flex;justify-content:space-between}
.ed-item{display:block;width:100%;text-align:left;border:0;background:transparent;border-radius:8px;padding:8px 10px;cursor:pointer;font-family:inherit}
.ed-item:hover{background:#f0f4f3}
.ed-item.active{background:var(--ink);color:#fff}
.ed-item b{display:block;font-family:"Archivo",sans-serif;font-size:14px}
.ed-item span{font-size:11px;color:var(--muted)}
.ed-item.active span{color:#cdd8d6}
.ed-empty{color:var(--muted);padding:16px;font-style:italic}
.ed-form{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.ed-formhead{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--line)}
.ed-formhead h2{font-family:"Archivo",sans-serif;font-size:18px;margin:0}
.ed-formbtns{display:flex;gap:8px}
.ed-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px}
.ed-sec{grid-column:1/-1;font-family:"Archivo",sans-serif;font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:var(--hue,#2C6E8F);margin:10px 0 2px;padding-top:8px;border-top:1px solid #eef2f1}
.ed-field{display:flex;flex-direction:column;gap:4px;font-size:12.5px;color:var(--muted)}
.ed-field.wide{grid-column:1/-1}
.ed-field input,.ed-field select,.ed-field textarea{border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:14px;font-family:inherit;color:var(--ink);background:#fff}
.ed-field textarea{resize:vertical;line-height:1.4}
.ed-field input:focus,.ed-field select:focus,.ed-field textarea:focus{outline:2px solid var(--accent);outline-offset:1px}
.ed-check{grid-column:auto;display:flex;align-items:center;gap:8px;font-size:14px;color:var(--ink);padding-top:18px}
.ed-dialog{width:min(760px,94vw);border:0;border-radius:14px;padding:0 24px 24px;box-shadow:0 30px 80px rgba(10,30,34,.35)}
.ed-dialog::backdrop{background:rgba(11,28,31,.5)}
.ed-dialog h3{font-family:"Archivo",sans-serif;margin:18px 0 8px}
.ed-dialog textarea{width:100%;border:1px solid var(--line);border-radius:10px;padding:12px;font-family:"IBM Plex Mono",monospace;font-size:12px}
.ed-dialog-actions{margin-top:10px}
.ed-x{position:absolute;right:14px;top:14px;border:1px solid var(--line);background:#fff;border-radius:50%;width:32px;height:32px;cursor:pointer}
@media (max-width:820px){.ed-cols{grid-template-columns:1fr}.ed-side{position:static}.ed-grid{grid-template-columns:1fr}}
@media (max-width:820px){
  .valve-cards{grid-template-columns:1fr}
  summary{grid-template-columns:18px 1fr;gap:8px}
  .row-take,.row-meta{grid-column:2}
  .row-meta{align-items:flex-start;text-align:left}
  .dates{align-items:flex-start}
  .d-grid{grid-template-columns:1fr}
  .d-side{border-left:0;border-top:1px solid var(--line);padding-left:0;padding-top:16px}
  .qf dd{text-align:left}
  .paper-cite{margin-left:0;width:100%}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""
LIST_JS = r"""
const $ = s => document.querySelector(s);
const rows = Array.from(document.querySelectorAll('details.row'));
const groups = Array.from(document.querySelectorAll('details.group'));
const search = $('#search');
const count = $('#count');
let state = {text:'',cat:'all',status:'all',pc:false};
function apply(){
  let shown=0;
  rows.forEach(r=>{
    const okText=!state.text||r.dataset.search.includes(state.text);
    const okCat=state.cat==='all'||r.dataset.cat===state.cat;
    const okStatus=state.status==='all'||r.dataset.status===state.status;
    const okPc=!state.pc||r.dataset.pc==='1';
    const vis=okText&&okCat&&okStatus&&okPc;
    r.style.display=vis?'':'none';r.dataset.vis=vis?'1':'0';if(vis)shown++;
  });
  const filterActive=!!(state.text||state.cat!=='all'||state.status!=='all'||state.pc);
  groups.forEach(g=>{
    const visRows=g.querySelectorAll('details.row[data-vis="1"]').length;
    const catOk=state.cat==='all'||g.dataset.cat===state.cat;
    g.style.display=(visRows>0&&catOk)?'':'none';
    if(filterActive&&visRows>0&&catOk)g.open=true;
  });
  count.textContent=shown+' / '+rows.length+' trials shown';
  $('#noresults').style.display=shown?'none':'block';
}
search.addEventListener('input',e=>{state.text=e.target.value.trim().toLowerCase();apply();});
document.querySelectorAll('.fchip').forEach(c=>c.addEventListener('click',()=>{
  document.querySelectorAll('.fchip').forEach(x=>x.classList.remove('active'));
  c.classList.add('active');state.cat=c.dataset.filter==='all'?'all':c.dataset.value;apply();
}));
document.querySelectorAll('.seg[data-group]').forEach(seg=>{
  const group=seg.dataset.group;
  seg.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{
    seg.querySelectorAll('button').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    if(group==='pc')state.pc=b.dataset.value==='1';else state[group]=b.dataset.value;apply();
  }));
});
$('#expandAll').addEventListener('click',()=>{groups.forEach(g=>g.open=true);rows.forEach(r=>{if(r.style.display!=='none')r.open=true;});});
$('#collapseAll').addEventListener('click',()=>{rows.forEach(r=>r.open=false);groups.forEach(g=>g.open=false);});
apply();
"""
def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(outdir, exist_ok=True)
    pages = {"index.html": build_home()}
    for k, *_ in VALVES:
        pages[f"{k}.html"] = (build_valve_list_page(k) if trials_for(k)
                              else build_coming_soon_page(k))
    for name, content in pages.items():
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            f.write(content)
    counts = {k: len(trials_for(k)) for k, *_ in VALVES}
    print("Wrote:", ", ".join(pages))
    print("Trial counts:", counts)
if __name__ == "__main__":
    main()
