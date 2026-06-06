import pandas as pd
from sklearn.ensemble import IsolationForest


def ml_anomaly_detection(df):

    device_features = []

    for device in df["device_id"].unique():

        temp = df[df["device_id"] == device]

        towers = temp["tower_id"].nunique()

        records = len(temp)

        avg_lat = temp["lat"].mean()

        avg_lon = temp["lon"].mean()

        active_hours = (
            temp["timestamp"]
            .dt.hour
            .nunique()
        )

        device_features.append({

            "device_id": device,
            "towers": towers,
            "records": records,
            "avg_lat": avg_lat,
            "avg_lon": avg_lon,
            "active_hours": active_hours

        })

    features_df = pd.DataFrame(device_features)

    X = features_df[[
        "towers",
        "records",
        "avg_lat",
        "avg_lon",
        "active_hours"
    ]]

    model = IsolationForest(
        contamination=0.15,
        random_state=42
    )

    features_df["anomaly"] = model.fit_predict(X)

    features_df["anomaly_score"] = (
        model.decision_function(X)
    )

    features_df["anomaly"] = (
        features_df["anomaly"]
        .map({
            1: "Normal",
            -1: "Suspicious"
        })
    )

    return features_df.sort_values(
        "anomaly_score"
    )