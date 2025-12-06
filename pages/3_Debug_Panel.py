
import streamlit as st
import json
import os
from modules.graph_engine import WorldGraph

st.set_page_config(page_title="Debug Panel", page_icon="🐞", layout="wide")

st.title("🐞 Debug Panel")

if 'world_graph' not in st.session_state:
    st.session_state.world_graph = WorldGraph()
wg = st.session_state.world_graph

tab_state, tab_graph, tab_history, tab_logs = st.tabs(["Session State", "Raw Graph Data", "📜 Campaign History", "Logs/Files"])

with tab_state:
    st.header("Session State")
    st.write(st.session_state)

with tab_graph:
    st.header("Graph Data (campaign.json)")
    
    st.metric("Total Nodes", wg.graph.number_of_nodes())
    st.metric("Total Edges", wg.graph.number_of_edges())
    
    st.markdown("### 🔍 JSON Preview")
    st.caption("Current In-Memory State")
    st.json(json.loads(wg.export_to_json()))

with tab_history:
    st.header("Campaign Log")
    
    if 'chat_history' in st.session_state and st.session_state.chat_history:
        # Prepare text for download
        log_text = "CAMPAIGN HISTORY\n================\n\n"
        
        for msg in st.session_state.chat_history:
            role = msg['role'].upper()
            content = msg['content']
            debug = msg.get('debug_info', None)
            
            # Display
            with st.chat_message(msg['role']):
                st.write(content)
                if debug:
                    with st.expander("🎲 Mechanics & Tables"):
                        st.write(f"**Type**: {debug.get('type')}")
                        if 'table' in debug:
                            st.write(f"**Table Used**: {debug['table']}")
                            st.page_link("pages/4_Wiki.py", label="📖 View Table in Wiki", icon="📘")
                        
                        if 'rolls' in debug:
                            st.subheader("Dice Rolls")
                            st.json(debug['rolls'])
                        if 'scores' in debug:
                            st.subheader("Net Scores")
                            st.json(debug['scores'])
            
            # Text format
            log_text += f"[{role}]: {content}\n"
            if debug:
                log_text += f"   [META]: {debug}\n"
            log_text += "\n"
            
        st.divider()
        st.download_button(
            label="📄 Download Campaign Log (.txt)",
            data=log_text,
            file_name="campaign_log.txt",
            mime="text/plain"
        )
    else:
        st.info("No history yet. Go to the Player Screen and start your adventure!")

with tab_logs:
    st.header("Directory Check")
    st.write("Current Dir:", os.getcwd())
    
    st.write("Resources:")
    if os.path.exists("resources/solo_play"):
        st.write(os.listdir("resources/solo_play"))
    else:
        st.error("resources/solo_play not found")
