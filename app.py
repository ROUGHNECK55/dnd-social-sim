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

# --- LOAD SECRETS ---
if "GEMINI_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("❌ **Missing API Key**")
    st.markdown("Please configure `GEMINI_API_KEY` in your Streamlit Secrets.")
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

def validate_url(url):
    if not url: return False, "URL is required."
    if not re.search(URL_PATTERN, url): return False, "Invalid URL format."
    if len(st.session_state['roster']) >= MAX_CHARS: return False, "Roster Full (Max 10)."
    return True, ""

def roll_d20(state, use_min_10):
    """
    Handles Advantage/Disadvantage AND Minimum 10 logic.
    If use_min_10 is True, the die rolls between 10 and 20.
    """
    # Determine the floor of the die
    low = 10 if use_min_10 else 1
    
    # Generate two potential rolls (in case of Adv/Dis)
    r1 = random.randint(low, 20)
    r2 = random.randint(low, 20)
    
    if state == "Advantage":
        return max(r1, r2)
    elif state == "Disadvantage":
        return min(r1, r2)
    else:
        return r1

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Roster Config")
    st.success("✅ AI Connected (Gemini 2.5)")
    
    with st.form("add_char_form", clear_on_submit=True):
        new_url = st.text_input("D&D Beyond URL")
        st.info("⚠️ Character Privacy must be **Public** on D&D Beyond.")
        submitted = st.form_submit_button("➕ Add Character")
        
        if submitted:
            is_valid, msg = validate_url(new_url)
            if is_valid:
                try:
                    with st.spinner("Fetching data..."):
                        char_obj = fetch_character(new_url)
                        if char_obj.name in st.session_state['roster']:
                            st.error(f"'{char_obj.name}' is already in the roster.")
                        else:
                            st.session_state['roster'][char_obj.name] = char_obj
                            st.success(f"Added **{char_obj.name}**!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Load Failed. Check privacy settings.\nError: {e}")
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

col1, col2 = st.columns(2)
with col1:
    speaker_name = st.selectbox("🗣️ Speaker", options=st.session_state['roster'].keys())
    # SPEAKER CONTROLS
    s_state = st.radio(f"{speaker_name}'s Roll", ["Normal", "Advantage", "Disadvantage"], key="s_state", horizontal=True)
    s_floor = st.radio(f"{speaker_name}'s Floor", ["Standard (1-20)", "Min 10 (10-20)"], key="s_floor", horizontal=True)

with col2:
    listener_opts = [n for n in st.session_state['roster'].keys() if n != speaker_name]
    listener_name = st.selectbox("👂 Listener", options=listener_opts)
    # LISTENER CONTROLS
    l_state = st.radio(f"{listener_name}'s Roll", ["Normal", "Advantage", "Disadvantage"], key="l_state", horizontal=True)
    l_floor = st.radio(f"{listener_name}'s Floor", ["Standard (1-20)", "Min 10 (10-20)"], key="l_floor", horizontal=True)

st.divider()

dialogue = st.text_area("Dialogue", height=100, placeholder=f"What does {speaker_name} say?")

outcome_setting = st.select_slider(
    "Deterministic Outcome (DM Fiat)", 
    options=[
        "Complete Rejection", 
        "Mostly Rejected", 
        "Neither Reject nor Accept", 
        "Mostly Accepted", 
        "Completely Accepted"
    ],
    value="Neither Reject nor Accept",
    help="You decide the result. The dice will decide the emotional flavor."
)

# ==========================================
# 6. EFFECTS & LOOKUP LOGIC
# ==========================================
EFFECTS_MATRIX = [
    {"intimidation": "{l} is deeply offended by {s}'s aggression and immediately becomes hostile or mocks the attempt.", "performance": "{l} finds {s} utterly obnoxious and actively tries to leave the conversation.", "deception": "{l} sees right through {s}, convinced they are lying maliciously.", "persuasion": "{l} completely misinterprets {s}'s logic, taking the suggestion as an insult."},
    {"intimidation": "{l} feels disrespected by {s} and digs their heels in, refusing to cooperate.", "performance": "{l} is unimpressed and dismissive of {s}'s antics.", "deception": "{l} distrusts {s} and is suspicious of their motives.", "persuasion": "{l} simply doesn't understand {s}'s point and gets frustrated."},
    {"intimidation": "{l} feels {s} is posturing but isn't truly afraid, leading to an awkward standoff.", "performance": "{l} avoids making eye contact, finding {s}'s behavior slightly cringe-worthy.", "deception": "{l} senses {s} is withholding information and becomes guarded.", "persuasion": "{l} is confused by the details and remains unconvinced by {s}."},
    {"intimidation": "{l} sees {s} as an equal; they are not scared, but they are listening.", "performance": "{l} is indifferent to {s}, neither entertained nor annoyed.", "deception": "{l} is neutral, neither believing nor disbelieving {s} fully.", "persuasion": "{l} understands the surface level of {s}'s request but needs more convincing."},
    {"intimidation": "{l} respects {s}'s strength and feels compelled to listen.", "performance": "{l} is drawn in by {s}'s charisma and pays close attention.", "deception": "{s}'s story seems plausible enough to {l}.", "persuasion": "{l} feels enlightened by {s}'s argument and is inclined to agree."},
    {"intimidation": "{l} is thoroughly cowed by {s} and feels a strong urge to submit to the demand.", "performance": "{l} is captivated, actively seeking {s}'s approval or company.", "deception": "{l} trusts {s} implicitly, swallowing the lie whole.", "persuasion": "{l} fully understands and empathizes with {s}'s intent."},
    {"intimidation": "{l} is terrified or awestruck, viewing {s} as a dominant force of nature.", "performance": "{l} becomes an instant fan, hanging on {s}'s every word.", "deception": "{l} believes {s} completely, perhaps even defending the lie to others.", "persuasion": "{l} experiences a shift in perspective, expanding their understanding to align with {s}."},
]

