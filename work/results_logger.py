#!/usr/bin/env python3
"""
Results Logger - Tracks and saves validation results
Creates a detailed log of all findings and changes
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ResultsLogger:
    def __init__(self):
        """Initialize the results logger"""
        self.results = []
        self.start_time = datetime.now()

    def log_result(self, line_num: int, tool_name: str, result: Dict):
        """
        Log a validation result

        Args:
            line_num: Line number in the CSV
            tool_name: Name of the tool
            result: Result dictionary from researcher
        """
        log_entry = {
            "line_number": line_num,
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat(),
            "changed": result["changed"],
            "summary": result["summary"],
            "details": result["details"],
        }

        # Add before/after comparison if changes were made
        if result["changed"]:
            log_entry["changes"] = self._get_changes(result["original"], result["row"])

        self.results.append(log_entry)

    def _get_changes(self, original: Dict, updated: Dict) -> List[Dict]:
        """
        Get the list of field changes

        Args:
            original: Original row data
            updated: Updated row data

        Returns:
            List of change dictionaries
        """
        changes = []
        for field in original.keys():
            if original[field] != updated[field]:
                changes.append(
                    {
                        "field": field,
                        "old_value": original[field],
                        "new_value": updated[field],
                    }
                )
        return changes

    def save_log(self, output_dir: Path) -> Path:
        """
        Save the log to a file

        Args:
            output_dir: Directory to save the log

        Returns:
            Path to the saved log file
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Create summary statistics
        total_processed = len(self.results)
        total_changed = sum(1 for r in self.results if r["changed"])
        total_unchanged = total_processed - total_changed

        log_data = {
            "summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_processed": total_processed,
                "total_changed": total_changed,
                "total_unchanged": total_unchanged,
            },
            "results": self.results,
        }

        # Save JSON log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"validation_log_{timestamp}.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        # Save human-readable log
        txt_path = output_dir / f"validation_log_{timestamp}.txt"
        self._save_readable_log(txt_path, log_data)

        return json_path

    def _save_readable_log(self, path: Path, log_data: Dict):
        """
        Save a human-readable version of the log

        Args:
            path: Path to save the log
            log_data: Log data dictionary
        """
        with open(path, "w", encoding="utf-8") as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write("AI TOOLS VALIDATION LOG\n")
            f.write("=" * 80 + "\n\n")

            # Write summary
            summary = log_data["summary"]
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Start Time:        {summary['start_time']}\n")
            f.write(f"End Time:          {summary['end_time']}\n")
            f.write(f"Duration:          {summary['duration_seconds']:.2f} seconds\n")
            f.write(f"Total Processed:   {summary['total_processed']}\n")
            f.write(f"Total Changed:     {summary['total_changed']}\n")
            f.write(f"Total Unchanged:   {summary['total_unchanged']}\n")
            f.write("\n\n")

            # Write individual results
            f.write("DETAILED RESULTS\n")
            f.write("=" * 80 + "\n\n")

            for result in log_data["results"]:
                f.write(f"Line #{result['line_number']}: {result['tool_name']}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Changed: {'YES' if result['changed'] else 'NO'}\n")
                f.write(f"Summary: {result['summary']}\n")
                f.write(f"Timestamp: {result['timestamp']}\n\n")

                # Write details
                if result["details"]:
                    f.write("Details:\n")
                    for detail in result["details"]:
                        f.write(f"  • {detail}\n")
                    f.write("\n")

                # Write changes if any
                if "changes" in result:
                    f.write("Changes Made:\n")
                    for change in result["changes"]:
                        f.write(f"  Field: {change['field']}\n")
                        f.write(f"    Old: {change['old_value']}\n")
                        f.write(f"    New: {change['new_value']}\n")
                    f.write("\n")

                f.write("\n")
