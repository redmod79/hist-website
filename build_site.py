#!/usr/bin/env python3
"""
build_site.py — Build the Historicist Proof Series website.

Scans D:/bible/bible-studies/hist-* for all 19 studies,
copies files into docs/studies/, generates mkdocs.yml and index.md,
and copies shared assets from etc-website.
"""

import json
import os
import re
import shutil
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
STUDIES_SRC = Path("D:/bible/bible-studies")
ETC_WEBSITE = Path("D:/bible/etc-website")
DOCS = PROJECT_ROOT / "docs"
DOCS_STUDIES = DOCS / "studies"

# ── Study metadata ─────────────────────────────────────────────────
SHORT_TITLES = {
    "hist-01": "How to Read Apocalyptic Prophecy",
    "hist-02": "Daniel 7: Beasts, Little Horn, Judgment",
    "hist-03": "The 70 Weeks: Jesus Fulfills the Timeline",
    "hist-04": "Daniel 8: The Little Horn Identified",
    "hist-05": "Daniel 8-9 Connected: The 2300 Days",
    "hist-06": "The Sanctuary Vindicated (1844)",
    "hist-07": "How the NT Treats Daniel 7-12",
    "hist-08": "'Shortly Come to Pass'",
    "hist-09": "Why Not Preterism, Futurism, or Idealism?",
    "hist-10": "The Seven Churches",
    "hist-11": "Rev 12: Woman, Dragon, 1260 Years",
    "hist-12": "Rev 13-14: Beast, Three Angels, Harvest",
    "hist-13": "The Olivet Discourse Spans History",
    "hist-14": "The Seven Seals Span History",
    "hist-15": "Trumpets: Warnings Before Judgment",
    "hist-16": "Bowls: After Judgment",
    "hist-17": "One Second Coming, Many Angles",
    "hist-18": "Recapitulation: Three Views, One Timeline",
    "hist-19": "Comprehensive Synthesis",
}

FULL_TITLES = {
    "hist-01": "How should we read apocalyptic prophecy? Hermeneutical principles for Daniel and Revelation.",
    "hist-02": "What are the four beasts, the little horn, and the judgment scene of Daniel 7?",
    "hist-03": "How does the 70-weeks prophecy empirically validate the day-year principle?",
    "hist-04": "What textual constraints identify Daniel 8's little horn as Rome, not Antiochus?",
    "hist-05": "How are Daniel 8 and 9 connected, and where do the 2300 days terminate?",
    "hist-06": "What does Daniel 8:14 actually say about the sanctuary, and what happened in 1844?",
    "hist-07": "How do Jesus, Paul, and John treat Daniel 7-12 as a unified prophetic system?",
    "hist-08": "What is the semantic range of en tachei, and does it require first-century fulfillment?",
    "hist-09": "Why do preterism, futurism, and idealism each fail on specific textual data?",
    "hist-10": "Do the seven churches operate on literal, prophetic, and universal levels simultaneously?",
    "hist-11": "How does Revelation 12 span from Christ's first coming to the post-1260 remnant?",
    "hist-12": "How does Revelation's composite beast absorb Daniel's four kingdoms, and what do the three angels proclaim?",
    "hist-13": "Does Jesus's Olivet Discourse span multiple centuries or only address the first century?",
    "hist-14": "Do the seven seals span from the apostolic era to the second coming?",
    "hist-15": "Are the trumpets probationary warnings sounded during Christ's intercessory ministry?",
    "hist-16": "Do the bowls execute final wrath after the close of probation?",
    "hist-17": "Do multiple Revelation passages describe the same second coming from different angles?",
    "hist-18": "Are Revelation's sequences parallel recapitulating views of the same history?",
    "hist-19": "The Historicist Proof: Comprehensive Synthesis of Studies 1-18",
}

# Cluster groupings
CLUSTERS = [
    {
        "name": "Cluster A -- Daniel Foundation",
        "desc": "Establishing the hermeneutical framework, the four-kingdom succession, and the day-year principle through Daniel's prophecies.",
        "studies": ["hist-01", "hist-02", "hist-03", "hist-04", "hist-05", "hist-06", "hist-07"],
    },
    {
        "name": "Cluster B -- Scope and Framework",
        "desc": "Resolving the scope question: does Revelation require first-century fulfillment, and why do alternative frameworks fail?",
        "studies": ["hist-08", "hist-09"],
    },
    {
        "name": "Cluster C -- Revelation Sequences",
        "desc": "Demonstrating that all four major Revelation sequences span history with identical endpoints.",
        "studies": ["hist-10", "hist-11", "hist-12", "hist-13", "hist-14", "hist-15", "hist-16"],
    },
    {
        "name": "Cluster D -- Integration",
        "desc": "Proving that these are multiple perspectives on one timeline converging on a single second coming.",
        "studies": ["hist-17", "hist-18"],
    },
    {
        "name": "Synthesis",
        "desc": "Complete synthesis of all 18 studies with deduplicated evidence tally and final assessment.",
        "studies": ["hist-19"],
    },
]

