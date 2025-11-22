import random
import sys
from dnd_loader import DndCharacter

# ==========================================
# 1. ROSTER CONFIGURATION
# ==========================================
ROSTER_URLS = {
    # Replace with your actual URLs
    "Shant": "https://www.dndbeyond.com/characters/117122592",
    "Arima": "https://www.dndbeyond.com/characters/27107475",
    "Grog": "https://www.dndbeyond.com/characters/75991828",
}

# ==========================================
# 2. CALCULATION LOGIC & DESCRIPTIVE EFFECTS
# ==========================================
# Placeholders: {s} = Speaker Name, {l} = Listener Name
effects = [
    {
        "min": -100, "max": -7, 
        "intimidation": "{l} is deeply offended by {s}'s aggression and immediately becomes hostile or mocks the attempt.",
        "performance": "{l} finds {s} utterly obnoxious and actively tries to leave the conversation.",
        "deception": "{l} sees right through {s}, convinced they are lying maliciously.",
        "persuasion": "{l} completely misinterprets {s}'s logic, taking the suggestion as an insult."
    },
    {
        "min": -6, "max": -5, 
        "intimidation": "{l} feels disrespected by {s} and digs their heels in, refusing to cooperate.",
        "performance": "{l} is unimpressed and dismissive of {s}'s antics.",
        "deception": "{l} distrusts {s} and is suspicious of their motives.",
        "persuasion": "{l} simply doesn't understand {s}'s point and gets frustrated."
    },
    {
        "min": -4, "max": -2, 
        "intimidation": "{l} feels {s} is posturing but isn't truly afraid, leading to an awkward standoff.",
        "performance": "{l} avoids making eye contact, finding {s}'s behavior slightly cringe-worthy.",
        "deception": "{l} senses {s} is withholding information and becomes guarded.",
        "persuasion": "{l} is confused by the details and remains unconvinced by {s}."
    },
    {
        "min": -1, "max": 0, 
        "intimidation": "{l} sees {s} as an equal; they are not scared, but they are listening.",
        "performance": "{l} is indifferent to {s}, neither entertained nor annoyed.",
        "deception": "{l} is neutral, neither believing nor disbelieving {s} fully.",
        "persuasion": "{l} understands the surface level of {s}'s request but needs more convincing."
    },
    {
        "min": 1, "max": 2, 
        "intimidation": "{l} respects {s}'s strength and feels compelled to listen.",
        "performance": "{l} is drawn in by {s}'s charisma and pays close attention.",
        "deception": "{s}'s story seems plausible enough to {l}.",
        "persuasion": "{l} feels enlightened by {s}'s argument and is inclined to agree."
    },
    {
        "min": 3, "max": 5, 
        "intimidation": "{l} is thoroughly cowed by {s} and feels a strong urge to submit to the demand.",
        "performance": "{l} is captivated, actively seeking {s}'s approval or company.",
        "deception": "{l} trusts {s} implicitely, swallowing the lie whole.",
        "persuasion": "{l} fully understands and empathizes with {s}'s intent."
    },
    {
        "min": 6, "max": 100, 
        "intimidation": "{l} is terrified or awestruck, viewing {s} as a dominant force of nature.",
        "performance": "{l} becomes an instant fan, hanging on {s}'s every word.",
        "deception": "{l} believes {s} completely, perhaps even defending the lie to others.",
        "persuasion": "{l} experiences a shift in perspective, expanding their understanding to align with {s}."
    },
]

def get_effect_row(value):
    for effect in effects:
        if effect["min"] <= value <= effect["max"]:
            return effect
    # Fallback
    return {k: "Result inconclusive." for k in ["intimidation", "performance", "deception", "persuasion"]}

def calculate_outcomes(speaker, listener):
    # Rolls
    d20_int = random.randint(1, 20)
    d20_perf = random.randint(1, 20)
    d20_dec = random.randint(1, 20)
    d20_pers = random.randint(1, 20)
    
    # Listener Resistance (Insight Check)
    npc_d20_insight = random.randint(1, 20) 
    
    # Stats
    s_int = speaker.skills['Intimidation'].total
    s_perf = speaker.skills['Performance'].total
    s_dec = speaker.skills['Deception'].total
    s_pers = speaker.skills['Persuasion'].total
    l_insight = listener.skills['Insight'].total

    # Math
    val_int = (s_int + d20_int) - (npc_d20_insight + l_insight)
    val_perf = (s_perf + d20_perf) - (npc_d20_insight + l_insight)
    val_dec = (s_dec + d20_dec) - (npc_d20_insight + l_insight)
    val_pers = (s_pers + d20_pers) + (npc_d20_insight + l_insight)

    # Helper to format strings with names
    def fmt(text):
        return text.format(s=speaker.name, l=listener.name)

    row_int = get_effect_row(val_int)
    row_perf = get_effect_row(val_perf)
    row_dec = get_effect_row(val_dec)
    row_pers = get_effect_row(val_pers)

    return {
        "raw_scores": {
            "int": val_int, "perf": val_perf, "dec": val_dec, "pers": val_pers
        },
        "results": {
            "Intimidation": fmt(row_int['intimidation']),
            "Performance": fmt(row_perf['performance']),
            "Deception": fmt(row_dec['deception']),
            "Persuasion": fmt(row_pers['persuasion'])
        }
    }

