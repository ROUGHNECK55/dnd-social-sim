
"""
prompt_templates.py

Centralized module for generating LLM prompts using Gemini best practices.
Structure:
### IDENTITY
### CONTEXT
### TASK
### CONSTRAINTS
### OUTPUT FORMAT
"""

AGREEMENT_SCALE = [
    "Whole Heartedly Disagree",
    "Disagree",
    "Somewhat Disagree",
    "Neither Agree or Disagree",
    "Somewhat Agree",
    "Agree",
    "Agrees Whole Heartedly"
]

def _build_context_section(context_str):
    return f"""### CONTEXT
The following JSON data represents the current World State (Short Term Memory).
It includes relevant Characters, Locations, and their relationships.
{context_str}
"""

def get_social_prompt(speaker_name, listener_name, context_str, user_action, outcome_str):
    """
    Generates a prompt for a Social Interaction.
    outcome_str: The determined result (e.g., "Agrees Whole Heartedly" or specific mechanic flavor).
    """
    return f"""### IDENTITY
You are a Dungeon Master and an expert creative writer for a Tabletop RPG.
You are roleplaying as the NPC: **{listener_name}**.

{_build_context_section(context_str)}

### TASK
Write a dialogue response for **{listener_name}** speaking to **{speaker_name}**.
The user (playing {speaker_name}) has just said/done: "{user_action}"

### CONSTRAINTS
1.  **Mandatory Outcome**: The reaction MUST align with this specific Result: **"{outcome_str}"**.
2.  **Tone**: Match the character's personality defined in the Context.
3.  **Brevity**: Keep the response concise (2-4 sentences) unless a monologue is appropriate.
4.  **No Markdown**: Do not use bold/italic formatting for speech. Use standard novel style.

### OUTPUT FORMAT
Return ONLY the dialogue/narrative text. No meta-commentary.
"""

def get_oracle_prompt(context_str, user_question, oracle_type="General"):
    """
    Generates a prompt for the Solo Oracle.
    """
    return f"""### IDENTITY
You are a Solo RPG Oracle, a dispassionate arbiter of fate.

{_build_context_section(context_str)}

### TASK
Answer the player's question based on the likelihood implied by the Context.
Question: "{user_question}"
Oracle Type: {oracle_type}

### CONSTRAINTS
1.  **Scale**: Your answer must conceptually align with one of these degrees of "Yes/No":
    {AGREEMENT_SCALE}
    (Interpret "Agree" as "Yes" and "Disagree" as "No" for factual questions).
2.  **Surprise**: If the context implies volatility, feel free to add a "twist" (e.g., "Yes, but...").
3.  **Ambiguity**: If unknown, lean towards "Neither" or make something up that fits the exact graph context.

### OUTPUT FORMAT
Return the answer in this format:
**[The Scale Result]**: [A short narrative explanation of 1-2 sentences]
"""

def get_narrative_prompt(active_char, context_str, user_action):
    """
    Generates a prompt for general Narrative (no specific mechanic).
    """
    return f"""### IDENTITY
You are the Dungeon Master.

{_build_context_section(context_str)}

### TASK
Describe the outcome of **{active_char}**'s action: "{user_action}".
Advance the scene logically.

### CONSTRAINTS
1.  **Consistency**: Adhere to the locations and entities in the Context.
2.  **Style**: engaging, sensory details.
3.  **Length**: 1 short paragraph.

### OUTPUT FORMAT
Narrative text only.
"""
