#!/usr/bin/env python
"""Update CM metadata YAML files from datasets.md.

Usage:
    python update_metadata.py [--fetch] [datasets_md_path]

Examples:
    # Fetch from GitHub and update (recommended)
    python update_metadata.py --fetch

    # Use local file
    python update_metadata.py /path/to/datasets.md

    # Use default local path (docs/datasets.md in this folder)
    python update_metadata.py

The script parses datasets.md and generates {universe}.yaml files.
"""

import argparse
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

# GitHub repository info
GITHUB_REPO_SSH = "git@github.com:Quantit-Github/finter-gitbook.git"
GITHUB_BRANCH = "main"
GITHUB_FILE_PATH = ".docs/finterlabs/finter-library/datasets.md"

# Universes to ignore (not available in actual data system)
IGNORE_UNIVERSES = {"vn_etf", "kr_etf", "common"}

# CM name mappings: datasets.md name -> actual data system name
# Some items in datasets.md have prefixes that don't exist in the actual data
CM_NAME_MAPPINGS: dict[str, str] = {
    "id-stock-sharia": "sharia",
    "id-stock-sector_code": "sector_code",
    # Add more mappings as discovered
}


@dataclass
class CMItem:
    """Represents a Content Model item."""

    cm_name: str
    description: str
    universe: str
    category: str

    def to_search_text(self) -> str:
        return f"{self.cm_name} | {self.description}"


def normalize_universe(text: str) -> str:
    """Convert universe header to normalized form."""
    return text.strip().lower().replace(" ", "_")


# CM value codes: cm_name -> value explanation
# These are looked up from search_db (OpenSearch) and hardcoded here for YAML generation
# Source: OpenSearch DB (finter-mcp/src/utils/opensearch_db.py)
CM_VALUE_CODES: dict[str, str] = {
    # === KR STOCK - company-status (event category) ===
    "overheating": "0=normal, 1=designation notice, 2=designated, 3=designation extended",
    "borrowing": "0=normal, 1=short-selling overheating",
    "caution": "0=normal, 1=caution",
    "market": "1=KOSPI, 2=KOSDAQ",
    "liquidation": "0=normal, 1=liquidation",
    "illiquid": "0=normal, 1=illiquid",
    "administration": "0=normal, 1=administrative",
    "alert": "0=normal, 1=investment warning",
    "abnormal": "0=normal, 1=abnormal surge",
    "suspension": "0=normal, 1=suspended",
    "list_yn": "1=listed, NaN=delisted",
    "unreliable": "0=normal, 1=unreliable disclosure",
    # === KR STOCK - governance (edge category) ===
    "exc_eq_ceo_chairman": "0=CEO≠Chairman, 1=CEO=Chairman",
    # === ID STOCK ===
    "sharia": "0=non-sharia, 1=sharia compliant",
    # Add more CM value codes here as discovered from search_db
}


def generate_note(cm_name: str, category: str, universe: str, code_mappings: dict[str, str]) -> str:
    """Generate usage note with code explanation if applicable."""
    parts = []

    # Base usage
    if "gics" in cm_name.lower():
        parts.append(f'cf.get_df("{cm_name}")')
        parts.append('cf.code_map("gics", level=1:Sector/2:IndustryGroup/3:Industry/4:SubIndustry/0:All)')
    elif "idxic" in cm_name.lower() or (universe == "id_stock" and "sector" in cm_name.lower()):
        parts.append(f'cf.get_df("{cm_name}")')
        parts.append('cf.code_map("idxic", level=1:Sector/2:Group/3:Industry/0:All)')
    elif category == "financial":
        # Financial items use get_fc
        # Note: cm_name already has pit- prefix for us_stock (added by dump_yaml)
        parts.append(f'cf.get_fc("{cm_name}")')
    else:
        parts.append(f'cf.get_df("{cm_name}")')

    # Check for code suffix in cm_name (e.g., net_buy_amt_0100 -> 0100)
    for code, desc in code_mappings.items():
        if cm_name.endswith(f"_{code}") or cm_name.endswith(f"-{code}"):
            parts.append(f"{code}={desc}")
            break

    # Add CM value codes if available (from CM_VALUE_CODES lookup)
    if cm_name in CM_VALUE_CODES:
        parts.append(CM_VALUE_CODES[cm_name])

    return " / ".join(parts)


