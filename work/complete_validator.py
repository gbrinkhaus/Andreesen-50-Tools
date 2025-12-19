#!/usr/bin/env python3
"""
AI Tools Complete Validator
Processes Andreesen Tools 50 CSV and creates comprehensive validation report.

For each tool generates 3 rows:
1. Original data (unchanged)
2. Link validation results (HTTP status)
3. Content analysis results (Ollama AI analysis)
"""

import csv
import os
import sys
import time
import requests
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import subprocess
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
INPUT_FILE = "Andreesen Tools 50 - UPDATED.csv"
OUTPUT_FILE = "Andreesen Tools 50 - COMPLETE.csv"
OLLAMA_MODEL = "gpt-oss:20b"
OLLAMA_TIMEOUT = 30
REQUEST_TIMEOUT = 10
RATE_LIMIT_DELAY = 0.5  # seconds between requests

# Headers to use for HTTP requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# Link type mapping
LINK_TYPES = {
    "Homepage": "Is this the company homepage?",
    "Privacy/Legal Link": "Does the page contain a privacy policy or legal information?",
    "DSGVO/GDPR Link": "Does the page mention GDPR compliance or data protection?",
    "Storage/Hosting Link": "Does the page describe data storage, infrastructure, or server locations?",
    "DPA/AVV Link": "Does the page contain a Data Processing Agreement or processing instructions?",
}


class LinkValidator:
    """Validates links and fetches their content."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def validate_url(self, url: str) -> Tuple[int, Optional[str]]:
        """
        Validate URL and return status code and content.

        Returns:
            Tuple of (status_code, content) or (None, None) on error
        """
        if not url or not url.strip():
            return (None, None)

        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            response = self.session.get(
                url, timeout=REQUEST_TIMEOUT, allow_redirects=True
            )
            # Return content only for successful responses
            if response.status_code == 200:
                return (response.status_code, response.text)
            else:
                return (response.status_code, None)
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout for {url}")
            return (None, None)
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error for {url}")
            return (None, None)
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            return (None, None)

    def format_status(self, status_code: Optional[int]) -> str:
        """Format HTTP status for output."""
        if status_code is None:
            return "❌ Not accessible"
        elif status_code == 200:
            return "✅ Valid (HTTP 200)"
        elif status_code == 403:
            return "✅ Valid (HTTP 403 - blocked)"
        elif status_code == 404:
            return "❌ Not found (HTTP 404)"
        elif 200 <= status_code < 300:
            return f"✅ Valid (HTTP {status_code})"
        elif 300 <= status_code < 400:
            return f"⚠️ Redirect (HTTP {status_code})"
        elif 400 <= status_code < 500:
            return f"❌ Client error (HTTP {status_code})"
        else:
            return f"❌ Server error (HTTP {status_code})"


class OllamaAnalyzer:
    """Analyzes content using Ollama."""

    @staticmethod
    def check_ollama_available() -> bool:
        """Check if Ollama is running and model is available."""
        try:
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=5
            )
            if OLLAMA_MODEL in result.stdout:
                logger.info(f"✓ Ollama model '{OLLAMA_MODEL}' found")
                return True
            else:
                logger.error(f"Ollama model '{OLLAMA_MODEL}' not found")
                return False
        except Exception as e:
            logger.error(f"Ollama not available: {e}")
            return False

    @staticmethod
    def analyze_content(content: str, link_type: str, question: str) -> str:
        """
        Use Ollama to analyze if content matches the link type.

        Returns:
            "Yes" or "No" based on analysis
        """
        if not content or not content.strip():
            return "No"

        # Truncate content to avoid token limits
        content_preview = content[:3000]

        prompt = f"""You are analyzing website content to determine if it contains specific information.

Link Type: {link_type}
Question: {question}

Website Content (preview):
{content_preview}

---

Answer ONLY with "Yes" or "No". No explanation.

