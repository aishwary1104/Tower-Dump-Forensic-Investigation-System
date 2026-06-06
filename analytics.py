import pandas as pd
from math import sqrt

def device_intelligence(df, device_id):

    data = df[df["device_id"] == device_id]

    if len(data) == 0:
        return None

    return {
        "first_seen": data["timestamp"].min(),
        "last_seen": data["timestamp"].max(),
        "total_records": len(data),
        "towers_visited": data["tower_id"].nunique(),
        "favorite_tower": data["tower_id"].mode()[0]
    }


def detect_speed_anomalies(df):

    anomalies = []

    for device in df["device_id"].unique():

        temp = (
            df[df["device_id"] == device]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        for i in range(1, len(temp)):

            dlat = temp.loc[i, "lat"] - temp.loc[i-1, "lat"]
            dlon = temp.loc[i, "lon"] - temp.loc[i-1, "lon"]

            distance_km = sqrt(dlat**2 + dlon**2) * 111

            time_hours = (
                temp.loc[i, "timestamp"]
                - temp.loc[i-1, "timestamp"]
            ).total_seconds() / 3600

            if time_hours <= 0:
                continue

            speed = distance_km / time_hours

            if speed > 500:

                anomalies.append({
                    "device_id": device,
                    "speed_kmh": round(speed, 2),
                    "from_tower": temp.loc[i-1, "tower_id"],
                    "to_tower": temp.loc[i, "tower_id"]
                })

    return pd.DataFrame(anomalies)