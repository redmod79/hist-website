#!/usr/bin/env python3
"""
Add Blue Letter Bible links to Strong's numbers, Hebrew words, and Greek words
in the etc-website markdown files.

Strong's numbers (H1234, G1234) are linked to their BLB lexicon pages.
Links open in a new tab via the attr_list extension ({target="_blank"}).

Usage:
    python add_blb_links.py                    # Process all study files
    python add_blb_links.py --dry-run          # Show what would change without modifying files
    python add_blb_links.py --revert           # Remove all BLB links (restore original text)
    python add_blb_links.py --stats            # Show statistics only
"""

import re
import os
import sys
import argparse
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "docs" / "studies"

# BLB URL patterns
BLB_HEBREW_URL = "https://www.blueletterbible.org/lexicon/h{num}/kjv/wlc/0-1/"
BLB_GREEK_URL = "https://www.blueletterbible.org/lexicon/g{num}/kjv/tr/0-1/"

# Match Strong's numbers NOT already inside markdown links
# Negative lookbehind for [ (already linked) or ( (inside URL) or / (inside URL path)
STRONGS_PATTERN = re.compile(
    r'(?<!\[)'           # not preceded by [
    r'(?<!\()'           # not preceded by (
    r'(?<!\/)'           # not preceded by /
    r'(?<!`)'            # not preceded by backtick
    r'\b([HG])(\d{1,5})\b'  # H or G followed by 1-5 digits
    r'(?!\])'            # not followed by ]
    r'(?!\))'            # not followed by )
    r'(?!`)'             # not followed by backtick
)

# Match our generated BLB links for revert
BLB_LINK_PATTERN = re.compile(
    r'\[([HG]\d{1,5})\]\(https://www\.blueletterbible\.org/lexicon/[hg]\d{1,5}/kjv/(?:wlc|tr)/0-1/\)\{:target="_blank"\}'
)


def should_skip_line(line):
    """Check if a line should be skipped (headers, code blocks, etc.)."""
    stripped = line.strip()
    # Skip empty lines
    if not stripped:
        return True
    # Skip lines that are purely markdown headers
    if stripped.startswith('#'):
        return True
    # Skip lines inside code fences (caller must track state)
    # Skip HTML comments
    if stripped.startswith('<!--') or stripped.startswith('-->'):
        return True
    return False


def is_in_code_block(lines, line_idx):
    """Check if a line is inside a fenced code block."""
    fence_count = 0
    for i in range(line_idx):
        if lines[i].strip().startswith('```'):
            fence_count += 1
    return fence_count % 2 == 1


def is_in_table_header(line):
    """Check if line is a table separator (|---|---|)."""
    return bool(re.match(r'^\s*\|[\s\-:|]+\|\s*$', line))


def is_in_existing_link(text, match_start, match_end):
    """Check if the match position is inside an existing markdown link."""
    # Check if we're inside [text](url) - look for enclosing brackets
    # Search backward for unmatched [
    bracket_depth = 0
    for i in range(match_start - 1, -1, -1):
        if text[i] == ']':
            bracket_depth += 1
        elif text[i] == '[':
            if bracket_depth == 0:
                # We're inside a [ ... ] - check if it's part of a link
                return True
            bracket_depth -= 1
        elif text[i] == ')':
            # Check if inside (url) part
            pass
        elif text[i] == '(':
            # We might be inside a URL
            # Check if preceded by ]
            for j in range(i - 1, -1, -1):
                if text[j] == ' ' or text[j] == '\n':
                    continue
                if text[j] == ']':
                    return True  # Inside URL part of [text](url)
                break

    # Also check if inside parentheses that follow ]
    paren_depth = 0
    for i in range(match_start - 1, -1, -1):
        if text[i] == ')':
            paren_depth += 1
        elif text[i] == '(':
            if paren_depth == 0:
                # Check if this ( is preceded by ]
                for j in range(i - 1, -1, -1):
                    if text[j] in ' \t':
                        continue
                    if text[j] == ']':
                        return True
                    break
            paren_depth -= 1
    return False


def add_links_to_line(line):
    """Add BLB links to Strong's numbers in a single line."""
    if not STRONGS_PATTERN.search(line):
        return line, 0

    result = []
    last_end = 0
    count = 0

    for match in STRONGS_PATTERN.finditer(line):
        prefix = match.group(1)  # H or G
        num = match.group(2)
        start = match.start()
        end = match.end()

        # Skip if inside an existing markdown link
        if is_in_existing_link(line, start, end):
            result.append(line[last_end:end])
            last_end = end
            continue

        # Skip if the number is too large (not a real Strong's number)
        num_int = int(num)
        if prefix == 'H' and num_int > 8850:
            result.append(line[last_end:end])
            last_end = end
            continue
        if prefix == 'G' and num_int > 5900:
            result.append(line[last_end:end])
            last_end = end
            continue

        # Skip very small numbers that are likely not Strong's (H1, G1, etc.)
        if num_int < 1:
            result.append(line[last_end:end])
            last_end = end
            continue

        # Build the link
        strongs_id = f"{prefix}{num}"
        if prefix == 'H':
            url = BLB_HEBREW_URL.format(num=num.lower())
        else:
            url = BLB_GREEK_URL.format(num=num.lower())

        link = f'[{strongs_id}]({url}){{:target="_blank"}}'

        result.append(line[last_end:start])
        result.append(link)
        last_end = end
        count += 1

    result.append(line[last_end:])
    return ''.join(result), count


