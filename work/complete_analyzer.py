#!/usr/bin/env python3
"""
Complete Analyzer - Creates ONE CSV with 3 rows per tool:
1. Original data
2. Link validation results
3. Content analysis results
"""

import csv
from pathlib import Path
from typing import Tuple
import requests
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import warnings

warnings.filterwarnings("ignore")


class CompleteAnalyzer:
    def __init__(
        self,
        csv_path: str,
        output_path: str = None,
        ollama_url: str = "http://localhost:11434",
        model: str = "gpt-oss:20b",
    ):
        """
        Initialize analyzer

        Args:
            csv_path: Path to CSV file
            output_path: Path for output CSV (if None, creates _COMPLETE.csv)
            ollama_url: Ollama service URL
            model: Model to use
        """
        self.csv_path = Path(csv_path)
        self.output_path = (
            Path(output_path)
            if output_path
            else Path("work/output") / f"{self.csv_path.stem}_COMPLETE.csv"
        )
        self.ollama_url = ollama_url
        self.model = model

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        self.link_columns = [
            "Homepage",
            "Privacy/Legal Link",
            "DSGVO/GDPR Link",
            "Storage/Hosting Link",
            "DPA/AVV Link",
        ]

        # Setup Selenium Chrome driver
        self.driver = None
        self._init_driver()

        self._verify_ollama()

    def _init_driver(self):
        """Initialize undetected Chrome driver to bypass Cloudflare"""
        try:
            self.driver = uc.Chrome(version_main=None, suppress_welcome=True)
            print("✅ Undetected Chrome driver initialized")
        except Exception as e:
            print(f"⚠️  Driver init failed: {e}")

    def _verify_ollama(self):
        """Verify Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama connected (model: {})".format(self.model))
                return True
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return False

    def check_link(self, url: str) -> str:
        """Check if link is valid using browser"""
        if not url or not url.strip():
            return "⚠️ Empty"

        try:
            # Try with browser first (handles Cloudflare)
            if self.driver:
                try:
                    self.driver.get(url)
                    time.sleep(1)

                    # Check if we got a real page
                    page_source = self.driver.page_source
                    if page_source and len(page_source) > 500:
                        return "✅ Valid (page loaded)"
                except:
                    pass

            # Fallback to HTTP HEAD
            response = self.session.head(url, timeout=10, allow_redirects=True)

            if 200 <= response.status_code < 300:
                return "✅ Valid (HTTP {})".format(response.status_code)
            elif response.status_code == 403:
                return "✅ Valid (HTTP 403 - blocked)"
            elif response.status_code == 429:
                return "✅ Valid (rate limited)"
            elif 300 <= response.status_code < 400:
                return "✅ Valid (redirect {})".format(response.status_code)
            elif response.status_code == 404:
                return "❌ Not found (HTTP 404)"
            elif response.status_code == 410:
                return "❌ Gone (HTTP 410)"
            elif response.status_code >= 500:
                return "⚠️ Server error (HTTP {})".format(response.status_code)
            else:
                return "❌ Error (HTTP {})".format(response.status_code)

        except requests.exceptions.Timeout:
            return "❌ Timeout"
        except requests.exceptions.ConnectionError:
            return "❌ No connection"
        except Exception as e:
            return "❌ Error: {}".format(str(e)[:15])

    def fetch_content(self, url: str) -> str:
        """Fetch page content using undetected Chrome (bypasses Cloudflare)"""
        if not self.driver:
            return ""

        try:
            self.driver.get(url)
            # Wait for page to load
            time.sleep(3)

            # Get page source
            page_source = self.driver.page_source

            if page_source and len(page_source) > 100:
                soup = BeautifulSoup(page_source, "html.parser")

                # Remove script and style tags
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                text = " ".join(chunk for chunk in chunks if chunk)

                if text and len(text) > 50:
                    return text[:5000]  # First 5000 chars of actual content
        except:
            pass
        return ""

    def analyze_with_ollama(self, link_type: str, content: str) -> str:
        """Use Ollama to analyze if content matches link type"""
        if not content:
            return "❌ No content"

        prompts = {
            "Homepage": "Is this the main website homepage?",
            "Privacy/Legal Link": "Does this contain privacy policy or legal terms?",
            "DSGVO/GDPR Link": "Does this mention GDPR, DSGVO, or EU data protection?",
            "Storage/Hosting Link": "Does this describe data storage, hosting, or security?",
            "DPA/AVV Link": "Does this contain a Data Processing Agreement or DPA?",
        }

        chunk_size = 4000
        chunks = [
            content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
        ]
        any_yes = False
        for idx, chunk in enumerate(chunks):
            prompt = f"""Analyze: {prompts.get(link_type, "What is this?")}

CONTENT:
{chunk}

