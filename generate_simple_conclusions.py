#!/usr/bin/env python3
"""
generate_simple_conclusions.py — Generate conclusion-simple.md for each hist study.

Reads each study's CONCLUSION.md and uses the Anthropic API to produce
a plain-language summary.
"""

import os
import re
import sys
import time
import anthropic
from pathlib import Path

DOCS_STUDIES = Path(__file__).resolve().parent / "docs" / "studies"
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are a Bible study summarizer. You convert technical evidence-based
Bible study conclusions into plain-language summaries that any reader can understand.

Rules:
- Write in clear, accessible English. No theological jargon unless you explain it.
- NEVER mention evidence tiers (E, N, I-A, I-B, I-C, I-D), evidence classification,
  or the methodology system. The reader should not know this system exists.
- NEVER include evidence tables, tallies, or counts.
- DO include direct Bible quotations (KJV) with references — these are essential.
- DO preserve the study's actual findings and conclusions faithfully.
- DO cover what the Bible says AND what it does not say on this topic.
- This series investigates whether Daniel and Revelation describe continuous history
  (historicism) vs. first-century events (preterism), future events (futurism), or
  timeless truths (idealism). Present the findings clearly.
- Follow this structure:
  1. Title (# heading) — a clear statement of the topic
  2. ## A Plain-English Summary of the Biblical Evidence (subtitle)
  3. Introduction — frame the question being investigated
  4. Multiple sections covering the main findings, with Bible quotes
  5. A section on what the Bible does NOT say (common misconceptions)
  6. Conclusion — summarize the overall finding
  7. Closing line: *Based on the full technical study completed [date]*
- The summary should be substantial — typically 1500-3000 words.
- Present both sides fairly where there is genuine debate, but state clearly
  where the weight of biblical evidence falls.
- Use > blockquote format for Bible verses.
- Use --- between major sections.
- Do NOT add any cross-references to other studies in the series."""

USER_PROMPT_TEMPLATE = """Read this technical Bible study conclusion and write a plain-language
summary (conclusion-simple.md) following the format described in your instructions.

The study folder is: {slug}

Here is the full CONCLUSION.md:

{conclusion_text}"""


def get_study_folders():
    """Find all hist study folders in docs/studies/."""
    folders = []
    for d in sorted(DOCS_STUDIES.iterdir()):
        if d.is_dir() and re.match(r"hist-\d{2}-", d.name):
            folders.append(d)
    return folders


def generate_simple(client, folder: Path) -> str:
    """Generate a conclusion-simple.md for one study."""
    conclusion_path = folder / "CONCLUSION.md"
    if not conclusion_path.exists():
        print(f"  WARNING: No CONCLUSION.md in {folder.name}")
        return None

    conclusion_text = conclusion_path.read_text(encoding="utf-8")

    # Truncate if extremely long (> 80K chars) to fit in context
    if len(conclusion_text) > 80000:
        conclusion_text = conclusion_text[:80000] + "\n\n[... truncated for length ...]"

    message = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    slug=folder.name,
                    conclusion_text=conclusion_text,
                ),
            }
        ],
    )

    return message.content[0].text


def main():
    client = anthropic.Anthropic()
    folders = get_study_folders()

    # Allow specifying specific studies on command line
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        targets = set(sys.argv[1:])
        folders = [f for f in folders if f.name in targets or
                   re.match(r"hist-(\d{2})", f.name).group(0) in targets]

    print(f"Generating conclusion-simple.md for {len(folders)} studies...\n")

    for i, folder in enumerate(folders, 1):
        output_path = folder / "conclusion-simple.md"

        # Skip if already exists (use --force to regenerate)
        if output_path.exists() and "--force" not in sys.argv:
            print(f"[{i}/{len(folders)}] {folder.name}: already exists (skip)")
            continue

        print(f"[{i}/{len(folders)}] {folder.name}: generating...", end="", flush=True)

        try:
            result = generate_simple(client, folder)
            if result:
                output_path.write_text(result + "\n", encoding="utf-8")
                word_count = len(result.split())
                print(f" done ({word_count} words)")
            else:
                print(" skipped (no CONCLUSION.md)")
        except Exception as e:
            print(f" ERROR: {e}")
            continue

    print("\nDone! Run build_site.py to update mkdocs.yml navigation.")


if __name__ == "__main__":
    main()
