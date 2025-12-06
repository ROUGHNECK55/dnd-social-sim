import streamlit as st
import pandas as pd
from modules.graph_engine import WorldGraph

st.set_page_config(page_title="DM Screen", page_icon="🗝️", layout="wide")

st.title("🗝️ DM Screen: World Builder")

# Initialize Graph Engine
if 'world_graph' not in st.session_state:
    st.session_state.world_graph = WorldGraph()

wg = st.session_state.world_graph

# Tabs for different DM functions
tab_ontology, tab_nodes, tab_ingest, tab_persistence = st.tabs(["📜 Ontology", "📦 Nodes & Relations", "📥 Ingestion", "💾 Save/Load"])

# ==========================
# PERSISTENCE TAB
# ==========================
with tab_persistence:
    st.header("💾 World Persistence")
    st.warning("⚠️ The server does NOT auto-save. You must download your world state to save functionality.")
    
    col_dl, col_ul = st.columns(2)
    
    with col_dl:
        st.subheader("Download World")
        json_data = wg.export_to_json()
        st.download_button(
            label="⬇️ Download campaign.json",
            data=json_data,
            file_name="campaign.json",
            mime="application/json"
        )
        
    with col_ul:
        st.subheader("Upload World")
        uploaded_file = st.file_uploader("Upload campaign.json", type=["json"])
        if uploaded_file is not None:
            if st.button("🚨 Overwrite Current World"):
                string_data = uploaded_file.getvalue().decode("utf-8")
                success, msg = wg.import_from_json(string_data)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# ==========================
# ONTOLOGY TAB
# ==========================
with tab_ontology:
    st.header("Ontology Management")
    st.info("Define the allowed types for Nodes and Edges in your world.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Node Types")
        current_node_types = wg.ontology["node_types"]
        # Simple text area for editing list (newline separated)
        new_node_types_str = st.text_area(
            "Allowed Node Types (one per line)", 
            value="\n".join(current_node_types),
            height=200
        )
        if st.button("Update Node Types"):
            node_types = [t.strip() for t in new_node_types_str.split("\n") if t.strip()]
            wg.update_ontology(node_types=node_types)
            st.success("Node types updated!")
            
    with col2:
        st.subheader("Edge Types")
        current_edge_types = wg.ontology["edge_types"]
        new_edge_types_str = st.text_area(
            "Allowed Edge Types (one per line)", 
            value="\n".join(current_edge_types),
            height=200
        )
        if st.button("Update Edge Types"):
            edge_types = [t.strip() for t in new_edge_types_str.split("\n") if t.strip()]
            wg.update_ontology(edge_types=edge_types)
            st.success("Edge types updated!")

# ==========================
# NODES TAB
# ==========================
with tab_nodes:
    st.header("Node Manager")
    
    # 1. CREATE NODE
    with st.expander("➕ Create New Node", expanded=False):
        c1, c2 = st.columns(2)
        node_name = c1.text_input("Node Name (Unique ID)")
        node_type = c2.selectbox("Node Type", wg.ontology["node_types"])
        node_desc = st.text_area("Description")
        
        if st.button("Create Node"):
            if node_name:
                if wg.add_node(node_name, node_type, node_desc):
                    st.success(f"Created node: {node_name}")
                else:
                    st.error("Failed to create node. Check logs or uniqueness.")
            else:
                st.warning("Name is required.")

    st.divider()

    # 2. LIST / EDIT NODES
    st.subheader("Existing Nodes")
    nodes = wg.get_all_nodes()
    
    if nodes:
        # Convert to DataFrame for easier viewing
        df_nodes = pd.DataFrame.from_dict(nodes, orient='index')
        st.dataframe(df_nodes, use_container_width=True)
        
        # Edit Selection
        selected_node = st.selectbox("Select Node to Edit/Delete", options=list(nodes.keys()))
        
        if selected_node:
            n_data = nodes[selected_node]
            st.write(f"**Editing: {selected_node}**")
            
            e_type = st.selectbox("Type", wg.ontology["node_types"], index=wg.ontology["node_types"].index(n_data['type']) if n_data['type'] in wg.ontology["node_types"] else 0)
            e_desc = st.text_area("Description", value=n_data.get('description', ''))
            
            c_edit, c_del = st.columns(2)
            if c_edit.button("Update Node"):
                wg.add_node(selected_node, e_type, e_desc)
                st.success("Updated!")
                st.rerun()
                
            if c_del.button("🗑️ Delete Node", type="primary"):
                wg.delete_node(selected_node)
                st.warning(f"Deleted {selected_node}")
                st.rerun()
                
    else:
        st.info("No nodes in the graph yet.")