def parse_hint_codes(content: str) -> dict[str, str]:
    """Extract code mappings from hint blocks.

    Returns dict like {"0100": "Institutions (Total)", "0101": "Securities & Futures"}
    """
    codes: dict[str, str] = {}

    # Find all hint blocks
    hint_pattern = re.compile(r"{% hint.*?%}(.*?){% endhint %}", re.DOTALL)
    # Code patterns:
    # - "* **CODE**: Description" (bold format)
    # - "* CODE: Description" (plain format)
    code_patterns = [
        re.compile(r"^\*\s+\*\*([A-Z0-9]+)\*\*:\s*(.+)$", re.MULTILINE),  # bold
        re.compile(r"^\*\s+([0-9]{4}):\s*(.+)$", re.MULTILINE),  # plain (investor codes)
    ]

    for hint_match in hint_pattern.finditer(content):
        hint_content = hint_match.group(1)
        for code_pattern in code_patterns:
            for code_match in code_pattern.finditer(hint_content):
                code = code_match.group(1)
                desc = code_match.group(2).strip()
                codes[code] = desc

    return codes


def parse_datasets_md(file_path: Path) -> tuple[list[CMItem], dict[str, str]]:
    """Parse datasets.md and extract CM items and code mappings."""
    content = file_path.read_text(encoding="utf-8")

    # Extract code mappings from hint blocks
    code_mappings = parse_hint_codes(content)

    items: list[CMItem] = []

    current_universe = ""
    current_category = ""
    in_item_list = False

    universe_pattern = re.compile(r"^#\s+([A-Z][A-Z\s]+)$")
    category_pattern = re.compile(r"^##\s+(\w+)$")
    item_pattern = re.compile(
        r"^[*•\-]\s+\*?\*?([a-z0-9_\\-]+)\*?\*?\s*[:\=]\s*(.+)$", re.IGNORECASE
    )
    bullet_pattern = re.compile(
        r"^•\s+\*\*\s*\*\*\s*([a-z0-9_\\-]+)\s*:\s*(.+)$", re.IGNORECASE
    )
    # Pattern for **item**: description format (US STOCK financial)
    bold_pattern = re.compile(
        r"^\*\*([a-z0-9_\\-]+)\*\*:\s*(.+)$", re.IGNORECASE
    )

    in_hint_block = False

    for line in content.split("\n"):
        line = line.rstrip().replace(r"\_", "_")

        if not line:
            continue

        # Track hint blocks - skip content inside them
        if "{% hint" in line:
            in_hint_block = True
            continue
        if "{% endhint %}" in line:
            in_hint_block = False
            continue
        if in_hint_block:
            continue

        universe_match = universe_pattern.match(line)
        if universe_match:
            current_universe = normalize_universe(universe_match.group(1))
            current_category = ""
            in_item_list = False
            continue

        category_match = category_pattern.match(line)
        if category_match:
            current_category = category_match.group(1).lower()
            in_item_list = False
            continue

        if line.strip() == "Item List":
            in_item_list = True
            continue

        if line.startswith("Example") or line.startswith("Metadata") or line.startswith("Data Format") or line.startswith("Report Value"):
            in_item_list = False
            continue

        # Skip known non-CM items (table format descriptions)
        if line.startswith("* **Index**") or line.startswith("* **Columns**") or line.startswith("* **Values**"):
            continue

        if in_item_list and current_universe:
            item_match = item_pattern.match(line) or bullet_pattern.match(line) or bold_pattern.match(line)
            if item_match:
                cm_name = item_match.group(1).strip()
                description = item_match.group(2).strip()
                description = re.sub(r"\\x20$", "", description).rstrip("\\")

                items.append(
                    CMItem(
                        cm_name=cm_name,
                        description=description,
                        universe=current_universe,
                        category=current_category,
                    )
                )

    return items, code_mappings