# Standard study files (in display order for nav)
STUDY_FILES = [
    ("CONCLUSION.md", None),           # Landing page (no label = index page)
    ("03-analysis.md", "Analysis"),
    ("02-verses.md", "Verses"),
    ("04-word-studies.md", "Word Studies"),
    ("01-topics.md", "Topics"),
    ("PROMPT.md", "Research Scope"),
]

# Raw data file display names
RAW_DATA_NAMES = {
    "concept-context": "Concept Context",
    "existing-studies": "Existing Studies",
    "greek-parsing": "Greek Parsing",
    "hebrew-parsing": "Hebrew Parsing",
    "naves-topics": "Nave's Topics",
    "parallels": "Cross-Testament Parallels",
    "strongs-lookups": "Strong's Lookups",
    "strongs": "Strong's Lookups",
    "web-research": "Web Research",
    "grammar-references": "Grammar References",
    "evidence-tally": "Evidence Tally",
    "study-db-queries": "Study DB Queries",
    "historicist-evidence": "Historicist Evidence",
    "anti-historicist-evidence": "Anti-Historicist Evidence",
    "ib-resolutions": "I-B Resolutions",
    "per-study-breakdown": "Per-Study Breakdown",
}


def get_raw_data_name(filename: str) -> str:
    """Get a display name for a raw-data file."""
    stem = Path(filename).stem
    if stem in RAW_DATA_NAMES:
        return RAW_DATA_NAMES[stem]
    return stem.replace("-", " ").title()


def find_study_folders() -> list[tuple[str, Path]]:
    """Find all hist-NN-* folders in the studies source directory."""
    folders = []
    for d in sorted(STUDIES_SRC.iterdir()):
        if d.is_dir() and re.match(r"hist-\d{2}-", d.name):
            slug = d.name
            num = slug.split("-")[1]
            key = f"hist-{num}"
            folders.append((key, d))
    return folders


def copy_study(key: str, src: Path, preserved_simples: dict):
    """Copy a study folder into docs/studies/."""
    dest = DOCS_STUDIES / src.name
    dest.mkdir(parents=True, exist_ok=True)

    # Copy standard files
    for fname, _ in STUDY_FILES:
        src_file = src / fname
        if src_file.exists():
            shutil.copy2(src_file, dest / fname)

    # Restore preserved conclusion-simple.md, or copy from source
    simple_path = dest / "conclusion-simple.md"
    if src.name in preserved_simples:
        simple_path.write_text(preserved_simples[src.name], encoding="utf-8")
    else:
        simple_src = src / "conclusion-simple.md"
        if simple_src.exists():
            shutil.copy2(simple_src, dest / "conclusion-simple.md")

    # Copy METADATA.yaml if present
    meta = src / "METADATA.yaml"
    if meta.exists():
        shutil.copy2(meta, dest / "METADATA.yaml")

    # Copy raw-data/ (both .md and .txt files)
    raw_src = src / "raw-data"
    if raw_src.exists() and raw_src.is_dir():
        raw_dest = dest / "raw-data"
        raw_dest.mkdir(parents=True, exist_ok=True)
        for f in raw_src.iterdir():
            if f.is_file():
                # Convert .txt to .md for MkDocs rendering
                if f.suffix == ".txt":
                    dest_file = raw_dest / (f.stem + ".md")
                    content = f.read_text(encoding="utf-8", errors="replace")
                    # Wrap in code block if it looks like raw data
                    dest_file.write_text(f"# {get_raw_data_name(f.name)}\n\n```\n{content}\n```\n", encoding="utf-8")
                else:
                    shutil.copy2(f, raw_dest / f.name)

    return dest


