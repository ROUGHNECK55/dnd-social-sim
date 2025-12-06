
import streamlit as st
import google.generativeai as genai
import json
from modules.graph_engine import WorldGraph
from modules.nlp_utils import extract_proper_noun_candidates, find_known_entities
from modules.mech_social import calculate_social_outcomes

st.set_page_config(page_title="Solo Player", page_icon="⚔️", layout="wide")

st.title("⚔️ Solo Player")

# --- 1. SETUP & CONFIG ---
if "GEMINI_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("❌ Missing API Key in secrets.")
    st.stop()

if 'world_graph' not in st.session_state:
    st.session_state.world_graph = WorldGraph()
wg = st.session_state.world_graph

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'roster' not in st.session_state:
    st.session_state['roster'] = {}

# --- 2. SIDEBAR (Character Selection) ---
with st.sidebar:
    st.header("👤 Active Character")
    # Quick roster access (simplified for now, ideally load from Graph)
    char_names = list(st.session_state['roster'].keys())
    if char_names:
        active_char = st.selectbox("Playing As", char_names)
    else:
        st.warning("No characters loaded. Go to Home to add them.")
        active_char = "Player"

# --- 3. CHAT INTERFACE ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. GAME LOOP & UI ---
col_action, col_target = st.columns([1, 2])

with col_action:
    action_type = st.radio("Action Type", ["Narrative", "Social", "Oracle"], horizontal=True)

target_context = None

with col_target:
    if action_type == "Social":
        # Filter nodes by Character or Faction
        candidate_targets = wg.get_nodes_by_type("Character") + wg.get_nodes_by_type("Faction")
        target_context = st.selectbox("Social Target", candidate_targets)
    elif action_type == "Oracle":
        # Maybe a sub-type of oracle question?
        oracle_type = st.selectbox("Oracle Type", ["General", "Existence", "Attribute", "Plot Twist"])
        target_context = oracle_type
    else:
        # Narrative - maybe select a Location?
        locs = wg.get_nodes_by_type("Location")
        if locs:
            target_context = st.selectbox("Current Location (Context)", locs)

# Context Helper (The requested @ tag replacement)
st.caption("🏷️ **Context Helper**: Select entities to strictly include in the AI's awareness.")
all_nodes = list(wg.graph.nodes())
context_tags = st.multiselect("Active Entities", all_nodes, default=[target_context] if target_context and action_type == "Social" else None)

user_input = st.chat_input("What do you do?")

if user_input:
    # A. DISPLAY USER INPUT
    st.session_state.chat_history.append({"role": "user", "content": user_input, "debug_info": None})
    with st.chat_message("user"):
        st.write(user_input)

    # B. CONTEXT RETRIEVAL (Explicit + Inferred)
    # Start with tags
    known_entities = set(context_tags) 
    # Add inferred (simple match)
    known_in_text = find_known_entities(user_input, all_nodes)
    known_entities.update(known_in_text)
    
    context_data = wg.get_context(list(known_entities))
    context_str = json.dumps(context_data, indent=2)

    with st.status("Gamemaster thinking...") as status:
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "text/plain"}) # Text is fine for narrative
            
            final_response = ""

            # C. EXPLICIT ROUTING
            if action_type == "Social":
                status.write("Processing Social Encounter...")
                if target_context and target_context in st.session_state['roster']:
                    speaker = st.session_state['roster'][active_char]
                    listener = st.session_state['roster'][target_context]
                    
                    # Mechanics
                    outcomes = calculate_social_outcomes(speaker, listener, "Normal", "Normal", {}, False)
                    
                    # Narrative Generation
                    prompt = f"""
                    Write a response for {listener.name} to {speaker.name}.
                    Context: {context_str}
                    User Action: "{user_input}"
                    Social Result Flavor: {outcomes['pers']} 
                    (Use Persuasion logic as default, but adapt if input implies Intimidation/Deception)
                    """
                    resp = model.generate_content(prompt)
                    final_response = resp.text
                elif target_context:
                    # NPC in Graph but not Roster (No stats) - Pure Narrative Social
                    prompt = f"""
                    Roleplay as {target_context}.
                    Context: {context_str}
                    User Action: "{user_input}"
                    Reflect the character's description from the context.
                    """
                    resp = model.generate_content(prompt)
                    final_response = resp.text
                else:
                     final_response = "⚠️ No Target Selected."

            elif action_type == "Oracle":
                status.write("Consulting the Oracle...")
                prompt = f"""
                Act as a Solo RPG Oracle.
                Type: {target_context}
                Context: {context_str}
                Question: "{user_input}"
                Provide a yes/no/maybe answer or a short conceptual result based on standard solo RPG tables.
                """
                resp = model.generate_content(prompt)
                final_response = f"🔮 **Oracle**: {resp.text}"

            else: # Narrative
                status.write("Weaving Story...")
                prompt = f"""
                Act as a Dungeon Master. Continue the story.
                Active Character: {active_char}
                Context: {context_str}
                Action: "{user_input}"
                Keep it engaging and concise.
                """
                resp = model.generate_content(prompt)
                final_response = resp.text

            # D. OUTPUT
            debug_info = None
            if action_type == "Social":
                debug_info = {
                     "type": "Social",
                     "rolls": outcomes['rolls'],
                     "scores": outcomes['scores'],
                     "table": "Effects Matrix"
                }
            elif action_type == "Oracle":
                debug_info = {
                    "type": "Oracle",
                    "subtype": target_context,
                    "table": f"Oracle ({target_context})"
                }

            st.session_state.chat_history.append({"role": "assistant", "content": final_response, "debug_info": debug_info})
            with st.chat_message("assistant"):
                st.write(final_response)

            # Success!
            st.rerun()

        except Exception as e:
            st.error(f"AI Error: {e}")