def load_existing_yaml(yaml_path: Path) -> dict[str, dict]:
    """Load existing YAML file and return items with their notes preserved."""
    if not yaml_path.exists():
        return {}

    existing: dict[str, dict] = {}
    current_item = None
    current_desc_lines = []
    current_note = ""

    with open(yaml_path, "r", encoding="utf-8") as f:
        for line in f:
            # Skip comments and empty lines for item detection
            if line.startswith("#") or not line.strip():
                continue

            # New item (starts at column 0, ends with :)
            if line[0].isalpha() and ":" in line and not line.startswith("  "):
                # Save previous item
                if current_item:
                    existing[current_item] = {
                        "description": "\n".join(current_desc_lines).strip(),
                        "note": current_note,
                    }

                current_item = line.split(":")[0].strip()
                current_desc_lines = []
                current_note = ""
            elif current_item:
                if line.strip().startswith("description:"):
                    continue
                elif line.strip().startswith("note:"):
                    # Extract note value (remove 'note: ' and quotes)
                    note_part = line.split("note:", 1)[1].strip()
                    current_note = note_part.strip("'\"")
                elif line.startswith("    ") and not line.strip().startswith("note:"):
                    current_desc_lines.append(line[4:].rstrip())

        # Save last item
        if current_item:
            existing[current_item] = {
                "description": "\n".join(current_desc_lines).strip(),
                "note": current_note,
            }

    return existing


def dump_yaml(items: list[CMItem], output_dir: Path, code_mappings: dict[str, str]):
    """Dump items to YAML files per universe, preserving existing items not in datasets.md."""
    # Group by universe
    by_universe: dict[str, list[CMItem]] = {}
    for item in items:
        by_universe.setdefault(item.universe, []).append(item)

    for universe, universe_items in by_universe.items():
        # Skip ignored universes
        if universe in IGNORE_UNIVERSES:
            print(f"Skipped {universe} (in IGNORE_UNIVERSES)")
            continue

        yaml_path = output_dir / f"{universe}.yaml"

        # Load existing items to preserve ones not in datasets.md
        existing_items = load_existing_yaml(yaml_path)

        # Group by category
        by_category: dict[str, list[CMItem]] = {}
        for item in universe_items:
            by_category.setdefault(item.category, []).append(item)

        # Track which items we're writing from datasets.md
        new_item_names: set[str] = set()

        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(f"# {universe.upper().replace('_', ' ')} CM Items\n")
            f.write("# Searchable by description\n\n")

            for category in sorted(by_category.keys()):
                f.write(f"# === {category.title()} ===\n\n")

                seen_names: dict[str, int] = {}
                for item in sorted(by_category[category], key=lambda x: x.cm_name):
                    cm_name = item.cm_name
                    desc = item.description

                    # Apply CM name mappings (datasets.md name -> actual data system name)
                    cm_name = CM_NAME_MAPPINGS.get(cm_name, cm_name)

                    # Add pit- prefix for US stock financial items
                    if item.category == "financial" and item.universe == "us_stock":
                        cm_name = f"pit-{cm_name}"

                    # Handle duplicates
                    if cm_name in seen_names:
                        seen_names[cm_name] += 1
                        if "weekly" in desc.lower():
                            cm_name = f"{cm_name}_weekly"
                        elif "monthly" in desc.lower():
                            cm_name = f"{cm_name}_monthly"
                        else:
                            cm_name = f"{cm_name}_{seen_names[item.cm_name]}"
                    else:
                        seen_names[cm_name] = 1

                    new_item_names.add(cm_name)

                    f.write(f"{cm_name}:\n")
                    f.write(f"  description: |\n    {desc}\n")
                    f.write(f"  note: '{generate_note(cm_name, item.category, item.universe, code_mappings)}'\n")
                    f.write("\n")

            # Preserve items from existing YAML that are not in datasets.md
            preserved_items = {k: v for k, v in existing_items.items()
                              if k not in new_item_names and k not in ("Index", "Columns", "Values")}
            if preserved_items:
                f.write("# === Preserved (not in datasets.md) ===\n\n")
                for cm_name in sorted(preserved_items.keys()):
                    item_data = preserved_items[cm_name]
                    f.write(f"{cm_name}:\n")
                    f.write(f"  description: |\n    {item_data['description']}\n")
                    f.write(f"  note: '{item_data['note']}'\n")
                    f.write("\n")

        total_items = len(universe_items) + len(preserved_items)
        preserved_count = len(preserved_items)
        if preserved_count > 0:
            print(f"Wrote {yaml_path} ({len(universe_items)} items + {preserved_count} preserved)")
        else:
            print(f"Wrote {yaml_path} ({len(universe_items)} items)")


