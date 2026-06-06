import pandas as pd


def calculate_threat_score(df):

    results = []

    for device in df["device_id"].unique():

        temp = df[df["device_id"] == device]

        # -------------------------
        # Mobility Score
        # -------------------------

        towers_visited = temp["tower_id"].nunique()

        mobility_score = min(
            towers_visited * 5,
            30
        )

        # -------------------------
        # Activity Score
        # -------------------------

        activity_score = min(
            len(temp),
            20
        )

        # -------------------------
        # Night Activity
        # -------------------------

        night_activity = temp[
            temp["timestamp"].dt.hour.between(0, 5)
        ]

        night_score = min(
            len(night_activity) * 2,
            20
        )

        # -------------------------
        # Tower Switching
        # -------------------------

        switches = (
            temp["tower_id"]
            != temp["tower_id"].shift()
        ).sum()

        switch_score = min(
            switches * 2,
            20
        )

        # -------------------------
        # Final Score
        # -------------------------

        total_score = (
            mobility_score
            + activity_score
            + night_score
            + switch_score
        )

        risk = "LOW"

        if total_score >= 70:
            risk = "HIGH"

        elif total_score >= 40:
            risk = "MEDIUM"

        results.append({

            "device_id": device,

            "threat_score": total_score,

            "risk_level": risk,

            "towers_visited": towers_visited,

            "records": len(temp),

            "night_activity": len(night_activity),

            "tower_switches": switches

        })

    return pd.DataFrame(results).sort_values(
        "threat_score",
        ascending=False
    )