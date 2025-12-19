#!/usr/bin/env python3
"""
Link Checker - Validates links in CSV and outputs original + explanation rows
Reads line by line, checks each link, writes NEW CSV with results
Uses GET requests with proper headers to bypass blocks (unblocked solution)
"""

import csv
from pathlib import Path
from typing import Dict, Tuple
import requests
import time
from utils import URLValidator


class LinkChecker:
    def __init__(self, csv_path: str, output_path: str = None):
        """
        Initialize link checker

        Args:
            csv_path: Path to CSV file to check
            output_path: Path for output CSV (if None, creates _CHECKED.csv)
        """
        self.csv_path = Path(csv_path)
        self.output_path = (
            Path(output_path)
            if output_path
            else Path("output") / f"{self.csv_path.stem}_CHECKED.csv"
        )

        self.validator = URLValidator(timeout=10)

        self.link_columns = [
            "Homepage",
            "Privacy/Legal Link",
            "DSGVO/GDPR Link",
            "Storage/Hosting Link",
            "DPA/AVV Link",
        ]

    def check_link(self, url: str) -> Tuple[bool, str]:
        """
        Check if link is valid using GET with proper headers (unblocked method)

        Args:
            url: URL to check

        Returns:
            Tuple of (is_valid, reason)
        """
        if not url or not url.strip():
            return False, "⚠️ Empty URL"

        # Use URLValidator which tries HEAD then GET for blocked links
        is_valid, status = self.validator.validate_url(url)
        if is_valid:
            return True, f"✅ Valid ({status})"
        else:
            return False, f"❌ Invalid ({status})"

    def process(self, start_line: int = 1, end_line: int = None):
        """
        Process CSV line by line

        Args:
            start_line: Starting line (1-indexed)
            end_line: Ending line (inclusive)
        """
        # Read CSV - skip empty header row
        print("📂 Reading CSV...")
        rows = []
        fieldnames = []

        with open(self.csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Skip first empty line(s), find actual header
            for i, line in enumerate(lines):
                if "App name" in line or "Kategorie" in line:
                    # Found real header, read from here
                    f_temp = open(self.csv_path, "r", encoding="utf-8")
                    reader = csv.DictReader(f_temp.readlines()[i:], delimiter=";")
                    fieldnames = reader.fieldnames or []
                    rows = list(reader)
                    f_temp.close()
                    break

        print(f"✅ Loaded {len(rows)} rows")

        # Determine processing range
        total = len(rows)
        end_line = end_line if end_line else total
        start_idx = start_line - 1
        end_idx = min(end_line, total)

        print(f"\n{'=' * 80}")
        print(f"🔍 CHECKING LINKS (lines {start_line} to {end_idx})")
        print(f"{'=' * 80}\n")

        output_rows = []

        # Add rows before processing range
        output_rows.extend(rows[:start_idx])

        # Process each row
        for idx in range(start_idx, end_idx):
            original_row = rows[idx]
            line_num = idx + 1

            tool_name = original_row.get("App name", f"Tool #{line_num}")
            print(f"📍 Line {line_num}: {tool_name}")

            # Create explanation row
            explanation_row = {key: "" for key in fieldnames}
            explanation_row["App name"] = "[LINK CHECK RESULTS]"

            # Check each link column
            for link_col in self.link_columns:
                if link_col not in fieldnames:
                    continue

                url = original_row.get(link_col, "").strip()

                if not url:
                    explanation_row[link_col] = "⚠️ No URL"
                    print(f"  ⚠️  {link_col}: No URL")
                else:
                    is_valid, reason = self.check_link(url)
                    explanation_row[link_col] = reason
                    print(f"  {reason} {link_col}")

                time.sleep(0.5)  # Rate limiting

            # Add both rows to output
            output_rows.append(original_row)
            output_rows.append(explanation_row)

        # Add rows after processing range
        if end_idx < len(rows):
            output_rows.extend(rows[end_idx:])

        # Write output CSV
        print(f"\n{'=' * 80}")
        print("💾 Writing output CSV...")

        with open(self.output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=fieldnames, delimiter=";", extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(output_rows)

        print(f"✅ Output: {self.output_path}")
        print(f"\nStructure:")
        print(f"  - Original data row")
        print(f"  - Explanation row with test results")
        print(f"  - (repeats for each tool)")


def main():
    """Command line interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python link_checker.py <csv_file> [start_line] [end_line]")
        print("Example: python link_checker.py 'Andreesen Tools 50 - UPDATED.csv' 1 5")
        sys.exit(1)

    csv_file = sys.argv[1]
    start_line = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end_line = int(sys.argv[3]) if len(sys.argv) > 3 else None

    checker = LinkChecker(csv_file)
    checker.process(start_line=start_line, end_line=end_line)


if __name__ == "__main__":
    main()
