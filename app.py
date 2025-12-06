
import streamlit as st
import random
import re
import google.generativeai as genai
from dnd_loader import DndCharacter

# ==========================================
# 1. CONFIGURATION & SECRETS
# ==========================================
st.set_page_config(page_title="D&D Social Eng", layout="wide", page_icon="🎲")

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
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'world_graph' not in st.session_state:
    # We defer loading WorldGraph to pages or lazy load
    pass

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

# ==========================================
# 4. SIDEBAR & MAIN
# ==========================================
st.title("🎲 D&D Solo Engine: Setup")
st.write("Welcome! Configure your party here, then navigate to the **Player Screen** or **DM Screen**.")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("⚙️ Roster Config")
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
        if st.button("Clear All"):
            st.session_state['roster'] = {}
            st.rerun()

with col2:
    st.header("Current Party")
    if st.session_state['roster']:
        for name in list(st.session_state['roster'].keys()):
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{name}**")
            if c2.button("🗑️", key=f"del_{name}"):
                del st.session_state['roster'][name]
                st.rerun()
    else:
        st.info("No characters added yet.")

st.divider()
st.info("👉 Use the Sidebar to navigate to **DM Screen** (World Building) or **Player Screen** (Game Loop).")