def fetch_from_github(dest_path: Path) -> bool:
    """Fetch datasets.md from GitHub via git sparse checkout."""
    print("Fetching datasets.md from GitHub (SSH)...")
    print(f"  Repo: {GITHUB_REPO_SSH}")
    print(f"  Branch: {GITHUB_BRANCH}")
    print(f"  File: {GITHUB_FILE_PATH}")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Initialize sparse checkout
            subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
            subprocess.run(
                ["git", "remote", "add", "origin", GITHUB_REPO_SSH],
                cwd=tmpdir, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "core.sparseCheckout", "true"],
                cwd=tmpdir, check=True, capture_output=True
            )

            # Set sparse checkout path
            sparse_file = tmpdir_path / ".git" / "info" / "sparse-checkout"
            sparse_file.parent.mkdir(parents=True, exist_ok=True)
            sparse_file.write_text(GITHUB_FILE_PATH + "\n")

            # Fetch and checkout
            subprocess.run(
                ["git", "fetch", "--depth=1", "origin", GITHUB_BRANCH],
                cwd=tmpdir, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "checkout", GITHUB_BRANCH],
                cwd=tmpdir, check=True, capture_output=True
            )

            # Copy file to destination
            src_file = tmpdir_path / GITHUB_FILE_PATH
            if not src_file.exists():
                print(f"  ERROR: File not found in repo: {GITHUB_FILE_PATH}")
                return False

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(src_file.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  Saved to: {dest_path}")
            return True

    except subprocess.CalledProcessError as e:
        print(f"  ERROR: Git command failed: {e}")
        if e.stderr:
            print(f"  {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Update CM metadata from datasets.md")
    parser.add_argument(
        "datasets_md",
        nargs="?",
        help="Path to datasets.md (default: docs/datasets.md in this folder)",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch datasets.md from GitHub before updating",
    )
    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    output_dir = script_dir
    datasets_path = script_dir / "docs" / "datasets.md"

    # Fetch from GitHub if requested
    if args.fetch:
        if not fetch_from_github(datasets_path):
            return 1
    elif args.datasets_md:
        datasets_path = Path(args.datasets_md)

    if not datasets_path.exists():
        print(f"ERROR: datasets.md not found at {datasets_path}")
        print("\nTo update metadata:")
        print("  1. Run with --fetch to download from GitHub:")
        print("     python update_metadata.py --fetch")
        print("  2. Or specify a local path:")
        print("     python update_metadata.py /path/to/datasets.md")
        return 1

    print(f"Parsing {datasets_path}...")
    items, code_mappings = parse_datasets_md(datasets_path)
    print(f"Parsed {len(items)} CM items")
    print(f"Found {len(code_mappings)} code mappings")

    print(f"\nWriting YAML files to {output_dir}...")
    dump_yaml(items, output_dir, code_mappings)

    # Stats
    universes = {}
    categories = {}
    for item in items:
        universes[item.universe] = universes.get(item.universe, 0) + 1
        categories[item.category] = categories.get(item.category, 0) + 1

    print("\n=== Stats ===")
    print(f"Total: {len(items)}")
    print("By universe:", universes)
    print("By category:", categories)

    return 0


if __name__ == "__main__":
    exit(main())
