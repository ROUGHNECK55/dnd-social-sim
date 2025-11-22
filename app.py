import streamlit as st
import random
import re
import google.generativeai as genai
from dnd_loader import DndCharacter

# ==========================================
# 1. CONFIGURATION & LIMITS
# ==========================================
st.set_page_config(page_title="D&D Social Sim", layout="wide", page_icon="🎲")

# Limit to prevent server abuse/memory overflow
MAX_CHARS = 8 

# Regex to validate URL before attempting fetch
URL_PATTERN = r"dndbeyond\.com/characters/\d+"

# ==========================================
# 2. SESSION STATE MANAGEMENT
# ==========================================
if 'roster' not in st.session_state:
    st.session_state['roster'] = {} # Stores {Name: DndCharacterObject}

if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ""

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
@st.cache_data(ttl=3600)
def fetch_character(url):
    """
    Cached function to load character. 
    Streamlit remembers the output for 1 hour so we don't spam D&D Beyond API.
    """
    return DndCharacter(url)

def validate_input(name, url):
    if not name or not url:
        return False, "Name and URL are required."
    if not re.search(URL_PATTERN, url):
        return False, "Invalid URL. Must be a public dndbeyond.com/characters/ link."
    if name in st.session_state['roster']:
        return False, f"Character '{name}' is already in the roster."
    if len(st.session_state['roster']) >= MAX_CHARS:
        return False, f"Roster full! Limit is {MAX_CHARS} characters to save memory."
    return True, ""

# ==========================================
# 4. SIDEBAR: SETUP & ROSTER
# ==========================================
with st.sidebar:
    st.title("⚙️ Setup")
    
    # API Key Input
    user_key = st.text_input("Gemini API Key", type="password", help="Get one at aistudio.google.com")
    if user_key:
        st.session_state['api_key'] = user_key
    
    st.divider()
    
    # Roster Management
    st.subheader(f"Roster ({len(st.session_state['roster'])}/{MAX_CHARS})")
    
    # Form to Add Character
    with st.form("add_char_form", clear_on_submit=True):
        new_name = st.text_input("Character Name (e.g., Vax)")
        new_url = st.text_input("D&D Beyond URL")
        submitted = st.form_submit_button("Add Character")
        
        if submitted:
            is_valid, msg = validate_input(new_name, new_url)
            if is_valid:
                try:
                    with st.spinner(f"Fetching {new_name}..."):
                        # Load character using cached function
                        char_obj = fetch_character(new_url)
                        # Verify name matches (optional, helps keep things organized)
                        # char_obj.name = new_name # Force the name user typed? Or keep sheet name?
                        st.session_state['roster'][new_name] = char_obj
                        st.success(f"Loaded {char_obj.name} (Lvl {char_obj.level})")
                except Exception as e:
                    st.error(f"Failed to load: {e}")
            else:
                st.error(msg)

    # List Loaded Characters
    if st.session_state['roster']:
        st.write("---")
        st.write("**Current Party:**")
        for name in list(st.session_state['roster'].keys()):
            c1, c2 = st.columns([3, 1])
            c1.text(name)
            if c2.button("❌", key=f"del_{name}"):
                del st.session_state['roster'][name]
                st.rerun()
                
    if st.button("Clear Entire Roster"):
        st.session_state['roster'] = {}
        st.rerun()

# ==========================================
# 5. MAIN APPLICATION INTERFACE
# ==========================================
st.title("⚔️ D&D Social Encounter Simulator")

if not st.session_state['api_key']:
    st.warning("Please enter your Google Gemini API Key in the sidebar to start.")
    st.stop()

if len(st.session_state['roster']) < 2:
    st.info("👈 Please add at least **2 Characters** in the sidebar to begin.")
    st.stop()

# --- SELECTION UI ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🗣️ Speaker")
    speaker_name = st.selectbox("Select who is talking:", options=st.session_state['roster'].keys(), key="speaker")

with col2:
    st.subheader("👂 Listener")
    # Exclude speaker from listener options
    listener_opts = [n for n in st.session_state['roster'].keys() if n != speaker_name]
    listener_name = st.selectbox("Select who is listening:", options=listener_opts, key="listener")

st.divider()

# --- INPUTS ---
dialogue = st.text_area("Dialogue Input", height=100, placeholder=f"What does {speaker_name} say to {listener_name}?")
likelihood = st.select_slider("Difficulty / Likelihood", 
    options=["Impossible", "Very Unlikely", "Unlikely", "Neutral", "Likely", "Very Likely", "Guaranteed"],
    value="Neutral",
    help="How willing is the Listener to agree before any dice are rolled?")