STANDARD_RANGES = [(-100, -7), (-6, -5), (-4, -2), (-1, 0), (1, 2), (3, 5), (6, 100)]
PERSUASION_RANGES = [(0, 9), (10, 14), (15, 19), (20, 24), (25, 29), (30, 34), (35, 200)]

def get_standard_text(score, skill_type, s_name, l_name):
    index = 3 
    for i, (min_val, max_val) in enumerate(STANDARD_RANGES):
        if min_val <= score <= max_val:
            index = i
            break
    return EFFECTS_MATRIX[index][skill_type].format(s=s_name, l=l_name)

def get_persuasion_text(score, s_name, l_name):
    index = 3 
    for i, (min_val, max_val) in enumerate(PERSUASION_RANGES):
        if min_val <= score <= max_val:
            index = i
            break
    return EFFECTS_MATRIX[index]["persuasion"].format(s=s_name, l=l_name)

# ==========================================
# 7. EXECUTION
# ==========================================
if st.button("🎲 Roll & Generate Response", type="primary", use_container_width=True):
    if not dialogue:
        st.error("Please enter dialogue.")
        st.stop()

    speaker = st.session_state['roster'][speaker_name]
    listener = st.session_state['roster'][listener_name]
    
    # --- BOOLEANS FOR MIN 10 ---
    s_use_min = (s_floor == "Min 10 (10-20)")
    l_use_min = (l_floor == "Min 10 (10-20)")

    # --- MATH (With Adv/Dis and Min 10) ---
    rolls = {}
    
    # Speaker Rolls
    rolls['int'] = roll_d20(s_state, s_use_min)
    rolls['perf'] = roll_d20(s_state, s_use_min)
    rolls['dec'] = roll_d20(s_state, s_use_min)
    rolls['pers'] = roll_d20(s_state, s_use_min)
    
    # Listener Roll
    rolls['insight'] = roll_d20(l_state, l_use_min)

    # Calculate Totals
    l_insight_total = listener.skills['Insight'].total + rolls['insight']
    
    score_int = (speaker.skills['Intimidation'].total + rolls['int']) - l_insight_total
    score_perf = (speaker.skills['Performance'].total + rolls['perf']) - l_insight_total
    score_dec = (speaker.skills['Deception'].total + rolls['dec']) - l_insight_total
    score_pers = (speaker.skills['Persuasion'].total + rolls['pers']) + l_insight_total 
    
    # --- TEXT LOOKUP ---
    outcomes = {
        'int': get_standard_text(score_int, 'intimidation', speaker.name, listener.name),
        'perf': get_standard_text(score_perf, 'performance', speaker.name, listener.name),
        'dec': get_standard_text(score_dec, 'deception', speaker.name, listener.name),
        'pers': get_persuasion_text(score_pers, speaker.name, listener.name),
    }

    # --- DISPLAY METRICS ---
    st.write("### 🎲 Dice Results (Flavor)")
    
    # Status Line
    s_label = f"{s_state}" + (" + Min 10" if s_use_min else "")
    l_label = f"{l_state}" + (" + Min 10" if l_use_min else "")
    st.caption(f"**{speaker_name}:** {s_label} | **{listener_name}:** {l_label}")
    st.info(f"**Target Outcome:** {outcome_setting}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Intimidation", score_int, help=outcomes['int'])
    c2.metric("Performance", score_perf, help=outcomes['perf'])
    c3.metric("Deception", score_dec, help=outcomes['dec'])
    c4.metric("Persuasion", score_pers, help=outcomes['pers'])

    # --- AI PROMPT ---
    prompt = f"""
    Act as a fantasy author / Dungeon Master.
    
    **SCENE:**
    *   **Speaker:** {speaker.name} (Traits: {speaker.traits}, Ideals: {speaker.ideals}, Flaws: {speaker.flaws})
    *   **Listener:** {listener.name} (Traits: {listener.traits}, Ideals: {listener.ideals}, Flaws: {listener.flaws})
    *   **Dialogue:** "{dialogue}"

    **DIRECTIVE (MANDATORY OUTCOME):**
    The interaction MUST end with: **{outcome_setting}**.

    **MECHANICS (EMOTIONAL FLAVOR):**
    I have simulated the dice rolls. Analyze the tone of the dialogue to pick the ONE skill used, then use its specific description below to "color" the outcome.
    (Example: If the Outcome is 'Rejection' but the Mechanics say 'Awestruck', the listener might be terrified but still forced to say no). Using the following to determine the flavor of the reaction.
    
    1. The amount of respect (Flavor): "{outcomes['int']}"
    2. The amount of attention (Flavor): "{outcomes['perf']}"
    3. The amount of trust (Flavor): "{outcomes['dec']}"
    4. The amount of understanding (Flavor): "{outcomes['pers']}"

    **TASK:**
    Write {listener.name}'s response. 
    1. **Enforce the Mandatory Outcome** ({outcome_setting}).
    2. Use the **Mechanical Flavor** to describe the listener's emotional state while delivering that outcome.
    3. Describe their internal thoughts and physical reaction.
    """

    with st.spinner("Consulting the Oracle..."):
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            st.markdown("### 📜 The Narrative")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"AI Error: {e}")
            st.error(f"AI Error: {e}")
