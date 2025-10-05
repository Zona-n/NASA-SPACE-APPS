import csv
import requests
import json
import time
import re

# Read the CSV file
papers_data = []

with open('publications.csv', 'r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # Skip header
    
    for row in csv_reader:
        title = row[0]
        link = row[1]
        
        # Extract PMC ID from link
        pmc_match = re.search(r'PMC(\d+)', link)
        if pmc_match:
            pmc_id = f"PMC{pmc_match.group(1)}"
            papers_data.append({
                'title': title,
                'pmc_id': pmc_id,
                'link': link
            })

print(f"Found {len(papers_data)} papers")

# Fetch detailed info for each paper
processed_papers = []

for i, paper in enumerate(papers_data):
    print(f"Processing {i+1}/{len(papers_data)}: {paper['pmc_id']}")
    
    try:
        url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{paper['pmc_id']}/unicode"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            doc = data[0]["documents"][0]
            passages = doc["passages"]
            
            # Extract info
            abstract = ""
            year = ""
            authors = []
            
            for passage in passages:
                section = passage["infons"].get("section_type", "")
                text = passage.get("text", "")
                
                if section == "ABSTRACT":
                    abstract = text[:500]  # Limit length
                
                # Get year from infons
                if not year and "year" in passage["infons"]:
                    year = passage["infons"]["year"]
                
                # Get authors
                for key, value in passage["infons"].items():
                    if key.startswith("name_"):
                        authors.append(value)
            
            # Extract keywords from title and abstract
            keywords = []
            title_lower = paper['title'].lower()
            abstract_lower = abstract.lower()
            
            # Common organisms
            if 'mice' in title_lower or 'mouse' in title_lower:
                keywords.append('mice')
            if 'rat' in title_lower or 'rats' in title_lower:
                keywords.append('rats')
            
            # Platforms
            if 'iss' in title_lower or 'international space station' in abstract_lower:
                keywords.append('iss')
            if 'shuttle' in title_lower:
                keywords.append('shuttle')
            
            # Tissue types
            if 'muscle' in title_lower or 'muscle' in abstract_lower:
                keywords.append('muscle')
            if 'bone' in title_lower or 'bone' in abstract_lower:
                keywords.append('bone')
            if 'cardiovascular' in title_lower or 'heart' in title_lower:
                keywords.append('cardiovascular')
            
            processed_papers.append({
                'id': paper['pmc_id'],
                'title': paper['title'],
                'year': year,
                'authors': ', '.join(authors[:3]) if authors else '',
                'abstract': abstract,
                'keywords': keywords,
                'organism': 'Mice' if 'mice' in keywords else '',
                'platform': 'ISS' if 'iss' in keywords else '',
                'duration': '',
                'citations': 0,
                'link': paper['link']
            })
            
        time.sleep(0.5)  # Be nice to the API
        
    except Exception as e:
        print(f"Error with {paper['pmc_id']}: {e}")
        # Add paper with just basic info
        processed_papers.append({
            'id': paper['pmc_id'],
            'title': paper['title'],
            'year': '',
            'authors': '',
            'abstract': '',
            'keywords': [],
            'organism': '',
            'platform': '',
            'duration': '',
            'citations': 0,
            'link': paper['link']
        })

# Save to JSON
with open('papers_data.json', 'w', encoding='utf-8') as f:
    json.dump(processed_papers, f, indent=2)

print(f"\nProcessed {len(processed_papers)} papers")
print("Saved to papers_data.json")