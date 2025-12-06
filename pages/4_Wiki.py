
import streamlit as st
import pandas as pd
from modules.mech_social import EFFECTS_MATRIX, STANDARD_RANGES, PERSUASION_RANGES

st.set_page_config(page_title="Mechanics Wiki", page_icon="📘", layout="wide")

st.title("📘 Mechanics Wiki")

st.markdown("""
This Engine uses a hybrid of **Graph-based Context** and **Deterministic Mechanics**. 
Here is how the underlying systems work.
""")

tab_social, tab_oracle, tab_graph = st.tabs(["🗣️ Social Sim", "🔮 Oracle", "🕸️ World Graph"])

# ==========================
# SOCIAL MECHANICS
# ==========================
with tab_social:
    st.header("Social Simulation Mechanics")
    
    st.subheader("1. The Contest")
    st.markdown("""
    When you interact with an NPC, a **Contested Roll** happens behind the scenes:
    
    $$
    \\text{Score} = (\\text{Player Skill} + \\text{d20}) - (\\text{NPC Insight} + \\text{d20})
    $$
    
    - **Player Skill**: Intimidation, Performance, Deception, or Persuasion.
    - **NPC Insight**: The listener's ability to read your intent.
    - **Result**: A positive score means you beat their insight. A negative score means they saw through you or resisted.
    """)
    
    st.subheader("2. Interpreting the Score")
    st.write("The Net Score determines the reaction via the **Effects Matrix**.")
    
    # Create a nice dataframe for the ranges
    ranges_data = []
    for i, (min_v, max_v) in enumerate(STANDARD_RANGES):
        ranges_data.append({
            "Range": f"{min_v} to {max_v}",
            "Outcome Level": f"Level {i} (0=Worst, 6=Best)",
            "Description": "See Matrix below"
        })
    st.table(pd.DataFrame(ranges_data))
    
    st.subheader("3. The Effects Matrix")
    st.info("This matrix dictates the *Flavor* of the response, which the AI then uses to write the dialogue.")
    
    # We reconstruct the matrix for display
    matrix_rows = []
    skill_types = ["intimidation", "performance", "deception", "persuasion"]
    
    for level, row in enumerate(EFFECTS_MATRIX):
        display_row = {"Level": level}
        for skill in skill_types:
            display_row[skill.capitalize()] = row[skill].format(s="{Speaker}", l="{Listener}")
        matrix_rows.append(display_row)
        
    df_matrix = pd.DataFrame(matrix_rows)
    st.dataframe(df_matrix.set_index("Level"), use_container_width=True)

# ==========================
# ORACLE
# ==========================
with tab_oracle:
    st.header("The Oracle")
    st.markdown("""
    The Oracle is used for **Solo Play** when you need to answer a question about the world that isn't defined in the Graph.
    
    **Logic Flow:**
    1.  **Context Check**: AI looks at the Graph context.
    2.  **Probability**: AI estimates the likelihood based on the context.
    3.  **Roll**: AI simulates a roll (conceptually) or uses a Logic Table.
    4.  **Result**: Returns a "Yes/No/But/And" style answer or a "Conceptual" answer.
    
    *Current Implementation: The Oracle uses the LLM's latent knowledge combined with standard Solo RPG probability prompts.*
    """)

# ==========================
# GRAPH
# ==========================
with tab_graph:
    st.header("The World Graph")
    st.markdown("""
    The brain of the operation.
    
    -   **Nodes**: People, Places, Items, Concepts.
    -   **Edges**: Relationships (e.g., "Gundren" --*Knows*--> "Map").
    
    **How it works during play:**
    1.  **Entity Tagging**: You select entities in the "Active Entities" box.
    2.  **Expansion**: The Engine grabs those nodes AND their direct neighbors (1 degree of separation).
    3.  **Context Window**: This sub-graph is converted to JSON and fed to the AI as "Short Term Memory".
    """)
