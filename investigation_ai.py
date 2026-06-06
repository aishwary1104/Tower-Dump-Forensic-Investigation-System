def generate_case_summary(

    device_id,
    threat_score,
    profile,
    prediction

):

    summary = f"""

INVESTIGATION SUMMARY

Device:
{device_id}

Threat Score:
{threat_score}

Likely Residence Tower:
{profile['home_tower']}

Likely Workplace Tower:
{profile['work_tower']}

Unique Towers:
{profile['total_towers']}

Predicted Next Tower:
{prediction['predicted_tower'] if prediction else 'Unknown'}

Analyst Assessment:

This device shows movement
across multiple towers and
has established behavioral
patterns.

Further investigation
recommended if threat
score exceeds 70.

"""

    return summary