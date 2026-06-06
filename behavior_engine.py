import pandas as pd


def identify_home_tower(df, device_id):

    temp = df[df["device_id"] == device_id].copy()

    if len(temp) == 0:
        return None

    temp["hour"] = temp["timestamp"].dt.hour

    night_data = temp[
        (temp["hour"] >= 21)
        | (temp["hour"] <= 6)
    ]

    if len(night_data) == 0:
        return None

    return night_data["tower_id"].mode()[0]


def identify_work_tower(df, device_id):

    temp = df[df["device_id"] == device_id].copy()

    if len(temp) == 0:
        return None

    temp["hour"] = temp["timestamp"].dt.hour

    work_data = temp[
        (temp["hour"] >= 9)
        & (temp["hour"] <= 17)
    ]

    if len(work_data) == 0:
        return None

    return work_data["tower_id"].mode()[0]


def active_hours(df, device_id):

    temp = df[df["device_id"] == device_id]

    if len(temp) == 0:
        return None

    hourly = (
        temp["timestamp"]
        .dt.hour
        .value_counts()
        .sort_index()
    )

    return hourly


def routine_routes(df, device_id):

    temp = (
        df[df["device_id"] == device_id]
        .sort_values("timestamp")
    )

    route = list(temp["tower_id"])

    return " → ".join(route)


def behavior_profile(df, device_id):

    temp = df[df["device_id"] == device_id]

    if len(temp) == 0:
        return None

    return {

        "home_tower":
        identify_home_tower(
            df,
            device_id
        ),

        "work_tower":
        identify_work_tower(
            df,
            device_id
        ),

        "total_towers":
        temp["tower_id"].nunique(),

        "total_records":
        len(temp),

        "route":
        routine_routes(
            df,
            device_id
        )

    }