def build_nav_entry(key: str, slug: str) -> dict:
    """Build a nav entry for one study."""
    num = key.split("-")[1]
    short_title = SHORT_TITLES.get(key, slug)
    nav_title = f"{num} -- {short_title}"

    dest = DOCS_STUDIES / slug
    items = []

    # Landing page: conclusion-simple.md if it exists, else CONCLUSION.md
    simple = dest / "conclusion-simple.md"
    conclusion = dest / "CONCLUSION.md"
    if simple.exists():
        items.append(f"studies/{slug}/conclusion-simple.md")
        if conclusion.exists():
            items.append({"Conclusion": f"studies/{slug}/CONCLUSION.md"})
    elif conclusion.exists():
        items.append(f"studies/{slug}/CONCLUSION.md")

    # Other standard files
    for fname, label in STUDY_FILES:
        if label is None:
            continue
        fpath = dest / fname
        if fpath.exists():
            items.append({label: f"studies/{slug}/{fname}"})

    # Raw data files
    raw_dir = dest / "raw-data"
    if raw_dir.exists() and raw_dir.is_dir():
        raw_items = []
        for f in sorted(raw_dir.iterdir()):
            if f.is_file() and f.suffix == ".md":
                display = get_raw_data_name(f.name)
                raw_items.append({display: f"studies/{slug}/raw-data/{f.name}"})
        if raw_items:
            items.append({"Raw Data": raw_items})

    return {nav_title: items}


def generate_mkdocs_yml(study_folders: list[tuple[str, Path]]):
    """Generate mkdocs.yml."""
    slug_map = {key: src.name for key, src in study_folders}

    lines = []
    lines.append('site_name: "The Historicist Proof"')
    lines.append("site_description: A 19-study biblical investigation examining whether Daniel and Revelation describe a continuous span of history from the prophet's time to the second coming. 496 evidence items classified.")
    lines.append("")
    lines.append("theme:")
    lines.append("  name: material")
    lines.append("  palette:")
    lines.append("    - scheme: default")
    lines.append("      primary: deep purple")
    lines.append("      accent: amber")
    lines.append("      toggle:")
    lines.append("        icon: material/brightness-7")
    lines.append("        name: Switch to dark mode")
    lines.append("    - scheme: slate")
    lines.append("      primary: deep purple")
    lines.append("      accent: amber")
    lines.append("      toggle:")
    lines.append("        icon: material/brightness-4")
    lines.append("        name: Switch to light mode")
    lines.append("  features:")
    lines.append("    - navigation.instant")
    lines.append("    - navigation.tracking")
    lines.append("    - navigation.tabs")
    lines.append("    - navigation.sections")
    lines.append("    - navigation.top")
    lines.append("    - navigation.indexes")
    lines.append("    - search.suggest")
    lines.append("    - search.highlight")
    lines.append("    - content.tabs.link")
    lines.append("    - toc.follow")
    lines.append("  font:")
    lines.append("    text: Roboto")
    lines.append("    code: Roboto Mono")
    lines.append("")
    lines.append("plugins:")
    lines.append("  - search")
    lines.append("")
    lines.append("markdown_extensions:")
    lines.append("  - abbr")
    lines.append("  - admonition")
    lines.append("  - attr_list")
    lines.append("  - def_list")
    lines.append("  - footnotes")
    lines.append("  - md_in_html")
    lines.append("  - tables")
    lines.append("  - toc:")
    lines.append("      permalink: true")
    lines.append("  - pymdownx.details")
    lines.append("  - pymdownx.superfences")
    lines.append("  - pymdownx.highlight:")
    lines.append("      anchor_linenums: true")
    lines.append("  - pymdownx.inlinehilite")
    lines.append("  - pymdownx.tabbed:")
    lines.append("      alternate_style: true")
    lines.append("  - pymdownx.tasklist:")
    lines.append("      custom_checkbox: true")
    lines.append("")
    lines.append("extra:")
    lines.append("  social:")
    lines.append("    - icon: fontawesome/solid/book-bible")
    lines.append("      link: /")
    lines.append("")
    lines.append("extra_javascript:")
    lines.append("  - javascripts/verse-popup.js")
    lines.append("  - javascripts/study-breadcrumbs.js")
    lines.append("  - javascripts/external-links.js")
    lines.append("")
    lines.append("extra_css:")
    lines.append("  - stylesheets/extra.css")
    lines.append("")
    lines.append("nav:")
    lines.append("  - Home: index.md")
    lines.append("  - Studies:")
    lines.append("")

    for cluster in CLUSTERS:
        lines.append(f"    # ── {cluster['name']} ──")
        lines.append(f'    - "{cluster["name"]}":')
        lines.append("")
        for key in cluster["studies"]:
            slug = slug_map.get(key)
            if not slug:
                continue
            nav_entry = build_nav_entry(key, slug)
            for title, items in nav_entry.items():
                lines.append(f'      - "{title}":')
                for item in items:
                    if isinstance(item, str):
                        lines.append(f"        - {item}")
                    elif isinstance(item, dict):
                        for label, val in item.items():
                            if isinstance(val, list):
                                lines.append(f"        - {label}:")
                                for sub in val:
                                    if isinstance(sub, dict):
                                        for slabel, spath in sub.items():
                                            lines.append(f'          - "{slabel}": {spath}')
                                    else:
                                        lines.append(f"          - {sub}")
                            else:
                                lines.append(f"        - {label}: {val}")
        lines.append("")

    lines.append("  - Methodology: methodology.md")
    lines.append('  - "Tools & Process": tools.md')

    yml_path = PROJECT_ROOT / "mkdocs.yml"
    yml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Generated {yml_path}")


