
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

    st.markdown("#### Persuasion Specifics")
    st.write("Persuasion uses a different difficulty curve due to its powerful nature:")
    
    p_ranges_data = []
    for i, (min_v, max_v) in enumerate(PERSUASION_RANGES):
        p_ranges_data.append({
            "Range": f"{min_v} to {max_v}",
            "Outcome Level": f"Level {i} (0=Worst, 6=Best)"
        })
    st.table(pd.DataFrame(p_ranges_data))
    
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
    The Oracle acts as a **Virtual Game Master**, simulating a probability check to answer user questions ("Is the door locked?", "Does the guard see me?").
    
    ### 1. The Decision Tree (Process)
    When you ask an Oracle Question, the system follows this logic:
    
    1.  **Context Analysis**: The AI reads the *Current Context* (Active Entities + Neighbors) and the *Question*.
    2.  **Likelihood Assessment**: The AI determines a "Likelihood Modifier" based on the logic of the scene.
        *   *Example: Asking "Is there dragon in this random tavern?" vs "Is there ale in this tavern?"*
    3.  **Virtual Roll**: The AI simulates a **d100** roll (conceptually) against this likelihood.
    4.  **Threshold Mapping**: The result is mapped to the **7-Point Agreement Scale**.
    
    ### 2. The Game Math (Simulated)
    While the AI uses latent probability, it simulates the following standard Tabletop math structure:
    
    **Base Logic**: 50/50 Chance (DC 50)
    **Modifiers**:
    *   **Impossible**: -40 to Roll (Requires near-perfect luck)
    *   **Unlikely**: -20 to Roll
    *   **Likely**: +20 to Roll
    *   **Certain**: +40 to Roll
    
    **The Output Mapping (7-Point Scale):**
    | Simulated d100 Result | Agreement Scale Outcome | Traditional Oracle |
    | :--- | :--- | :--- |
    | **91+** | **Agrees Whole Heartedly** | "Yes, and..." (Critical Success) |
    | **71 - 90** | **Agree** | "Yes" |
    | **51 - 70** | **Somewhat Agree** | "Yes, but..." (Success at a cost) |
    | **41 - 50** | **Neither Agree or Disagree** | "Maybe" / "Unclear" |
    | **21 - 40** | **Somewhat Disagree** | "No, but..." (Fail forward) |
    | **11 - 20** | **Disagree** | "No" |
    | **10 or less** | **Whole Heartedly Disagree** | "No, and..." (Critical Fail) |

    ### 3. Examples
    
    **Example A: The Guard**
    *   **Context**: Player is sneaking. Guard is "Lazy" and "Tired".
    *   **Question**: "Does the guard notice me?"
    *   **Assessment**: Guard is distracted. Likelihood of noticing is *Unlikely (-20)*.
    *   **Simulated Roll**: AI rolls a 60. -20 Modifier = **40**.
    *   **Result**: 40 maps to **Somewhat Disagree** ("No, but...").
    *   **Output**: *"No, he doesn't see you, BUT he hears a noise and starts walking toward your hiding spot."*

    **Example B: The Locked Door**
    *   **Context**: A high-security vault.
    *   **Question**: "Is the door unlocked?"
    *   **Assessment**: It's a vault. Likelihood is *Impossible (-40)*.
    *   **Simulated Roll**: AI rolls a 95 (Amazing luck). -40 Modifier = **55**.
    *   **Result**: 55 maps to **Somewhat Agree** ("Yes, but...").
    *   **Output**: *"Yes, it's unlocked, BUT the alarm system is clearly active and will trigger if you open it."*
    
    ### The Agreement Scale
    For both Oracle answers and Social outcomes, the Engine uses a 7-point scale:
    
    | Level | Meaning |
    | :--- | :--- |
    | **Agrees Whole Heartedly** | Equivalent to "Yes, and..." or CRIT SUCCESS |
    | **Agree** | "Yes" or Strong Success |
    | **Somewhat Agree** | "Yes, but..." or Marginal Success |
    | **Neither Agree or Disagree** | "Maybe" or Neutral/Stalemate |
    | **Somewhat Disagree** | "No, but..." or Marginal Failure |
    | **Disagree** | "No" or Strong Failure |
    | **Whole Heartedly Disagree** | "No, and..." or CRIT FAIL |
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
