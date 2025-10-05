import os
import json

def load_all_publications(data_folder='data'):
    """Load all JSON files from the data folder and extract key information"""
    publications = []
    
    for filename in os.listdir(data_folder):
        if filename.endswith('.json'):
            filepath = os.path.join(data_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract from BioC format
                    if isinstance(data, list) and len(data) > 0:
                        doc = data[0].get('documents', [{}])[0]
                        passages = doc.get('passages', [])
                        
                        title = ""
                        abstract = ""
                        full_text = ""
                        
                        for passage in passages:
                            section = passage.get('infons', {}).get('section_type', '')
                            text = passage.get('text', '')
                            
                            if section == 'TITLE':
                                title = text
                            elif section == 'ABSTRACT':
                                abstract = text
                            
                            full_text += text + " "
                        
                        if title:  # Only add if we found content
                            publications.append({
                                'id': doc.get('id', filename),
                                'title': title,
                                'abstract': abstract,
                                'content': full_text[:5000]  # Limit for AI context
                            })
                            
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return publications

def create_knowledge_base_text(publications):
    """Create a formatted text for AI context"""
    knowledge_text = "NASA Space Bioscience Publications Database:\n\n"
    
    for pub in publications:
        knowledge_text += f"Paper ID: {pub['id']}\n"
        knowledge_text += f"Title: {pub['title']}\n"
        knowledge_text += f"Abstract: {pub['abstract']}\n"
        knowledge_text += "-" * 80 + "\n\n"
    
    return knowledge_text