def generate_index_md():
    """Generate docs/index.md."""
    content = []

    content.append("# The Historicist Proof: Does Bible Prophecy Span History?")
    content.append("")
    content.append("*A 19-study biblical investigation examining whether Daniel and Revelation describe a continuous span of history from the prophet's time to the second coming of Christ.*")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## The Question")
    content.append("")
    content.append("Four major schools of prophetic interpretation compete for how to read Daniel and Revelation:")
    content.append("")
    content.append("- **Historicism:** The prophecies span continuous history from the prophet's time to the second coming")
    content.append("- **Preterism:** The prophecies were fulfilled primarily in the first century (by AD 70)")
    content.append("- **Futurism:** The prophecies are primarily about a future tribulation period")
    content.append("- **Idealism:** The prophecies portray timeless spiritual truths without specific historical referents")
    content.append("")
    content.append("Rather than assuming any position, this series investigates the biblical evidence from the ground up across 19 studies. The question is **scope**: does the text itself require an extended historical span, or can it be confined to a single era?")
    content.append("")
    content.append("## The Approach")
    content.append("")
    content.append("Each study is a genuine investigation. The agents gathered ALL relevant evidence, presented what each side claims, and let the biblical text speak for itself. No study presupposed its conclusion. Evidence was classified into hierarchical tiers:")
    content.append("")
    content.append("- **Explicit (E):** What the text directly says -- a quote or close paraphrase")
    content.append("- **Necessary Implication (N):** What unavoidably follows from explicit statements")
    content.append("- **Inference** (four types):")
    content.append("    - **I-A (Evidence-Extending):** Systematizes E/N items using only the text's own vocabulary")
    content.append("    - **I-B (Competing-Evidence):** Both sides cite E/N support; resolved by Scripture-interprets-Scripture")
    content.append("    - **I-C (Compatible External):** External reasoning that does not contradict E/N")
    content.append("    - **I-D (Counter-Evidence External):** External concepts that require overriding E/N statements")
    content.append("")
    content.append("**Hierarchy:** E > N > I-A > I-B (resolved by SIS) > I-C > I-D")
    content.append("")
    content.append("[**Read the Methodology**](methodology.md){ .md-button }")
    synth_simple = DOCS_STUDIES / "hist-19-comprehensive-synthesis" / "conclusion-simple.md"
    if synth_simple.exists():
        content.append("[**Skip to the Final Synthesis**](studies/hist-19-comprehensive-synthesis/conclusion-simple.md){ .md-button .md-button--primary }")
    else:
        content.append("[**Skip to the Final Synthesis**](studies/hist-19-comprehensive-synthesis/CONCLUSION.md){ .md-button .md-button--primary }")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## The 19 Studies")
    content.append("")

    for cluster in CLUSTERS:
        content.append(f"### {cluster['name']}")
        content.append("")
        content.append(cluster["desc"])
        content.append("")
        content.append("| # | Study | Question |")
        content.append("|---|-------|----------|")
        for key in cluster["studies"]:
            num = key.split("-")[1]
            short = SHORT_TITLES.get(key, key)
            full = FULL_TITLES.get(key, short)
            slug = None
            for d in sorted(STUDIES_SRC.iterdir()):
                if d.is_dir() and d.name.startswith(f"{key}-"):
                    slug = d.name
                    break
            if slug:
                simple_path = DOCS_STUDIES / slug / "conclusion-simple.md"
                if simple_path.exists():
                    link = f"studies/{slug}/conclusion-simple.md"
                else:
                    link = f"studies/{slug}/CONCLUSION.md"
                content.append(f"| {num} | [{short}]({link}) | {full} |")
            else:
                content.append(f"| {num} | {short} | {full} |")
        content.append("")

    content.append("---")
    content.append("")
    content.append("## What Each Study Contains")
    content.append("")
    content.append("Every study includes multiple layers of research, all accessible through the navigation:")
    content.append("")
    content.append("| File | Contents |")
    content.append("|------|----------|")
    content.append("| **Simple Conclusion** | A plain-language summary of the study's findings -- no technical jargon or evidence tables |")
    content.append("| **Conclusion** | The final evidence classification with Explicit/Necessary Implication/Inference tables, I-B resolutions, tally, and assessment |")
    content.append("| **Analysis** | Verse-by-verse analysis, identified patterns, connections between passages, both-sides arguments |")
    content.append("| **Verses** | Full KJV text for every passage examined, organized thematically |")
    content.append("| **Word Studies** | Hebrew and Greek word studies with Strong's numbers, semantic ranges, and parsing |")
    content.append("| **Topics** | Nave's Topical Bible entries and key research findings |")
    content.append("| **Research Scope** | The original research question and scope that guided the investigation |")
    content.append("| **Raw Data** | Nave's topic output, Strong's lookups, Greek/Hebrew parsing, cross-testament parallels |")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## Evidence Summary (from Study 19)")
    content.append("")
    content.append("Study 19 synthesized the evidence from Studies 1-18 on the central question of whether Daniel and Revelation describe continuous history. The synthesis classified **496 unique evidence items** across those studies.")
    content.append("")
    content.append("### Positional Distribution")
    content.append("")
    content.append("| Tier | Historicist | Anti-Historicist | Neutral/Shared | Total |")
    content.append("|------|-----------|-----------|----------------|-------|")
    content.append("| E (Explicit) | 33 | 0 | 257 | 290 |")
    content.append("| N (Necessary Implication) | 9 | 0 | 86 | 95 |")
    content.append("| I-A (Evidence-Extending) | 56 | 0 | 3 | 59 |")
    content.append("| I-B (Competing-Evidence) | 1 | 22 | 1 | 24 |")
    content.append("| I-C (Compatible External) | 1 | 6 | 1 | 8 |")
    content.append("| I-D (Counter-Evidence External) | 0 | 20 | 0 | 20 |")
    content.append("| **Total** | **100** | **48** | **348** | **496** |")
    content.append("")
    content.append("### The Critical Asymmetry")
    content.append("")
    content.append("Not a single explicit statement (E-tier) or necessary implication (N-tier) in the entire 496-item evidence base supports the Anti-Historicist position. All 42 E+N positional items support Historicism. The Anti-Historicist position's 48 items exist entirely at the inference level (I-B, I-C, and I-D).")
    content.append("")
    content.append("- **Historicist position:** 33% E, 9% N, 56% I-A, 1% I-B (resolved FOR), 1% I-C, 0% I-D")
    content.append("- **Anti-Historicist position:** 0% E, 0% N, 0% I-A, 45.8% I-B (all resolved AGAINST), 12.5% I-C, 41.7% I-D")
    content.append("")
    content.append("The Historicist position never requires overriding explicit text (zero I-D items). The Anti-Historicist position requires overriding explicit statements in 20 documented cases.")
    content.append("")
    synth_simple2 = DOCS_STUDIES / "hist-19-comprehensive-synthesis" / "conclusion-simple.md"
    if synth_simple2.exists():
        content.append("[**Read the Full Synthesis**](studies/hist-19-comprehensive-synthesis/conclusion-simple.md){ .md-button .md-button--primary }")
    else:
        content.append("[**Read the Full Synthesis**](studies/hist-19-comprehensive-synthesis/CONCLUSION.md){ .md-button .md-button--primary }")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## Source Restrictions")
    content.append("")
    content.append("This series uses **no Ellen White, no Adventist pioneer sources** as authoritative evidence. Permitted sources are:")
    content.append("")
    content.append("- Scripture (KJV text with Hebrew/Greek analysis)")
    content.append("- Secular and church historians (for verifying prophetic claims against historical events)")
    content.append("- Scholarly commentators from all traditions")
    content.append("- Hebrew and Greek lexicons, grammars, and concordances")
    content.append("")
    content.append("The question is always: **What does the Bible say?**")
    content.append("")
    content.append("---")
    content.append("")
    # Related Studies — read from shared hub-website/related-studies.json
    links_file = Path("D:/bible/hub-website/related-studies.json")
    if links_file.exists():
        links = json.loads(links_file.read_text(encoding="utf-8"))
        content.append("## Related Studies")
        content.append("")
        content.append("These companion sites use the same tool-driven research methodology:")
        content.append("")
        content.append("| Site | Description |")
        content.append("|------|-------------|")
        for entry in links:
            if entry["id"] == "hist":
                continue
            content.append(f"| [**{entry['name']}**]({entry['url']}) | {entry['description']} |")

    index_path = DOCS / "index.md"
    index_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    print(f"  Generated {index_path}")