# ==========================
# INGESTION TAB
# ==========================
# ==========================
# INGESTION TAB
# ==========================
with tab_ingest:
    st.header("📥 Ingestion Engine")
    st.info("Paste text or load converted resources to auto-generate Nodes.")

    # State Init
    if 'ingest_source_text' not in st.session_state:
        st.session_state.ingest_source_text = ""
    if 'ingest_extracted_data' not in st.session_state:
        st.session_state.ingest_extracted_data = None

    # 1. Source Selection
    ingest_source = st.radio("Source", ["Paste Text", "Load Resource File"])
    
    if ingest_source == "Paste Text":
        # Synchronize text area with session state
        val = st.text_area("Content to Ingest", value=st.session_state.ingest_source_text, height=300)
        st.session_state.ingest_source_text = val
    else:
        # Load File Logic
        import os
        resource_dir = os.path.join("resources", "solo_play")
        if os.path.exists(resource_dir):
            files = [f for f in os.listdir(resource_dir) if f.endswith(".md")]
            selected_file = st.selectbox("Select File", files)
            if selected_file:
                with open(os.path.join(resource_dir, selected_file), 'r', encoding='utf-8') as f:
                    full_text = f.read()
                    st.text_area("File Preview (First 1000 chars)", full_text[:1000], disabled=True)
                    if st.button("Load File Content"):
                        st.session_state.ingest_source_text = full_text
                        st.success("File loaded into memory!")
                        st.rerun()
        else:
            st.error("Resource directory not found.")

    st.write(f"**Current Text Length:** {len(st.session_state.ingest_source_text)} chars")

    # 2. Extract Button
    if st.button("🔮 AI Extract Nodes", type="primary", disabled=not st.session_state.ingest_source_text):
        if len(st.session_state.ingest_source_text) > 50000:
             st.warning("Text too long! Please process in chunks (< 50k characters).")
        else:
            import google.generativeai as genai
            import json
            
            if "GEMINI_API_KEY" in st.secrets:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
                
                prompt_extract = f"""
                Extract entities from the text as Nodes for a Graph Database.
                Ontology (Allowed Types): {wg.ontology['node_types']}
                
                Return JSON dict with key "nodes": [ {{ "name": "...", "type": "...", "description": "..." }} ]
                
                Text:
                {st.session_state.ingest_source_text[:30000]} 
                """
                
                with st.spinner("Extracting..."):
                    try:
                        from modules.utils import parse_llm_json
                        
                        resp = model.generate_content(prompt_extract)
                        data, err = parse_llm_json(resp.text)
                        
                        if err:
                            st.error(err)
                        elif 'nodes' not in data:
                             st.error("Invalid response format: 'nodes' key missing.")
                        else:
                            st.session_state.ingest_extracted_data = data['nodes']
                            st.rerun()

                    except Exception as e:
                        st.error(f"Extraction failed: {e}")
    
    # 3. Review & Save (Outside the Extract button block)
    if st.session_state.ingest_extracted_data:
        st.divider()
        st.subheader("Review Extracted Nodes")
        
        df_extract = pd.DataFrame(st.session_state.ingest_extracted_data)
        st.dataframe(df_extract)
        
        c_save, c_clear = st.columns(2)
        
        if c_save.button("💾 Save All to Graph"):
            count = 0
            for n in st.session_state.ingest_extracted_data:
                # Add node returns True if success
                if wg.add_node(n['name'], n['type'], n['description']):
                    count += 1
            st.success(f"Successfully added {count} nodes!")
            st.session_state.ingest_extracted_data = None # Clear after save
            st.rerun()
            
        if c_clear.button("❌ Discard"):
            st.session_state.ingest_extracted_data = None
            st.rerun()
