# AI Tools Validator

A Python-based system to validate and correct a CSV list of AI tools, checking link validity and compliance documentation.

## Overview

This system processes a CSV file containing AI tools and their associated links (homepage, privacy policy, GDPR info, storage details, and DPA). It validates each link, attempts to find replacements for broken links, and creates a detailed report of findings.

## Architecture

The system uses a multi-agent approach:

1. **Main Processor** (`main_processor.py`) - Orchestrator that reads the CSV line by line
2. **Link Researcher** (`link_researcher.py`) - Validates and researches each tool's information
3. **Results Logger** (`results_logger.py`) - Tracks all findings and changes
4. **Utils** (`utils.py`) - Shared utilities for URL validation and content fetching

## Features

- ✅ Validates all links in the CSV (homepage, privacy, GDPR, storage, DPA)
- 🔍 Fetches homepage content to find replacement links
- 🔄 Automatically replaces broken links when alternatives are found
- 📊 Creates validated CSV output with corrections
- 📋 Generates detailed logs (JSON and human-readable formats)
- 🎯 Supports batch processing (process specific line ranges)
- ⏱️ Rate limiting to avoid overwhelming servers
- 📝 One-sentence summary for each tool processed

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage (Process Entire File)

```bash
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv
```

### Process Specific Lines

Process only lines 1-10:
```bash
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 1 10
```

Process lines 11-20:
```bash
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 11 20
```

### Process Single Line

Process only line 5:
```bash
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 5 5
```

## Output Files

The system generates three types of output:

1. **Validated CSV** - `DISCOVERY_LINKS_50_TOOLS_VALIDATED.csv`
   - Contains the corrected data with fixed links

2. **JSON Log** - `validation_log_YYYYMMDD_HHMMSS.json`
   - Structured data of all findings and changes
   - Machine-readable format for further processing

3. **Text Log** - `validation_log_YYYYMMDD_HHMMSS.txt`
   - Human-readable report with detailed findings
   - Summary statistics and per-tool results

## How It Works

### Step-by-Step Process

For each tool in the CSV:

1. **Homepage Validation**
   - Checks if the homepage URL is accessible
   - If invalid, attempts to find alternative homepage

2. **Content Fetching**
   - Retrieves homepage HTML content
   - Extracts all links for potential replacements

3. **Link Validation**
   - Validates each field: Privacy/Legal, GDPR, Storage, DPA
   - Checks HTTP status codes (200 = valid)

4. **Intelligent Replacement**
   - For broken links, searches homepage for suitable replacements
   - Uses keyword matching (e.g., "privacy" for Privacy/Legal Link)
   - Validates replacement links before using them

5. **Logging**
   - Records all findings and changes
   - Creates summary: "All links valid" or "Updated X field(s)"

## Configuration

You can adjust settings in the code:

### In `link_researcher.py`:
```python
LinkResearcher(timeout=10, delay=1)
```
- `timeout`: Seconds to wait for each request (default: 10)
- `delay`: Seconds between requests to avoid rate limiting (default: 1)

### In `utils.py`:
```python
URLValidator(timeout=10)
ContentFetcher(timeout=10)
```
- Adjust timeout values for slower connections

## Example Output

### Console Output
```
🚀 Starting validation of DISCOVERY_LINKS_50_TOOLS.csv
📊 Processing lines 1 to 10
================================================================================

📍 Processing #1: OpenAI
================================================================================
  🔍 Researching: OpenAI
    🏠 Checking homepage: https://openai.com
    ✅ Homepage valid (Status: HTTP 200)
    📄 Fetching homepage content...
    ✅ Content fetched (125643 chars)
    🔗 Found 87 links on homepage
    🔗 Checking Privacy/Legal Link: https://openai.com/policies/privacy-policy/
      ✅ Valid (Status: HTTP 200)
    ...

✅ Completed #1: All links valid, no changes needed
```

### Log Summary
```
SUMMARY
--------------------------------------------------------------------------------
Start Time:        2025-12-19T10:30:00
End Time:          2025-12-19T10:35:00
Duration:          300.00 seconds
Total Processed:   50
Total Changed:     12
Total Unchanged:   38
```

## Batch Processing Strategy

For large lists, process in batches to monitor progress:

```bash
# Batch 1: Lines 1-10
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 1 10

# Batch 2: Lines 11-20
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 11 20

# Batch 3: Lines 21-30
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 21 30

# And so on...
```

## Troubleshooting

### Issue: "Connection Error" for many URLs
- Some websites block automated requests
- Try increasing the delay between requests
- Check your internet connection

### Issue: "Timeout" errors
- Increase the timeout value in the code
- Process in smaller batches
- Check if specific websites are slow

### Issue: Rate limiting (429 errors)
- Increase the delay parameter
- Process smaller batches with breaks in between

## CSV Format

The CSV must have these columns (semicolon-delimited):
- `Tool Name`
- `Homepage`
- `Privacy/Legal Link`
- `DSGVO/GDPR Link`
- `Storage/Hosting Link`
- `DPA/AVV Link`

## Advanced Usage

### Validate a Single Problematic Tool

If you know a specific tool has issues (e.g., line 15):
```bash
python main_processor.py DISCOVERY_LINKS_50_TOOLS.csv 15 15
```

### Process Only Changed Entries

After an initial run, you can manually identify which tools need re-checking and process only those lines.

## Dependencies

- **requests**: HTTP library for making web requests
- **beautifulsoup4**: HTML parsing and link extraction
- **lxml**: Fast XML/HTML parser

## License

This is a utility tool for data validation and correction.

## Notes

- The system respects rate limits with built-in delays
- Links are validated but not deeply analyzed for content
- Replacement links are chosen based on keyword matching
- Always review the logs before trusting automated changes
- Some sites may block automated access (403/429 errors)
