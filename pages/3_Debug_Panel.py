
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
    
    if os.path.exists("data/campaign.json"):
        with open("data/campaign.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            st.json(data)
    else:
        st.warning("No campaign.json file found.")
        
    if st.button("Force Save Graph"):
        wg.save()
        st.success("Graph Saved.")

with tab_logs:
    st.header("Directory Check")
    st.write("Current Dir:", os.getcwd())
    
    st.write("Resources:")
    if os.path.exists("resources/solo_play"):
        st.write(os.listdir("resources/solo_play"))
    else:
        st.error("resources/solo_play not found")
