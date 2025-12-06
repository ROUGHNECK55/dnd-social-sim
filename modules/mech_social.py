
import random

EFFECTS_MATRIX = [
    {"intimidation": "{l} is deeply offended by {s}'s aggression and immediately becomes hostile or mocks the attempt.", "performance": "{l} finds {s} utterly obnoxious and actively tries to leave the conversation.", "deception": "{l} sees right through {s}, convinced they are lying maliciously.", "persuasion": "{l} completely misinterprets {s}'s logic, taking the suggestion as an insult."},
    {"intimidation": "{l} feels disrespected by {s} and digs their heels in, refusing to cooperate.", "performance": "{l} is unimpressed and dismissive of {s}'s antics.", "deception": "{l} distrusts {s} and is suspicious of their motives.", "persuasion": "{l} simply doesn't understand {s}'s point and gets frustrated."},
    {"intimidation": "{l} feels {s} is posturing but isn't truly afraid, leading to an awkward standoff.", "performance": "{l} avoids making eye contact, finding {s}'s behavior slightly cringe-worthy.", "deception": "{l} senses {s} is withholding information and becomes guarded.", "persuasion": "{l} is confused by the details and remains unconvinced by {s}."},
    {"intimidation": "{l} sees {s} as an equal; they are not scared, but they are listening.", "performance": "{l} is indifferent to {s}, neither entertained nor annoyed.", "deception": "{l} is neutral, neither believing nor disbelieving {s} fully.", "persuasion": "{l} understands the surface level of {s}'s request but needs more convincing."},
    {"intimidation": "{l} respects {s}'s strength and feels compelled to listen.", "performance": "{l} is drawn in by {s}'s charisma and pays close attention.", "deception": "{s}'s story seems plausible enough to {l}.", "persuasion": "{l} feels enlightened by {s}'s argument and is inclined to agree."},
    {"intimidation": "{l} is thoroughly cowed by {s} and feels a strong urge to submit to the demand.", "performance": "{l} is captivated, actively seeking {s}'s approval or company.", "deception": "{l} trusts {s} implicitly, swallowing the lie whole.", "persuasion": "{l} fully understands and empathizes with {s}'s intent."},
    {"intimidation": "{l} is terrified or awestruck, viewing {s} as a dominant force of nature.", "performance": "{l} becomes an instant fan, hanging on {s}'s every word.", "deception": "{l} believes {s} completely, perhaps even defending the lie to others.", "persuasion": "{l} experiences a shift in perspective, expanding their understanding to align with {s}."},
]

STANDARD_RANGES = [(-100, -7), (-6, -5), (-4, -2), (-1, 0), (1, 2), (3, 5), (6, 100)]
PERSUASION_RANGES = [(0, 9), (10, 14), (15, 19), (20, 24), (25, 29), (30, 34), (35, 200)]

def roll_d20(state, use_min_10):
    """
    Handles Advantage/Disadvantage AND Minimum 10 logic.
    If use_min_10 is True, the die rolls between 10 and 20.
    """
    low = 10 if use_min_10 else 1
    
    r1 = random.randint(low, 20)
    r2 = random.randint(low, 20)
    
    if state == "Advantage":
        return max(r1, r2)
    elif state == "Disadvantage":
        return min(r1, r2)
    else:
        return r1

def get_standard_text(score, skill_type, s_name, l_name):
    index = 3 
    for i, (min_val, max_val) in enumerate(STANDARD_RANGES):
        if min_val <= score <= max_val:
            index = i
            break
    return EFFECTS_MATRIX[index][skill_type].format(s=s_name, l=l_name)

def get_persuasion_text(score, s_name, l_name):
    index = 3 
    for i, (min_val, max_val) in enumerate(PERSUASION_RANGES):
        if min_val <= score <= max_val:
            index = i
            break
    return EFFECTS_MATRIX[index]["persuasion"].format(s=s_name, l=l_name)

def calculate_social_outcomes(speaker, listener, s_state, l_state, min_flags, l_min_insight=False):
    """
    Calculates the detailed social outcomes based on character stats and dice rolls.
    min_flags: dict with keys 'int', 'perf', 'dec', 'pers' (booleans)
    """
    rolls = {}
    rolls['int'] = roll_d20(s_state, min_flags.get('int', False))
    rolls['perf'] = roll_d20(s_state, min_flags.get('perf', False))
    rolls['dec'] = roll_d20(s_state, min_flags.get('dec', False))
    rolls['pers'] = roll_d20(s_state, min_flags.get('pers', False))
    rolls['insight'] = roll_d20(l_state, l_min_insight)

    l_insight_total = listener.skills['Insight'].total + rolls['insight']
    
    score_int = (speaker.skills['Intimidation'].total + rolls['int']) - l_insight_total
    score_perf = (speaker.skills['Performance'].total + rolls['perf']) - l_insight_total
    score_dec = (speaker.skills['Deception'].total + rolls['dec']) - l_insight_total
    score_pers = (speaker.skills['Persuasion'].total + rolls['pers']) + l_insight_total 
    
    outcomes = {
        'int': get_standard_text(score_int, 'intimidation', speaker.name, listener.name),
        'perf': get_standard_text(score_perf, 'performance', speaker.name, listener.name),
        'dec': get_standard_text(score_dec, 'deception', speaker.name, listener.name),
        'pers': get_persuasion_text(score_pers, speaker.name, listener.name),
        'scores': {
            'int': score_int,
            'perf': score_perf,
            'dec': score_dec,
            'pers': score_pers
        },
        'rolls': rolls
    }
    return outcomes
