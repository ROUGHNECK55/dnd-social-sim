
import re
from typing import List, Set

def extract_proper_noun_candidates(text: str) -> Set[str]:
    """
    Extracts capitalized words that might be proper nouns.
    Very basic logic: Capitalized words not at start of sentence (imperfect).
    """
    # Simple regex for capitalized words. 
    # This is a naive implementation; for production, use spaCy.
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    return set(words)

def clean_text(text: str) -> str:
    return text.strip()

def find_known_entities(text: str, known_nodes: List[str]) -> List[str]:
    """
    Finds which of the known nodes appear in the text.
    Case-insensitive matching for better UX, returning the canonical Node Name.
    """
    found = []
    text_lower = text.lower()
    
    # Sort by length descending to match "Deep Gnome" before "Gnome"
    # (Simple greedy approach)
    sorted_nodes = sorted(known_nodes, key=len, reverse=True)
    
    for node in sorted_nodes:
        # Simple substring match (could be improved with tokenization boundaries)
        if node.lower() in text_lower:
            found.append(node)
            
    return found
