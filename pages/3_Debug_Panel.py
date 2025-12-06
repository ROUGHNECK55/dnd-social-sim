
import streamlit as st
import json
import os
from modules.graph_engine import WorldGraph

st.set_page_config(page_title="Debug Panel", page_icon="🐞", layout="wide")

st.title("🐞 Debug Panel")

if 'world_graph' not in st.session_state:
    st.session_state.world_graph = WorldGraph()
wg = st.session_state.world_graph

tab_state, tab_graph, tab_logs = st.tabs(["Session State", "Raw Graph Data", "Logs/Files"])

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

with tab_logs:
    st.header("Directory Check")
    st.write("Current Dir:", os.getcwd())
    
    st.write("Resources:")
    if os.path.exists("resources/solo_play"):
        st.write(os.listdir("resources/solo_play"))
    else:
        st.error("resources/solo_play not found")
