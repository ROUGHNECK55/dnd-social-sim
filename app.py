import streamlit as st
import random
import re
import google.generativeai as genai
from dnd_loader import DndCharacter

# ==========================================
# 1. CONFIGURATION & SECRETS
# ==========================================
st.set_page_config(page_title="D&D Social Sim", layout="wide", page_icon="🎲")

MAX_CHARS = 10 
URL_PATTERN = r"dndbeyond\.com/characters/\d+"

# --- LOAD SECRETS (STRICT MODE) ---
# We try to get the key. If missing, we STOP. We do not ask the user.
if "GEMINI_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("❌ **Missing API Key**")
    st.markdown("""
    **To the App Owner:**
    1. Go to your Streamlit App Dashboard.
    2. Click **Settings** -> **Secrets**.
    3. Add this line: `GEMINI_API_KEY = "AIzaSy..."`
    """)
    st.stop()

# ==========================================
# 2. SESSION STATE
# ==========================================
if 'roster' not in st.session_state:
    st.session_state['roster'] = {} 

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
@st.cache_data(ttl=3600)
def fetch_character(url):
    return DndCharacter(url)

def validate_input(name, url):
    if not name or not url: return False, "Name and URL are required."
    if not re.search(URL_PATTERN, url): return False, "Invalid URL."
    if name in st.session_state['roster']: return False, "Name taken."
    if len(st.session_state['roster']) >= MAX_CHARS: return False, "Roster Full."
    return True, ""

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Roster Config")
    st.success("✅ AI Connected (Service Account)")
    
    with st.form("add_char_form", clear_on_submit=True):
        new_name = st.text_input("Name (e.g. Vex)")
        new_url = st.text_input("D&D Beyond URL")
        submitted = st.form_submit_button("➕ Add Character")
        
        if submitted:
            is_valid, msg = validate_input(new_name, new_url)
            if is_valid:
                try:
                    with st.spinner(f"Summoning {new_name}..."):
                        st.session_state['roster'][new_name] = fetch_character(new_url)
                        st.success(f"Added {new_name}!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Load Failed: {e}")
            else:
                st.error(msg)

    if st.session_state['roster']:
        st.divider()
        st.write(f"**Party ({len(st.session_state['roster'])})**")
        for name in list(st.session_state['roster'].keys()):
            c1, c2 = st.columns([3, 1])
            c1.write(name)
            if c2.button("🗑️", key=f"del_{name}"):
                del st.session_state['roster'][name]
                st.rerun()
        if st.button("Clear All"):
            st.session_state['roster'] = {}
            st.rerun()

# ==========================================
# 5. MAIN LOGIC
# ==========================================
st.title("⚔️ D&D Social Simulator")

if len(st.session_state['roster']) < 2:
    st.info("👈 Please add at least **2 Characters** in the sidebar.")
    st.stop()

# --- SELECTION ---
col1, col2 = st.columns(2)
with col1:
    speaker_name = st.selectbox("🗣️ Speaker", options=st.session_state['roster'].keys())
with col2:
    listener_opts = [n for n in st.session_state['roster'].keys() if n != speaker_name]
    listener_name = st.selectbox("👂 Listener", options=listener_opts)

st.divider()

# --- INPUTS ---
dialogue = st.text_area("Dialogue", height=100, placeholder=f"What does {speaker_name} say?")
likelihood = st.select_slider("Context / Difficulty", 
    options=["Impossible", "Very Unlikely", "Unlikely", "Neutral", "Likely", "Very Likely", "Guaranteed"],
    value="Neutral")

# ==========================================
# 6. EFFECTS MATRIX & GENERATION
# ==========================================
EFFECTS_MATRIX = [
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
        "deception": "{l} trusts {s} implicitly, swallowing the lie whole.",
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

def get_outcome_text(score, skill_type, s_name, l_name):
    for row in EFFECTS_MATRIX:
        if row["min"] <= score <= row["max"]:
            return row[skill_type].format(s=s_name, l=l_name)
    return "Result unclear."

if st.button("🎲 Roll & Generate Response", type="primary", use_container_width=True):
    if not dialogue:
        st.error("Please enter dialogue.")
        st.stop()

    speaker = st.session_state['roster'][speaker_name]
    listener = st.session_state['roster'][listener_name]
    
    # --- MATH ---
    rolls = {k: random.randint(1,20) for k in ['int','perf','dec','pers','insight']}
    l_insight_total = listener.skills['Insight'].total + rolls['insight']
    
    scores = {
        'intimidation': (speaker.skills['Intimidation'].total + rolls['int']) - l_insight_total,
        'performance': (speaker.skills['Performance'].total + rolls['perf']) - l_insight_total,
        'deception': (speaker.skills['Deception'].total + rolls['dec']) - l_insight_total,
        'persuasion': (speaker.skills['Persuasion'].total + rolls['pers']) + l_insight_total 
    }
    
    outcomes = {
        'int': get_outcome_text(scores['intimidation'], 'intimidation', speaker.name, listener.name),
        'perf': get_outcome_text(scores['performance'], 'performance', speaker.name, listener.name),
        'dec': get_outcome_text(scores['deception'], 'deception', speaker.name, listener.name),
        'pers': get_outcome_text(scores['persuasion'], 'persuasion', speaker.name, listener.name),
    }

    # --- DISPLAY METRICS ---
    st.write("### 🎲 Mechanical Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Intimidation", scores['intimidation'], help=outcomes['int'])
    c2.metric("Performance", scores['performance'], help=outcomes['perf'])
    c3.metric("Deception", scores['deception'], help=outcomes['dec'])
    c4.metric("Persuasion", scores['persuasion'], help=outcomes['pers'])

    # --- AI PROMPT ---
    prompt = f"""
    Act as a fantasy author / Dungeon Master.
    
    **SCENE:**
    *   **Speaker:** {speaker.name} (Traits: {speaker.traits}, Ideals: {speaker.ideals}, Flaws: {speaker.flaws})
    *   **Listener:** {listener.name} (Traits: {listener.traits}, Ideals: {listener.ideals}, Flaws: {listener.flaws})
    *   **Context:** The listener is "{likelihood}" to agree.
    *   **Dialogue:** "{dialogue}"

    **MECHANICS:**
    I have simulated the social dice rolls. Analyze the tone of the dialogue to decide which ONE skill applies, then use the description below to write the response.
    
    1. IF Intimidation (Score {scores['intimidation']}): "{outcomes['int']}"
    2. IF Performance (Score {scores['performance']}): "{outcomes['perf']}"
    3. IF Deception (Score {scores['deception']}): "{outcomes['dec']}"
    4. IF Persuasion (Score {scores['persuasion']}): "{outcomes['pers']}"

    **TASK:**
    Write {listener.name}'s response. 
    - Describe their internal thought process.
    - Give their spoken or physical reaction based strictly on the mechanics.
    """

    with st.spinner("Consulting the Oracle..."):
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # TRY FLASH FIRST, FALLBACK TO PRO IF 404
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
            except Exception:
                # Fallback for older keys/regions
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
            
            st.markdown("### 📜 The Narrative")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"AI Error: {e}")