def generate_tools_md():
    """Generate docs/tools.md."""
    content = """# Research Tools & Process

*This page describes the automated research system and investigative methodology that produced the 19 studies in this series.*

---

## Investigative Stance

Each study is produced by an agent that functions as an **investigator, not an advocate.** This distinction governs every step of the process:

- **Gather evidence from all sides.** If a passage is cited by historicists, examine it honestly. If a passage is cited by preterists, futurists, or idealists, examine it honestly.
- **Do not assume a conclusion before examining the evidence.** The conclusion emerges FROM the evidence, not the reverse.
- **State what the text says, not opinions about it.** The agent does not use editorial characterizations like "genuine tension," "strongest argument," or "non-intuitive reading." It states what each passage says and what each interpretive position infers from it.
- **Never use language like "irrefutable," "obviously," or "clearly proves."** Use "the text states," "this is consistent with."

---

## How the Studies Were Produced

Each study was generated by a multi-agent pipeline, a Claude Code skill that answers Bible questions through tool-driven research. The pipeline ensures that:

- **Scope comes from tools, not training knowledge.** The AI does not decide which verses are relevant based on what it was trained on. Instead, tools search topical dictionaries, concordances, and semantic indexes to discover what Scripture says about the topic.
- **Research and analysis are separated.** The agent that gathers data is not the same agent that draws conclusions. This prevents confirmation bias.
- **Every claim is traceable.** Raw tool output is preserved in each study's `raw-data/` folder, so every finding can be verified against its source.

### The Three-Agent Pipeline

```
Phase 1: Scoping Agent
   | Discovers topics, verses, Strong's numbers, related studies
   | Writes PROMPT.md (the research brief)

Phase 2: Research Agent
   | Reads PROMPT.md
   | Retrieves all verse text, runs parallels, word studies, parsing
   | Writes 01-topics.md, 02-verses.md, 04-word-studies.md
   | Saves raw tool output to raw-data/

Phase 3: Analysis Agent
   | Reads clean research files
   | Applies the evidence classification methodology
   | Writes 03-analysis.md and CONCLUSION.md
```

**Why three agents instead of one?**

- The **scoping agent** prevents training-knowledge bias. Scope comes from tool discovery, not from what the AI "knows" about theology.
- The **research agent** gets a fresh context window dedicated to data gathering. This maximizes the amount of data it can collect without running out of context.
- The **analysis agent** gets a fresh context window loaded with clean, organized research. This maximizes its capacity for synthesis and careful reasoning.

---

## The Study Files

Each study directory contains these files, produced by the pipeline:

| File | Produced By | Contents |
|------|-------------|----------|
| `PROMPT.md` | Scoping Agent | The research brief: tool-discovered topics, verses, Strong's numbers, related studies, and focus areas |
| `01-topics.md` | Research Agent | Nave's Topical Bible entries with all verse references for each topic |
| `02-verses.md` | Research Agent | Full KJV text for every verse examined, organized thematically |
| `04-word-studies.md` | Research Agent | Strong's concordance data: Hebrew/Greek words, definitions, translation statistics, verse occurrences |
| `raw-data/` | Research Agent | Raw tool output archived by category (Strong's lookups, parsing, parallels, etc.) |
| `03-analysis.md` | Analysis Agent | Verse-by-verse analysis with full evidence classification applied |
| `CONCLUSION.md` | Analysis Agent | Evidence tables (E/N/I), tally, and final assessment |

---

## Data Sources

The tools draw from these primary data sources:

| Source | Description | Size |
|--------|-------------|------|
| **KJV Bible** | Complete King James Version text | 31,102 verses |
| **Nave's Topical Bible** | Orville J. Nave's topical dictionary | 5,319 topics |
| **Strong's Concordance** | James Strong's exhaustive concordance with Hebrew/Greek lexicon | Every word in the KJV mapped to original language |
| **BHSA** (Biblia Hebraica Stuttgartensia Amstelodamensis) | Hebrew Bible linguistic database via Text-Fabric | Full morphological parsing of every Hebrew word |
| **N1904** (Nestle 1904) | Greek New Testament linguistic database via Text-Fabric | Full morphological parsing of every Greek word |
| **Textus Receptus** | Byzantine Greek text tradition | For textual variant comparison |
| **LXX Mapping** | Septuagint translation correspondences | Hebrew-to-Greek word mappings |
| **Sentence embeddings** | Pre-computed semantic vectors | For semantic search across all sources |

---

## Evidence Classification Methodology

The core of the methodology is a three-tier evidence classification system that distinguishes between what Scripture directly states, what necessarily follows from it, and what positions claim it implies.

### The Three Tiers

**E -- Explicit.** "The Bible says X." You can point to a verse that says X. A close paraphrase of the actual words of a specific verse, with no concept, framework, or interpretation added beyond what the words themselves require.

**N -- Necessary Implication.** "The Bible implies X." You can point to verses that, when combined, force X with no alternative. Every reader from any theological position must agree this follows -- no additional reasoning is required.

**I -- Inference.** "A position claims the Bible teaches X." No verse explicitly states X, and no combination of verses necessarily implies X. Something must be added beyond what the text contains.

**Critical rule:** Inferences cannot block explicit statements or necessary implications. If E and N items establish X, the existence of passages that *could be inferred* to teach not-X does not prevent X from being established.

---

### The 4-Type Inference Taxonomy

Inferences are further classified on two dimensions:

|  | Derived from E/N | Not derived from E/N |
|--|--|--|
| **Aligns with E/N** | **I-A** (Evidence-Extending) | **I-C** (Compatible External) |
| **Conflicts with E/N** | **I-B** (Competing-Evidence) | **I-D** (Counter-Evidence External) |

**I-A (Evidence-Extending):** Uses only vocabulary and concepts found in E/N statements. An inference only because it systematizes multiple E/N items into a broader claim. Strongest inference type.

**I-B (Competing-Evidence):** Some E/N statements support it, but other E/N statements appear to contradict it. Genuine textual tension where both sides can cite Scripture. Requires the SIS Resolution Protocol.

**I-C (Compatible External):** Reasoning from outside the text (theological tradition, philosophical framework, historical context) that does not contradict any E/N statement. Supplemental only.

**I-D (Counter-Evidence External):** External concepts that require overriding, redefining, or qualifying E/N statements to be maintained. Weakest inference type.

**Evidence hierarchy:** E > N > I-A > I-B (resolved by SIS) > I-C > I-D

---

### Positional Classification

Evidence items are classified by position (Historicist, Anti-Historicist, or Neutral/Shared) based on the same methodology used across the series. Items are classified positionally **only when one side must deny the textual observation.** Factual observations that both sides must accept are classified Neutral regardless of which side cites them.

[**Read the Full Methodology**](methodology.md){ .md-button }
"""
    tools_path = DOCS / "tools.md"
    tools_path.write_text(content, encoding="utf-8")
    print(f"  Generated {tools_path}")


