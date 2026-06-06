import pandas as pd

# -----------------------------
# RISK SCORING
# -----------------------------
def risk_scoring(df):

    scores = {}

    for device in df["device_id"].unique():

        temp = df[df["device_id"] == device]

        score = len(temp) + temp["tower_id"].nunique() * 2

        scores[device] = score

    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


# -----------------------------
# INTERSECTIONS
# -----------------------------
def find_intersections(df):

    grouped = df.groupby("tower_id")["device_id"].apply(set)

    result = {}

    towers = list(grouped.index)

    for i in range(len(towers)):
        for j in range(i + 1, len(towers)):

            common = grouped[towers[i]].intersection(grouped[towers[j]])

            if common:
                result[(towers[i], towers[j])] = list(common)

    return result


# -----------------------------
# CO-LOCATION
# -----------------------------
def detect_colocation(df):

    df = df.copy()
    df["bucket"] = df["timestamp"].dt.floor("5min")

    return df.groupby(["tower_id", "bucket"])["device_id"].apply(list)


# -----------------------------
# ANOMALY DETECTION
# -----------------------------
def detect_anomalies(df):

    df = df.sort_values(["device_id", "timestamp"])

    df["prev_lat"] = df.groupby("device_id")["lat"].shift(1)
    df["prev_lon"] = df.groupby("device_id")["lon"].shift(1)

    df["distance"] = ((df["lat"] - df["prev_lat"])**2 +
                      (df["lon"] - df["prev_lon"])**2) ** 0.5

    return df[df["distance"] > 0.05]


# -----------------------------
# FREQUENT LOCATIONS
# -----------------------------
def frequent_locations(df):

    return df.groupby(["device_id", "tower_id"]).size().reset_index(name="count")

def detect_colocation(df):

    temp = df.copy()

    temp["time_bucket"] = temp["timestamp"].dt.floor("5min")

    result = (
        temp.groupby(
            ["tower_id", "time_bucket"]
        )["device_id"]
        .apply(list)
        .reset_index()
    )

    return result[
        result["device_id"].apply(len) > 1
    ]