# ==========================================
# 3. INTERACTIVE TOOLS
# ==========================================
def select_character(prompt_text, char_list):
    print(f"\n--- {prompt_text} ---")
    keys = list(char_list.keys())
    for i, name in enumerate(keys):
        print(f"{i + 1}. {name}")
    
    while True:
        try:
            choice = int(input("Select Number: ")) - 1
            if 0 <= choice < len(keys):
                return char_list[keys[choice]]
            print("Invalid number.")
        except ValueError:
            print("Please enter a number.")

def generate_prompt(speaker, listener, dialogue, likelihood, outcomes):
    results = outcomes['results']
    scores = outcomes['raw_scores']
    
    print("\n" + "#"*30 + " COPY FOR GEMINI " + "#"*30 + "\n")
    
    prompt = f"""
I am writing a D&D story. I need you to write the response of an NPC based on a player's dialogue, the specific context of the request, and a full set of mechanical social dice rolls.

**SCENE SETUP:**
*   **Speaker:** {speaker.name}
*   **Listener:** {listener.name}
*   **Context/Difficulty:** The user has stated that for the listener to agree to this specific request, it is: "{likelihood}".

**CHARACTER TRAITS:**
*   **{speaker.name}:** {speaker.traits} | Ideals: {speaker.ideals} | Flaws: {speaker.flaws} | Appearance: {speaker.appearance}
*   **{listener.name}:** {listener.traits} | Ideals: {listener.ideals} | Flaws: {listener.flaws} | Appearance: {listener.appearance}

**THE INPUT:**
{speaker.name} says:
> "{dialogue}"

**THE MECHANICS (Social Vectors):**
I have simulated the dice rolls for all possible social approaches. Please analyze the *tone* of the dialogue above to decide which skill was used, and then apply the specific result below.

1.  **Intimidation (Score {scores['int']}):** {results['Intimidation']}
2.  **Performance (Score {scores['perf']}):** {results['Performance']}
3.  **Deception (Score {scores['dec']}):** {results['Deception']}
4.  **Persuasion (Score {scores['pers']}):** {results['Persuasion']}

**TASK:**
Write the narrative response. 
1.  Determine which of the 4 approaches best matches the specific words chosen in the dialogue.
2.  Take the result of that approach (and the "Context/Difficulty") to determine the success or failure.
3.  Describe {listener.name}'s internal thought process filtering the words through their Personality Traits.
4.  Write {listener.name}'s spoken or physical response.
    """
    print(prompt.strip())
    print("\n" + "#"*30 + " END COPY " + "#"*30 + "\n")

# ==========================================
# 4. MAIN LOOP
# ==========================================
def main():
    print("Initializing Social Session...")
    loaded_chars = {}
    
    # Load characters
    for name, url in ROSTER_URLS.items():
        try:
            print(f"Loading {name}...")
            loaded_chars[name] = DndCharacter(url)
        except Exception as e:
            print(f"Failed to load {name}: {e}")

    if len(loaded_chars) < 2:
        print("Error: Need at least 2 loaded characters to interact.")
        return

    while True:
        print("\n" + "="*40)
        print("NEW INTERACTION")
        print("="*40)
        
        # 1. Select Speaker
        speaker = select_character("Select the SPEAKER", loaded_chars)
        
        # 2. Select Listener
        others = {k:v for k,v in loaded_chars.items() if v != speaker}
        listener = select_character("Select the LISTENER", others)
        
        # 3. Enter Dialogue
        print(f"\nWhat does {speaker.name} say to {listener.name}?")
        dialogue = input("> ")

        # 4. Enter Likelihood / Context
        print(f"\nHow likely is {listener.name} to do what is asked?")
        print("(Examples: 'Impossible', 'Very Unlikely', 'Standard', 'Eager', 'Already agrees')")
        likelihood = input("> ")
        
        # 5. Process
        print("Calculating social vectors...")
        outcomes = calculate_outcomes(speaker, listener)
        
        # 6. Output
        generate_prompt(speaker, listener, dialogue, likelihood, outcomes)
        
        # 7. Continue?
        cont = input("Run another interaction? (y/n): ")
        if cont.lower() != 'y':
            break

if __name__ == "__main__":
    main()