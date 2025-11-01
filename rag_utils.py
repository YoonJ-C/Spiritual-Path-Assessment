"""Simple RAG utilities for loading religion data"""
import csv

def load_religions_from_csv(csv_path):
    """Load religion data from CSV file"""
    try:
        religions = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                religions[row['religion']] = row
        print(f"✅ Loaded {len(religions)} religions from CSV")
        return religions
    except Exception as e:
        print(f"⚠️ Error loading religions CSV: {e}")
        return {}

def prepare_religion_rag_context(religion_data):
    """Prepare context string from religion data"""
    parts = []
    
    if 'description' in religion_data:
        parts.append(f"Description: {religion_data['description']}")
    if 'practices' in religion_data:
        parts.append(f"Practices: {religion_data['practices']}")
    if 'core_beliefs' in religion_data:
        parts.append(f"Core Beliefs: {religion_data['core_beliefs']}")
    if 'common_curiosities' in religion_data:
        parts.append(f"Common Questions: {religion_data['common_curiosities']}")
    
    return ['\n\n'.join(parts)]
