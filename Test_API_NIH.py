import csv
import os
import requests
import json
from urllib.parse import urlparse

# configuration
INPUT_CSV = "publications.csv"   # your input CSV file
OUTPUT_DIR = "data/SB_publication"            # folder to save results
os.makedirs(OUTPUT_DIR, exist_ok=True)

# extrack PMC ID from URL
def extract_pmc_id(url):
    """
    Extracts the PMC ID from the URL.
    Example URL: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11353732/
    """
    try:
        parts = url.strip("/").split("/")  # remove trailing slash and split
        for part in reversed(parts):
            if part.startswith("PMC"):
                return part
        return None
    except Exception as e:
        print(f"Error extracting PMC ID from {url}: {e}")
        return None

# main loop
with open(INPUT_CSV, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        title = row.get("Title", "").strip().replace("/", "_").replace("\\", "_")
        url = row.get("Link", "").strip()  

        pmc_id = extract_pmc_id(url)
        if not pmc_id:
            print(f"⚠️ Skipping: Could not extract PMC ID from URL ({url})")
            continue

        api_url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmc_id}/unicode"
        print(f"Fetching {pmc_id} ...")

        try:
            response = requests.get(api_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                output_path = os.path.join(OUTPUT_DIR, f"{pmc_id}.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Saved: {output_path}")
            else:
                print(f"Error {response.status_code} for {pmc_id}")
        except Exception as e:
            print(f"Failed to process {pmc_id}: {e}")