def copy_assets():
    """Copy shared assets from etc-website."""
    js_src = ETC_WEBSITE / "docs" / "javascripts"
    js_dest = DOCS / "javascripts"
    js_dest.mkdir(parents=True, exist_ok=True)
    for fname in ["verse-popup.js", "study-breadcrumbs.js", "external-links.js",
                   "verses.json", "strongs.json"]:
        src = js_src / fname
        if src.exists():
            shutil.copy2(src, js_dest / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  WARNING: {src} not found")

    css_src = ETC_WEBSITE / "docs" / "stylesheets" / "extra.css"
    css_dest = DOCS / "stylesheets"
    css_dest.mkdir(parents=True, exist_ok=True)
    if css_src.exists():
        shutil.copy2(css_src, css_dest / "extra.css")
        print(f"  Copied extra.css")


def copy_methodology():
    """Copy hist-series-methodology.md to docs/methodology.md."""
    src = STUDIES_SRC / "hist-series-methodology.md"
    dest = DOCS / "methodology.md"
    if src.exists():
        shutil.copy2(src, dest)
        print(f"  Copied methodology.md")
    else:
        print(f"  WARNING: {src} not found")


def generate_deploy_yml():
    """Generate .github/workflows/deploy.yml."""
    deploy_dir = PROJECT_ROOT / ".github" / "workflows"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    content = """name: Deploy MkDocs to GitHub Pages

on:
  push:
    branches:
      - master

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure Git credentials
        run: |
          git config user.email "action@github.com"
          git config user.name "GitHub Actions"

      - uses: actions/setup-python@v5
        with:
          python-version: 3.x

      - name: Cache MkDocs dependencies
        uses: actions/cache@v4
        with:
          key: mkdocs-material-${{ hashFiles('**/requirements.txt') }}
          path: .cache
          restore-keys: mkdocs-material-

      - name: Install MkDocs Material
        run: pip install mkdocs-material

      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force
"""
    (deploy_dir / "deploy.yml").write_text(content, encoding="utf-8")
    print(f"  Generated deploy.yml")


def generate_gitignore():
    """Generate .gitignore."""
    content = """site/
.venv/
__pycache__/
node_modules/
"""
    (PROJECT_ROOT / ".gitignore").write_text(content, encoding="utf-8")
    print(f"  Generated .gitignore")


def generate_readme(study_folders: list[tuple[str, Path]]):
    """Generate README.md."""
    lines = []
    lines.append("# The Historicist Proof: Does Bible Prophecy Span History?")
    lines.append("")
    lines.append("A 19-study biblical investigation examining whether Daniel and Revelation describe a continuous span of history from the prophet's time to the second coming of Christ. 496 evidence items classified.")
    lines.append("")
    lines.append("## Studies")
    lines.append("")
    lines.append("| # | Study | Question |")
    lines.append("|---|-------|----------|")
    for key, src in study_folders:
        num = key.split("-")[1]
        short = SHORT_TITLES.get(key, key)
        full = FULL_TITLES.get(key, short)
        lines.append(f"| {num} | {short} | {full} |")
    lines.append("")
    lines.append("## Built With")
    lines.append("")
    lines.append("- [MkDocs](https://www.mkdocs.org/) with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)")
    lines.append("- Interactive Bible verse and Strong's number popups")
    lines.append("- Full KJV text and Strong's Concordance data")

    (PROJECT_ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Generated README.md")


def main():
    print("=" * 60)
    print("Building Historicist Proof Series website")
    print("=" * 60)

    # Preserve any existing conclusion-simple.md files before cleaning
    preserved_simples = {}
    if DOCS_STUDIES.exists():
        for d in DOCS_STUDIES.iterdir():
            if d.is_dir():
                simple = d / "conclusion-simple.md"
                if simple.exists():
                    preserved_simples[d.name] = simple.read_text(encoding="utf-8")
        shutil.rmtree(DOCS_STUDIES)
    DOCS_STUDIES.mkdir(parents=True)
    print(f"  Preserved {len(preserved_simples)} conclusion-simple.md files")

    # Find all study folders
    print("\n[1/7] Finding study folders...")
    study_folders = find_study_folders()
    print(f"  Found {len(study_folders)} studies")

    # Copy studies
    print("\n[2/7] Copying study files...")
    for key, src in study_folders:
        dest = copy_study(key, src, preserved_simples)
        print(f"  {key}: {src.name} -> {dest.relative_to(PROJECT_ROOT)}")

    # Copy methodology
    print("\n[3/7] Copying methodology...")
    copy_methodology()

    # Copy shared assets
    print("\n[4/7] Copying shared assets from etc-website...")
    copy_assets()

    # Generate mkdocs.yml
    print("\n[5/7] Generating mkdocs.yml...")
    generate_mkdocs_yml(study_folders)

    # Generate index.md
    print("\n[6/7] Generating index.md and tools.md...")
    generate_index_md()
    generate_tools_md()

    # Generate supporting files
    print("\n[7/7] Generating supporting files...")
    generate_deploy_yml()
    generate_gitignore()
    generate_readme(study_folders)

    print("\n" + "=" * 60)
    print("Build complete!")
    print(f"  Studies: {len(study_folders)}")
    print(f"  Output: {DOCS}")
    print("\nNext steps:")
    print("  1. cd hist-website && python add_blb_links.py docs/")
    print("  2. mkdocs serve")
    print("=" * 60)


if __name__ == "__main__":
    main()
