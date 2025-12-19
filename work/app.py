#!/usr/bin/env python3
"""
Andreesen 50 Tools - Main Entry Point
Orchestrates all operations: link checking, content analysis, validation
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Andreesen 50 Tools - Complete Analysis Pipeline"
    )
    parser.add_argument(
        "command", choices=["check", "analyze", "validate"], help="Command to run"
    )
    parser.add_argument("csv_file", help="Input CSV file")
    parser.add_argument(
        "--start", type=int, default=1, help="Starting line (1-indexed)"
    )
    parser.add_argument("--end", type=int, default=None, help="Ending line (inclusive)")
    parser.add_argument("--output", type=str, default=None, help="Output CSV file path")
    parser.add_argument(
        "--ollama-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama service URL",
    )
    parser.add_argument(
        "--model", type=str, default="gpt-oss:20b", help="Ollama model to use"
    )

    args = parser.parse_args()

    if args.command == "check":
        from link_checker import LinkChecker

        print(f"\n{'=' * 80}")
        print("🔗 LINK CHECKER")
        print(f"{'=' * 80}\n")
        checker = LinkChecker(args.csv_file, args.output)
        checker.process(start_line=args.start, end_line=args.end)

    elif args.command == "analyze":
        from complete_analyzer import CompleteAnalyzer

        print(f"\n{'=' * 80}")
        print("📊 COMPLETE ANALYZER (Link Check + Content Analysis)")
        print(f"{'=' * 80}\n")
        analyzer = CompleteAnalyzer(
            args.csv_file, args.output, ollama_url=args.ollama_url, model=args.model
        )
        analyzer.process(start_line=args.start, end_line=args.end)

    elif args.command == "validate":
        import subprocess

        print(f"\n{'=' * 80}")
        print("✅ VALIDATOR")
        print(f"{'=' * 80}\n")
        subprocess.run([sys.executable, "complete_validator.py", args.csv_file])


if __name__ == "__main__":
    main()