def process_file(filepath, dry_run=False):
    """Process a single markdown file, adding BLB links."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    total_links = 0
    in_code_block = False

    for i, line in enumerate(lines):
        # Track code fence state
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue

        # Skip lines in code blocks
        if in_code_block:
            new_lines.append(line)
            continue

        # Skip table separator lines
        if is_in_table_header(line):
            new_lines.append(line)
            continue

        # Process the line
        new_line, count = add_links_to_line(line)
        new_lines.append(new_line)
        total_links += count

    new_content = '\n'.join(new_lines)

    if total_links > 0 and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return total_links


def revert_file(filepath):
    """Remove BLB links from a file, restoring plain Strong's numbers."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = BLB_LINK_PATTERN.sub(r'\1', content)
    changes = len(BLB_LINK_PATTERN.findall(content))

    if changes > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return changes


def get_all_md_files():
    """Get all markdown files in the studies directory."""
    files = []
    for root, dirs, filenames in os.walk(DOCS_DIR):
        for filename in filenames:
            if filename.endswith('.md'):
                files.append(Path(root) / filename)
    return sorted(files)


def collect_stats():
    """Collect statistics about Strong's numbers across all files."""
    hebrew_nums = {}
    greek_nums = {}

    for filepath in get_all_md_files():
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        study = filepath.parent.name
        if study == 'raw-data':
            study = filepath.parent.parent.name

        for match in STRONGS_PATTERN.finditer(content):
            prefix = match.group(1)
            num = int(match.group(2))
            strongs_id = f"{prefix}{match.group(2)}"

            if prefix == 'H' and num <= 8850:
                if strongs_id not in hebrew_nums:
                    hebrew_nums[strongs_id] = set()
                hebrew_nums[strongs_id].add(study)
            elif prefix == 'G' and num <= 5900:
                if strongs_id not in greek_nums:
                    greek_nums[strongs_id] = set()
                greek_nums[strongs_id].add(study)

    return hebrew_nums, greek_nums


def main():
    parser = argparse.ArgumentParser(description="Add Blue Letter Bible links to Strong's numbers")
    parser.add_argument('--dry-run', action='store_true', help="Show what would change without modifying files")
    parser.add_argument('--revert', action='store_true', help="Remove all BLB links")
    parser.add_argument('--stats', action='store_true', help="Show statistics only")
    parser.add_argument('--master-file', type=str, help="Write master list to this file")
    args = parser.parse_args()

    if args.stats or args.master_file:
        hebrew_nums, greek_nums = collect_stats()
        print(f"Unique Hebrew Strong's numbers: {len(hebrew_nums)}")
        print(f"Unique Greek Strong's numbers: {len(greek_nums)}")
        print(f"Total unique Strong's numbers: {len(hebrew_nums) + len(greek_nums)}")
        print()

        if args.master_file:
            with open(args.master_file, 'w', encoding='utf-8') as f:
                f.write("# Master Strong's Numbers List\n\n")
                f.write(f"Total unique: {len(hebrew_nums) + len(greek_nums)} "
                        f"({len(hebrew_nums)} Hebrew, {len(greek_nums)} Greek)\n\n")

                f.write("## Hebrew Strong's Numbers\n\n")
                f.write("| Number | BLB Link | Studies |\n")
                f.write("|--------|----------|----------|\n")
                for num in sorted(hebrew_nums.keys(), key=lambda x: int(x[1:])):
                    studies = ', '.join(sorted(hebrew_nums[num]))
                    url = BLB_HEBREW_URL.format(num=num[1:])
                    f.write(f"| {num} | {url} | {studies} |\n")

                f.write(f"\n## Greek Strong's Numbers\n\n")
                f.write("| Number | BLB Link | Studies |\n")
                f.write("|--------|----------|----------|\n")
                for num in sorted(greek_nums.keys(), key=lambda x: int(x[1:])):
                    studies = ', '.join(sorted(greek_nums[num]))
                    url = BLB_GREEK_URL.format(num=num[1:])
                    f.write(f"| {num} | {url} | {studies} |\n")

            print(f"Master file written to: {args.master_file}")
        return

    files = get_all_md_files()
    total_changes = 0

    if args.revert:
        print("Reverting BLB links...")
        for filepath in files:
            changes = revert_file(filepath)
            if changes > 0:
                rel = filepath.relative_to(DOCS_DIR)
                print(f"  {rel}: reverted {changes} links")
                total_changes += changes
        print(f"\nTotal: reverted {total_changes} links across all files")
    else:
        action = "Would add" if args.dry_run else "Added"
        if args.dry_run:
            print("DRY RUN - no files will be modified\n")

        for filepath in files:
            links_added = process_file(filepath, dry_run=args.dry_run)
            if links_added > 0:
                rel = filepath.relative_to(DOCS_DIR)
                print(f"  {rel}: {action} {links_added} links")
                total_changes += links_added

        print(f"\nTotal: {action.lower()} {total_changes} links across all files")


if __name__ == '__main__':
    main()