# ==========================================
# 6. LOGIC & GENERATION
# ==========================================
if st.button("🎲 Roll & Generate Response", type="primary", use_container_width=True):
    
    if not dialogue:
        st.error("Please enter some dialogue first.")
        st.stop()

    speaker = st.session_state['roster'][speaker_name]
    listener = st.session_state['roster'][listener_name]
    
    # --- MECHANICAL LOGIC ---
    # Dice Rolls
    d20_int = random.randint(1, 20)
    d20_perf = random.randint(1, 20)
    d20_dec = random.randint(1, 20)
    d20_pers = random.randint(1, 20)
    npc_insight_roll = random.randint(1, 20)
    
    # Skill Mods
    s_int = speaker.skills['Intimidation'].total
    s_perf = speaker.skills['Performance'].total
    s_dec = speaker.skills['Deception'].total
    s_pers = speaker.skills['Persuasion'].total
    l_insight = listener.skills['Insight'].total

    # Calculation (Speaker Total - Listener Passive/Active Insight)
    val_int = (s_int + d20_int) - (l_insight + npc_insight_roll)
    val_perf = (s_perf + d20_perf) - (l_insight + npc_insight_roll)
    val_dec = (s_dec + d20_dec) - (l_insight + npc_insight_roll)
    val_pers = (s_pers + d20_pers) + (l_insight + npc_insight_roll)

    # Narrative Outcomes
    effects = [
        {"min": -100, "max": -7, "desc": "Hostile/Mocking"},
        {"min": -6, "max": -5, "desc": "Disrespectful/Dismissive"},
        {"min": -4, "max": -2, "desc": "Awkward/Guarded"},
        {"min": -1, "max": 0, "desc": "Neutral/Indifferent"},
        {"min": 1, "max": 2, "desc": "Interested/Believable"},
        {"min": 3, "max": 5, "desc": "Trusting/Venerated"},
        {"min": 6, "max": 100, "desc": "Awestruck/Devoted"},
    ]
    
    def get_desc(val):
        for e in effects:
            if e['min'] <= val <= e['max']: return e['desc']
        return "Unknown"

    # --- DISPLAY RESULTS ---
    st.write("### 🎲 Mechanical Results")
    st.caption(f"Listener Insight Check: {npc_insight_roll} + {l_insight} = {npc_insight_roll+l_insight}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Intimidation", f"{val_int}", delta=get_desc(val_int))
    c2.metric("Performance", f"{val_perf}", delta=get_desc(val_perf))
    c3.metric("Deception", f"{val_dec}", delta=get_desc(val_dec))
    c4.metric("Persuasion", f"{val_pers}", delta=get_desc(val_pers))

    # --- AI GENERATION ---
    prompt = f"""
    Act as a fantasy author. I need a narrative response for an NPC based on mechanical D&D 5e dice rolls.

    **SCENE:**
    *   **Speaker:** {speaker.name}
    *   **Listener:** {listener.name}
    *   **Context:** The listener is currently "{likelihood}" to agree.
    *   **Dialogue:** "{dialogue}"

    **PROFILES:**
    *   **{speaker.name}:** {speaker.traits} | Ideals: {speaker.ideals} | Flaws: {speaker.flaws}
    *   **{listener.name}:** {listener.traits} | Ideals: {listener.ideals} | Flaws: {listener.flaws}

    **MECHANICS (The Simulation):**
    I have simulated 4 approaches. Please analyze the TONE of the dialogue to pick the ONE skill the player is using, then use that specific result.
    
    1. IF Intimidation: {get_desc(val_int)} (Roll Score: {val_int})
    2. IF Performance: {get_desc(val_perf)} (Roll Score: {val_perf})
    3. IF Deception: {get_desc(val_dec)} (Roll Score: {val_dec})
    4. IF Persuasion: {get_desc(val_pers)} (Roll Score: {val_pers})

    **OUTPUT:**
    Write {listener.name}'s response. 
    1. Describe their internal reaction (filtering the speaker's words through their own Flaws/Ideals).
    2. Write their spoken or physical response.
    """

    with st.spinner("Summoning the Dungeon Master AI..."):
        try:
            genai.configure(api_key=st.session_state['api_key'])
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            
            st.markdown("### 📜 The Story")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"Gemini API Error: {e}")