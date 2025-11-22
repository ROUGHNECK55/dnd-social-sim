import requests
import math
import re

class Attribute:
    def __init__(self, name, value, override=None):
        self.name = name
        self.base_value = value
        self.override = override
        
    @property
    def score(self):
        # Returns the override if it exists (e.g. Belt of Giant Strength), otherwise base
        if self.override:
            return self.override
        return self.base_value
    
    @property
    def modifier(self):
        return (self.score - 10) // 2

    def __repr__(self):
        return f"{self.name}: {self.score} ({self.modifier:+})"

class Skill:
    def __init__(self, name, ability_obj, proficiency_level=0, misc_bonus=0, pb=2):
        self.name = name
        self.ability = ability_obj
        self.proficiency_level = proficiency_level
        self.misc_bonus = misc_bonus
        self.pb = pb
        
    @property
    def total(self):
        prof_bonus = math.floor(self.pb * self.proficiency_level)
        return self.ability.modifier + prof_bonus + self.misc_bonus

    def __repr__(self):
        return f"{self.name:<15} {self.total:+2}"

class DndCharacter:
    ABILITY_MAP = {1:"Strength", 2:"Dexterity", 3:"Constitution", 4:"Intelligence", 5:"Wisdom", 6:"Charisma"}
    
    SKILL_ABILITY_MAP = {
        "Athletics": "Strength", "Acrobatics": "Dexterity", "Sleight of Hand": "Dexterity", "Stealth": "Dexterity",
        "Arcana": "Intelligence", "History": "Intelligence", "Investigation": "Intelligence", "Nature": "Intelligence",
        "Religion": "Intelligence", "Animal Handling": "Wisdom", "Insight": "Wisdom", "Medicine": "Wisdom",
        "Perception": "Wisdom", "Survival": "Wisdom", "Deception": "Charisma", "Intimidation": "Charisma",
        "Performance": "Charisma", "Persuasion": "Charisma"
    }

    def __init__(self, url):
        self.character_id = self._extract_id(url)
        self.json_data = self._fetch_data()
        
        # Basic Info
        self.name = self.json_data.get("name", "Unknown")
        self.level = sum(c.get("level", 0) for c in self.json_data.get("classes", []))
        self.proficiency_bonus = math.ceil(self.level / 4) + 1 if self.level > 0 else 2
        
        # Containers
        self.attributes = {}
        self.skills = {}
        
        # Roleplay / Description Fields
        self.background_name = ""
        self.background_desc = ""
        self.appearance = ""
        self.traits = ""
        self.ideals = ""
        self.bonds = ""
        self.flaws = ""
        self.notes = "" # General Backstory notes

        # Execution
        self._parse_attributes()
        self._parse_skills()
        self._parse_flavor() # <--- This is where we load the text descriptions

    def _extract_id(self, url):
        match = re.search(r'(\d+)', url.split('/')[-1])
        if not match: match = re.search(r'/characters/(\d+)', url)
        if match: return match.group(1)
        raise ValueError("Could not extract Character ID from URL.")

    def _fetch_data(self):
        api_url = f"https://character-service.dndbeyond.com/character/v5/character/{self.character_id}"
        print(f"Fetching data for ID: {self.character_id} ...")
        response = requests.get(api_url)
        if response.status_code != 200: raise ConnectionError("Failed to fetch data.")
        data = response.json()
        return data["data"] if "data" in data else data

    def _parse_attributes(self):
        stats_base = {s['id']: s['value'] for s in self.json_data.get('stats', [])}
        stats_bonus = {s['id']: s['value'] for s in self.json_data.get('bonusStats', [])}
        stats_override = {s['id']: s['value'] for s in self.json_data.get('overrideStats', [])}
        for char_stat_id, name in self.ABILITY_MAP.items():
            base = stats_base.get(char_stat_id, 10) or 10
            bonus = stats_bonus.get(char_stat_id, 0) or 0
            override = stats_override.get(char_stat_id, None)
            self.attributes[name] = Attribute(name, base + bonus, override)

    def _parse_skills(self):
        modifiers = self.json_data.get("modifiers", {})
        all_mods = []
        for source in modifiers.values(): all_mods.extend(source)
        skill_prof = {}
        for mod in all_mods:
            if mod.get("type") == "proficiency": skill_prof[mod.get("friendlySubtypeName")] = 1
            elif mod.get("type") == "expertise": skill_prof[mod.get("friendlySubtypeName")] = 2
        
        for skill_name, ability_name in self.SKILL_ABILITY_MAP.items():
            self.skills[skill_name] = Skill(skill_name, self.attributes[ability_name], skill_prof.get(skill_name, 0), 0, self.proficiency_bonus)

    def _parse_flavor(self):
        """
        Extracts narrative details from specific JSON paths in D&D Beyond data.
        """
        def clean_html(raw_html):
            if not raw_html: return "Not specified."
            cleanr = re.compile('<.*?>') # Regex to remove HTML tags
            text = re.sub(cleanr, '', raw_html)
            # Replace common HTML entities
            text = text.replace('&nbsp;', ' ').replace('&rsquo;', "'").replace('&quot;', '"')
            return text.strip()

        # 1. Personality Traits (Ideals, Bonds, Flaws)
        # Located in data['traits']
        traits_data = self.json_data.get("traits", {})
        self.traits = clean_html(traits_data.get("personalityTraits"))
        self.ideals = clean_html(traits_data.get("ideals"))
        self.bonds = clean_html(traits_data.get("bonds"))
        self.flaws = clean_html(traits_data.get("flaws"))

        # 2. Appearance & Backstory
        # Located in data['notes']
        notes_data = self.json_data.get("notes", {})
        self.appearance = clean_html(notes_data.get("appearance"))
        self.notes = clean_html(notes_data.get("backstory"))

        # If appearance text box is empty, try to construct it from physical traits
        if self.appearance == "Not specified.":
            eyes = self.json_data.get("eyes", "")
            hair = self.json_data.get("hair", "")
            skin = self.json_data.get("skin", "")
            height = self.json_data.get("height", "")
            weight = self.json_data.get("weight", "")
            
            details = []
            if eyes: details.append(f"Eyes: {eyes}")
            if hair: details.append(f"Hair: {hair}")
            if skin: details.append(f"Skin: {skin}")
            if height: details.append(f"Height: {height}")
            if weight: details.append(f"Weight: {weight} lbs")
            
            if details:
                self.appearance = ", ".join(details)

        # 3. Background
        # Located in data['background']['definition']['name']
        bg_obj = self.json_data.get("background", {})
        # Safety check if background is None or empty
        if bg_obj and "definition" in bg_obj and bg_obj["definition"]:
            self.background_name = bg_obj["definition"].get("name", "Unknown Background")
            self.background_desc = clean_html(bg_obj["definition"].get("description", ""))
        else:
             # Check for Custom Background
             if bg_obj and "customBackground" in bg_obj and bg_obj["customBackground"]:
                 self.background_name = bg_obj["customBackground"].get("name", "Custom Background")
                 self.background_desc = clean_html(bg_obj["customBackground"].get("description", ""))
             else:
                 self.background_name = "None"
                 self.background_desc = ""