Answer ONLY with: YES or NO (one word)."""
            print(
                f"\n--- OLLAMA PROMPT for {link_type} (chunk {idx + 1}/{len(chunks)}) ---\nQUESTION: {prompts.get(link_type, 'What is this?')}\n--- END PROMPT ---\n"
            )
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.1,
                    },
                    timeout=60,
                )
                if response.status_code == 200:
                    result = response.json().get("response", "").strip().upper()
                    if "YES" in result:
                        any_yes = True
                        break
                else:
                    print(f"❌ Ollama error: {response.status_code}")
            except Exception as e:
                print(f"❌ Ollama error: {e}")
        if any_yes:
            return "✅ Yes"
        else:
            return "❌ No"

        print(
            f"\n--- OLLAMA PROMPT for {link_type} ---\nQUESTION: {prompts.get(link_type, 'What is this?')}\n--- END PROMPT ---\n"
        )

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json().get("response", "").strip().upper()

                # Format with consistent icons
                if "YES" in result:
                    return f"✅ Yes"
                elif "NO" in result:
                    return f"❌ No"
                else:
                    return f"⚠️ Unclear: {result[:30]}"
        except requests.exceptions.Timeout:
            return "⚠️ Timeout"
        except Exception as e:
            return f"⚠️ Error"

        return "⚠️ No response"

    def process(self, start_line: int = 1, end_line: int = None):
        """
        Process CSV: creates 3 rows per tool
        """
        # Read CSV
        print("📂 Reading CSV...")
        rows = []
        fieldnames = []

        with open(self.csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "App name" in line or "Kategorie" in line:
                    f_temp = open(self.csv_path, "r", encoding="utf-8")
                    reader = csv.DictReader(f_temp.readlines()[i:], delimiter=";")
                    fieldnames = reader.fieldnames or []
                    rows = list(reader)
                    f_temp.close()
                    break

        print(f"✅ Loaded {len(rows)} rows")

        # Determine range
        total = len(rows)
        end_line = end_line if end_line else total
        start_idx = start_line - 1
        end_idx = min(end_line, total)

        print(f"\n{'=' * 80}")
        print(f"🔍 CREATING COMPLETE ANALYSIS (lines {start_line} to {end_idx})")
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

            # Add original row
            output_rows.append(original_row)

            # Create link check row
            link_check_row = {key: "" for key in fieldnames}
            link_check_row["App name"] = "[LINK CHECK]"

            for link_col in self.link_columns:
                if link_col not in fieldnames:
                    continue

                url = original_row.get(link_col, "").strip()
                result = self.check_link(url)
                link_check_row[link_col] = result
                print(f"  {result} {link_col}")

                time.sleep(0.3)

            output_rows.append(link_check_row)

            # Create content analysis row
            analysis_row = {key: "" for key in fieldnames}
            analysis_row["App name"] = "[CONTENT ANALYSIS]"

            for link_col in self.link_columns:
                if link_col not in fieldnames:
                    continue

                url = original_row.get(link_col, "").strip()

                if not url:
                    analysis_row[link_col] = "⚠️ No URL"
                else:
                    print(f"  🔍 Analyzing {link_col}...")
                    content = self.fetch_content(url)

                    if not content:
                        analysis_row[link_col] = "❌ No content"
                    else:
                        analysis = self.analyze_with_ollama(link_col, content)
                        analysis_row[link_col] = analysis
                        print(f"     {analysis}")

                time.sleep(1)

            output_rows.append(analysis_row)

            # Write results after each tool
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=fieldnames, delimiter=";", extrasaction="ignore"
                )
                writer.writeheader()
                writer.writerows(output_rows)

        # Add rows after processing range
        if end_idx < len(rows):
            output_rows.extend(rows[end_idx:])

        # Write output
        print(f"\n{'=' * 80}")
        print("💾 Writing output CSV...")

        # Ensure output directory exists before writing
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=fieldnames, delimiter=";", extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(output_rows)

        print(f"✅ Output: {self.output_path}")
        print(f"\nStructure per tool:")
        print(f"  Row 1: Original data")
        print(f"  Row 2: [LINK CHECK] - Link validation results")
        print(f"  Row 3: [CONTENT ANALYSIS] - Ollama analysis results")


def main():
    """Command line interface"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python complete_analyzer.py <csv_file> [start_line] [end_line]")
        print(
            "Example: python complete_analyzer.py 'Andreesen Tools 50 - UPDATED.csv' 1 2"
        )
        sys.exit(1)

    csv_file = sys.argv[1]
    start_line = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end_line = int(sys.argv[3]) if len(sys.argv) > 3 else None

    analyzer = CompleteAnalyzer(csv_file)
    try:
        analyzer.process(start_line=start_line, end_line=end_line)
    finally:
        if analyzer.driver:
            analyzer.driver.quit()


if __name__ == "__main__":
    main()
