#!/usr/bin/env python3
import webbrowser
import csv
import time

# Path to your CSV file
csv_file = "/Users/gerritbrinkhaus/Library/Mobile Documents/com~apple~CloudDocs/Documents/Coaching/Artikel/work/DISCOVERY_LINKS_50_TOOLS.csv"

# Read the CSV and extract homepage URLs
urls = []
with open(csv_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter=";")
    for row in reader:
        if row["Homepage"]:
            urls.append(row["Homepage"])

# Open each URL in the default browser
print(f"Opening {len(urls)} homepages...")
for i, url in enumerate(urls, 1):
    print(f"[{i}/{len(urls)}] Opening: {url}")
    webbrowser.open(url)
    time.sleep(0.5)  # Small delay to avoid overwhelming the browser

print("Done!")
