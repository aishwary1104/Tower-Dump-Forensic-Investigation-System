import pandas as pd


def relationship_strength(df):

    temp = df.copy()

    temp["time_bucket"] = temp["timestamp"].dt.floor("5min")

    colocations = (
        temp.groupby(
            ["tower_id", "time_bucket"]
        )["device_id"]
        .apply(list)
        .reset_index()
    )

    relationships = []

    for _, row in colocations.iterrows():

        devices = row["device_id"]

        if len(devices) < 2:
            continue

        for i in range(len(devices)):
            for j in range(i + 1, len(devices)):

                relationships.append(
                    (
                        devices[i],
                        devices[j]
                    )
                )

    if not relationships:

        return pd.DataFrame()

    rel_df = pd.DataFrame(
        relationships,
        columns=[
            "device_a",
            "device_b"
        ]
    )

    rel_df["pair"] = rel_df.apply(
        lambda x: tuple(
            sorted(
                [x["device_a"], x["device_b"]]
            )
        ),
        axis=1
    )

    result = (
        rel_df.groupby("pair")
        .size()
        .reset_index(name="meetings")
    )

    result[["device_a", "device_b"]] = pd.DataFrame(
        result["pair"].tolist(),
        index=result.index
    )

    result["relationship_strength"] = (
        result["meetings"]
        / result["meetings"].max()
    ) * 100

    return result.sort_values(
        "relationship_strength",
        ascending=False
    )


def common_towers(df, device1, device2):

    towers1 = set(
        df[df["device_id"] == device1]["tower_id"]
    )

    towers2 = set(
        df[df["device_id"] == device2]["tower_id"]
    )

    return list(
        towers1.intersection(towers2)
    )


def common_time_windows(df, device1, device2):

    temp = df.copy()

    temp["time_bucket"] = temp["timestamp"].dt.floor("5min")

    result = []

    grouped = (
        temp.groupby(
            ["tower_id", "time_bucket"]
        )["device_id"]
        .apply(list)
        .reset_index()
    )

    for _, row in grouped.iterrows():

        devices = row["device_id"]

        if (
            device1 in devices
            and
            device2 in devices
        ):

            result.append({

                "tower":
                row["tower_id"],

                "time":
                row["time_bucket"]

            })

    return pd.DataFrame(result)