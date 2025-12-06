
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

# --- 4. GAME LOOP ---
user_input = st.chat_input("What do you do?")

if user_input:
    # A. DISPLAY USER INPUT
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # B. VALIDATION GATE
    # 1. Extract potential proper nouns (Naive capitalized words)
    # candidates = extract_proper_noun_candidates(user_input)
    # allow_list = ["I", "The", "A", "An", "In", "On", "At", "To"] # Stopwords for capitalization
    # filtered_candidates = {c for c in candidates if c not in allow_list}
    
    # 2. Check against Graph
    known_nodes = list(wg.graph.nodes())
    known_in_text = find_known_entities(user_input, known_nodes)
    
    # STRICT MODE: If there's a capitalized word that isn't known, flag it?
    # This is tricky without a good NER. 
    # Current User Rule: "If player says something exists... check against library... if cannot find match -> ignore/prompt error."
    # We will assume 'find_known_entities' captures the valid ones. 
    # If the user input has NO known entities but clearly interacts with a named thing, we might catch it via LLM.
    # For now, we trust the 'known_in_text' as the Context.
    
    # C. CONTEXT RETRIEVAL
    context_data = wg.get_context(known_in_text)
    context_str = json.dumps(context_data, indent=2)

    # D. LLM: INSTRUCTION GENERATION
    # We ask the LLM to analyze the intent and suggest mechanics.
    prompt_planner = f"""
    Act as a DM AI.
    User Input: "{user_input}"
    Active Character: {active_char}
    World Context (Known Entities): {context_str}
    
    Determine the next step. Return JSON ONLY.
    Options:
    1. "social": The user is trying to socially interact with an NPC.
    2. "oracle": The user is asking a question about the world or exploring unknown.
    3. "narrative": Just a simple action/description, no dice needed.
    4. "error": The user refers to a Proper Noun that is NOT in the Context (Hallucination check).
    
    JSON Format:
    {{
        "type": "social" | "oracle" | "narrative" | "error",
        "reason": "explanation",
        "target": "name of npc if social",
        "missing_entity": "name of entity if error"
    }}
    """
    
    with st.status("Thinking...") as status:
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
            from modules.utils import parse_llm_json
            response = model.generate_content(prompt_planner)
            plan, err = parse_llm_json(response.text)
            
            if err:
                 status.write("Error parsing plan. Retrying...")
                 # Optional: Retry logic here, for now just fail gracefully
                 st.error(f"Planner Error: {err}")
                 st.stop()

            
            status.write(f"Plan: {plan['type']}")
            
            # E. MECHANICS EXECUTION
            final_response = ""
            
            if plan['type'] == 'error':
                 final_response = f"🚫 **Unknown Entity**: I don't know who or what '{plan.get('missing_entity')}' is. (DM Screen update required?)"
            
            elif plan['type'] == 'social':
                # Simplified Social Sim hook
                target_npc = plan.get('target')
                if target_npc and target_npc in st.session_state['roster']:
                    speaker = st.session_state['roster'][active_char]
                    listener = st.session_state['roster'][target_npc]
                    
                    # Auto-roll for now (Standard)
                    outcomes = calculate_social_outcomes(speaker, listener, "Normal", "Normal", {}, False)
                    
                    # Generate Dialogue
                    narrative_prompt = f"""
                    Write a response for {listener.name} to {speaker.name}.
                    Dialogue: "{user_input}"
                    Social Roll Flavor: {outcomes['pers']} (Persuasion used as default for valid flow)
                    Enforce the mechanics flavor.
                    """
                    model_narrative = genai.GenerativeModel('gemini-2.5-flash')
                    res_narrative = model_narrative.generate_content(narrative_prompt)
                    final_response = res_narrative.text
                else:
                    final_response = f"⚠️ Target NPC '{target_npc}' not found in Roster (Stats needed for social sim)."
            
            elif plan['type'] == 'oracle':
                # Ask Oracle logic (Placeholder for solo play tables)
                final_response = f"🔮 **Oracle says**: Something interesting happens regarding {context_data['nodes'].keys()}. (Table lookup implementation pending)"
                
            else: # Narrative
                narrative_prompt = f"""
                Continue the story. 
                Context: {context_str}
                Action: {user_input}
                """
                model_narrative = genai.GenerativeModel('gemini-2.5-flash')
                res = model_narrative.generate_content(narrative_prompt)
                final_response = res.text

            # F. DISPLAY RESPONSE
            st.session_state.chat_history.append({"role": "assistant", "content": final_response})
            with st.chat_message("assistant"):
                st.write(final_response)
                
        except Exception as e:
            st.error(f"Error: {e}")