Is the answer to the question "Yes" based on this content?"""

        try:
            result = subprocess.run(
                ["ollama", "run", OLLAMA_MODEL],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=OLLAMA_TIMEOUT,
            )

            response = result.stdout.strip().lower()
            if "yes" in response:
                return "Yes"
            elif "no" in response:
                return "No"
            else:
                logger.warning(f"Unexpected Ollama response: {response}")
                return "No"

        except subprocess.TimeoutExpired:
            logger.warning("Ollama analysis timed out")
            return "No"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return "No"


class CSVProcessor:
    """Processes the CSV file and generates output."""

    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.validator = LinkValidator()
        self.analyzer = OllamaAnalyzer()
        self.link_columns = [
            "Homepage",
            "Privacy/Legal Link",
            "DSGVO/GDPR Link",
            "Storage/Hosting Link",
            "DPA/AVV Link",
        ]
        self.ollama_available = False

    def read_csv(self) -> Tuple[List[str], List[List[str]]]:
        """Read input CSV file."""
        with open(self.input_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            headers = next(reader)  # Skip empty row
            headers = next(reader)  # Get actual headers
            rows = list(reader)
        return headers, rows

    def process_tool(self, headers: List[str], row: List[str]) -> List[List[str]]:
        """
        Process single tool and return 3 rows (original, validation, analysis).
        """
        output_rows = []

        # Row 1: Original data
        output_rows.append(row)

        # Row 2: Link validation
        validation_row = row.copy()
        app_name_idx = headers.index("App name")
        validation_row[app_name_idx] = "[LINK CHECK]"

        # Get link column indices and validate
        for link_type in self.link_columns:
            try:
                col_idx = headers.index(link_type)
                url = row[col_idx] if col_idx < len(row) else ""
                status_code, _ = self.validator.validate_url(url)
                validation_row[col_idx] = self.validator.format_status(status_code)
                time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
            except Exception as e:
                logger.warning(f"Error validating {link_type}: {e}")

        output_rows.append(validation_row)

        # Row 3: Content analysis (only if Ollama available)
        if self.ollama_available:
            analysis_row = row.copy()
            analysis_row[app_name_idx] = "[CONTENT ANALYSIS]"

            for link_type in self.link_columns:
                try:
                    col_idx = headers.index(link_type)
                    url = row[col_idx] if col_idx < len(row) else ""
                    _, content = self.validator.validate_url(url)

                    if content:
                        question = LINK_TYPES.get(link_type, "")
                        result = self.analyzer.analyze_content(
                            content, link_type, question
                        )
                        analysis_row[col_idx] = result
                    else:
                        analysis_row[col_idx] = "N/A"
                except Exception as e:
                    logger.warning(f"Error analyzing {link_type}: {e}")
                    analysis_row[col_idx] = "Error"

            output_rows.append(analysis_row)

        return output_rows

    def write_csv(self, headers: List[str], all_rows: List[List[str]]):
        """Write output CSV file."""
        with open(self.output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([""] * len(headers))  # Empty header row
            writer.writerow(headers)
            writer.writerows(all_rows)
        logger.info(f"✓ Output written to {self.output_file}")

    def process(self):
        """Main processing pipeline."""
        logger.info(f"Reading {self.input_file}...")
        headers, rows = self.read_csv()

        # Check Ollama availability
        self.ollama_available = self.analyzer.check_ollama_available()
        if not self.ollama_available:
            logger.warning("Ollama not available - skipping content analysis")

        logger.info(f"Processing {len(rows)} tools...")
        all_output_rows = []

        for idx, row in enumerate(rows, 1):
            app_name = (
                row[headers.index("App name")]
                if "App name" in headers
                else f"Tool {idx}"
            )
            logger.info(f"  [{idx}/{len(rows)}] Processing {app_name}...")

            tool_rows = self.process_tool(headers, row)
            all_output_rows.extend(tool_rows)

        logger.info("Writing output file...")
        self.write_csv(headers, all_output_rows)
        logger.info("✓ Complete!")


def main():
    """Main entry point."""
    try:
        if not os.path.exists(INPUT_FILE):
            logger.error(f"Input file not found: {INPUT_FILE}")
            sys.exit(1)

        processor = CSVProcessor(INPUT_FILE, OUTPUT_FILE)
        processor.process()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
