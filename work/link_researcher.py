#!/usr/bin/env python3
"""
Link Researcher - Validates links and evaluates CSV content
Acts as the research agent that checks each tool's information
"""

import time
from typing import Dict, List
from utils import URLValidator, ContentFetcher, LinkFinder


class LinkResearcher:
    def __init__(self, timeout=10, delay=1):
        """
        Initialize the researcher

        Args:
            timeout: Seconds to wait for each request
            delay: Seconds to wait between requests to avoid rate limiting
        """
        self.validator = URLValidator(timeout=timeout)
        self.fetcher = ContentFetcher(timeout=timeout)
        self.link_finder = LinkFinder()
        self.delay = delay

    def research_and_validate(self, row: Dict, line_num: int) -> Dict:
        """
        Research and validate a single CSV row

        Args:
            row: Dictionary containing CSV row data
            line_num: Line number for reference

        Returns:
            Dictionary with keys: 'row', 'changed', 'summary', 'details'
        """
        tool_name = row["Tool Name"]
        changes_made = []
        details = []
        original_row = row.copy()

        # Define the fields to check
        fields = [
            "Homepage",
            "Privacy/Legal Link",
            "DSGVO/GDPR Link",
            "Storage/Hosting Link",
            "DPA/AVV Link",
        ]

        print(f"  🔍 Researching: {tool_name}")

        # Step 1: Validate homepage
        homepage = row["Homepage"]
        print(f"    🏠 Checking homepage: {homepage}")

        homepage_valid, homepage_status = self.validator.validate_url(homepage)

        if not homepage_valid:
            print(f"    ❌ Homepage invalid (Status: {homepage_status})")
            details.append(f"Homepage invalid: {homepage_status}")
            # Try to find a working alternative
            alt_homepage = self._find_alternative_homepage(tool_name)
            if alt_homepage:
                row["Homepage"] = alt_homepage
                homepage = alt_homepage
                changes_made.append(f"Updated homepage to {alt_homepage}")
                print(f"    ✅ Found alternative: {alt_homepage}")
            else:
                details.append("Could not find alternative homepage")
                print(f"    ⚠️  No alternative found")
        else:
            print(f"    ✅ Homepage valid (Status: {homepage_status})")
            details.append(f"Homepage valid: {homepage_status}")

        time.sleep(self.delay)

        # Step 2: Fetch homepage content for link discovery
        print(f"    📄 Fetching homepage content...")
        homepage_content = self.fetcher.fetch_content(homepage)

        if homepage_content:
            print(f"    ✅ Content fetched ({len(homepage_content)} chars)")
            # Extract all links from homepage
            found_links = self.link_finder.extract_links(homepage_content, homepage)
            print(f"    🔗 Found {len(found_links)} links on homepage")
        else:
            print(f"    ❌ Could not fetch homepage content")
            found_links = []
            details.append("Could not fetch homepage content")

        time.sleep(self.delay)

        # Step 3: Validate and fix other links
        for field in fields[1:]:  # Skip Homepage as we already checked it
            current_url = row[field]
            print(f"    🔗 Checking {field}: {current_url}")

            is_valid, status = self.validator.validate_url(current_url)

            if not is_valid:
                print(f"      ❌ Invalid (Status: {status})")
                details.append(f"{field} invalid: {status}")

                # Try to find a replacement from the homepage links
                replacement = self._find_replacement_link(
                    field, current_url, found_links, homepage
                )

                if replacement and replacement != current_url:
                    row[field] = replacement
                    changes_made.append(f"Updated {field} to {replacement}")
                    print(f"      ✅ Found replacement: {replacement}")
                else:
                    details.append(f"Could not find replacement for {field}")
                    print(f"      ⚠️  No replacement found")
            else:
                print(f"      ✅ Valid (Status: {status})")
                details.append(f"{field} valid: {status}")

            time.sleep(self.delay)

        # Step 4: Create summary
        changed = len(changes_made) > 0
        if changed:
            summary = f"Updated {len(changes_made)} field(s): " + "; ".join(
                changes_made
            )
        else:
            summary = "All links valid, no changes needed"

        return {
            "row": row,
            "changed": changed,
            "summary": summary,
            "details": details,
            "original": original_row,
        }

    def _find_alternative_homepage(self, tool_name: str) -> str:
        """
        Try to find an alternative homepage using search patterns

        Args:
            tool_name: Name of the tool

        Returns:
            Alternative URL or empty string
        """
        # Common patterns for AI tool homepages
        patterns = [
            f"https://www.{tool_name.lower().replace(' ', '')}.com",
            f"https://{tool_name.lower().replace(' ', '')}.ai",
            f"https://{tool_name.lower().replace(' ', '')}.io",
            f"https://www.{tool_name.lower().replace(' ', '')}.ai",
        ]

        for pattern in patterns:
            is_valid, _ = self.validator.validate_url(pattern)
            if is_valid:
                return pattern

        return ""

    def _find_replacement_link(
        self, field_name: str, current_url: str, found_links: List[str], base_url: str
    ) -> str:
        """
        Find a replacement link from the discovered links

        Args:
            field_name: Name of the field (e.g., 'Privacy/Legal Link')
            current_url: Current URL in the field
            found_links: List of links found on the homepage
            base_url: Base URL of the homepage

        Returns:
            Replacement URL or current URL if no better option found
        """
        # Define keywords for each field type
        keywords_map = {
            "Privacy/Legal Link": ["privacy", "legal", "policy"],
            "DSGVO/GDPR Link": ["gdpr", "dsgvo", "privacy", "data-protection"],
            "Storage/Hosting Link": [
                "security",
                "trust",
                "infrastructure",
                "hosting",
                "storage",
            ],
            "DPA/AVV Link": ["dpa", "avv", "data-processing", "addendum", "dpa"],
        }

        keywords = keywords_map.get(field_name, [])

        # Score each found link
        best_match = None
        best_score = 0

        for link in found_links:
            score = 0
            link_lower = link.lower()

            # Check for keywords
            for keyword in keywords:
                if keyword in link_lower:
                    score += 10

            # Prefer links from the same domain
            if base_url.split("/")[2] in link:
                score += 5

            # Validate the link
            is_valid, status = self.validator.validate_url(link)
            if is_valid:
                score += 20
            else:
                score = 0  # Invalid links get 0 score

            if score > best_score:
                best_score = score
                best_match = link

        # Only return if we found a decent match
        if best_score >= 20:  # At least valid
            return best_match

        return current_url
