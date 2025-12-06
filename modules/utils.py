
import json
import re

def clean_json_text(text: str) -> str:
    """
    Cleans text to ensure it is valid JSON.
    Removes Markdown code blocks (```json ... ```).
    """
    # Remove markdown code fences
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text)
    
    # Strip whitespace
    text = text.strip()
    
    return text

def parse_llm_json(text: str):
    """
    Attempts to parse JSON from LLM output.
    Returns (data, error_message).
    """
    cleaned = clean_json_text(text)
    try:
        data = json.loads(cleaned)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON Parsing Error: {e} | Content: {text[:100]}..."
