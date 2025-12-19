#!/usr/bin/env python3
"""
Main Processor - Orchestrates the CSV validation process
Reads the CSV line by line and delegates validation to the researcher agent
"""

import csv
import sys
from pathlib import Path
from datetime import datetime
from link_researcher import LinkResearcher
from results_logger import ResultsLogger


class MainProcessor:
    def __init__(self, csv_path, output_path=None, start_line=1, end_line=None):
        """
        Initialize the main processor

        Args:
            csv_path: Path to the input CSV file
            output_path: Path for the corrected output CSV (defaults to input_VALIDATED.csv)
            start_line: Line number to start processing from (1-indexed, excluding header)
            end_line: Line number to stop processing at (inclusive)
        """
        self.csv_path = Path(csv_path)
        self.output_path = (
            Path(output_path)
            if output_path
            else self.csv_path.parent / f"{self.csv_path.stem}_VALIDATED.csv"
        )
        self.start_line = start_line
        self.end_line = end_line

        self.researcher = LinkResearcher()
        self.logger = ResultsLogger()

    def process(self):
        """Main processing loop"""
        print(f"🚀 Starting validation of {self.csv_path}")
        print(f"📊 Processing lines {self.start_line} to {self.end_line or 'end'}")
        print("=" * 80)

        rows = []
        header = None
        processed_count = 0
        changed_count = 0

        # Read all rows first
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            header = reader.fieldnames
            for row in reader:
                rows.append(row)

        # Determine which rows to process
        total_rows = len(rows)
        start_idx = self.start_line - 1  # Convert to 0-indexed
        end_idx = self.end_line if self.end_line else total_rows

        print(f"📄 Total rows in file: {total_rows}")
        print(f"🎯 Will process rows {start_idx + 1} to {end_idx}")
        print("=" * 80 + "\n")

        # Process specified rows
        for idx in range(start_idx, min(end_idx, total_rows)):
            row = rows[idx]
            line_num = idx + 1
            processed_count += 1

            print(f"\n{'=' * 80}")
            print(f"📍 Processing #{line_num}: {row['Tool Name']}")
            print(f"{'=' * 80}")

            # Research and validate this row
            result = self.researcher.research_and_validate(row, line_num)

            # Update the row if changes were made
            if result["changed"]:
                rows[idx] = result["row"]
                changed_count += 1

            # Log the result
            self.logger.log_result(line_num, row["Tool Name"], result)

            print(f"\n✅ Completed #{line_num}: {result['summary']}")

        # Write the updated CSV
        self._write_csv(header, rows)

        # Save the log
        log_path = self.logger.save_log(self.output_path.parent)

        # Print summary
        print("\n" + "=" * 80)
        print("🎉 PROCESSING COMPLETE")
        print("=" * 80)
        print(f"📊 Processed: {processed_count} rows")
        print(f"✏️  Changed: {changed_count} rows")
        print(f"💾 Output CSV: {self.output_path}")
        print(f"📋 Results log: {log_path}")
        print("=" * 80)

    def _write_csv(self, header, rows):
        """Write the updated CSV file"""
        with open(self.output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)


def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("Usage: python main_processor.py <csv_file> [start_line] [end_line]")
        print("Example: python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 1 10")
        sys.exit(1)

    csv_file = sys.argv[1]
    start_line = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end_line = int(sys.argv[3]) if len(sys.argv) > 3 else None

    processor = MainProcessor(csv_file, start_line=start_line, end_line=end_line)
    processor.process()


if __name__ == "__main__":
    main()
