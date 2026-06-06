import pandas as pd


def build_markov_model(df, device_id):

    temp = (
        df[df["device_id"] == device_id]
        .sort_values("timestamp")
    )

    towers = list(
        temp["tower_id"]
    )

    transitions = {}

    for i in range(len(towers)-1):

        current = towers[i]
        nxt = towers[i+1]

        if current not in transitions:

            transitions[current] = {}

        if nxt not in transitions[current]:

            transitions[current][nxt] = 0

        transitions[current][nxt] += 1

    return transitions


def predict_next_tower(df, device_id):

    model = build_markov_model(
        df,
        device_id
    )

    temp = (
        df[df["device_id"] == device_id]
        .sort_values("timestamp")
    )

    if len(temp) < 2:

        return None

    current_tower = temp.iloc[-1]["tower_id"]

    if current_tower not in model:

        return None

    next_options = model[current_tower]

    predicted = max(
        next_options,
        key=next_options.get
    )

    confidence = (
        next_options[predicted]
        /
        sum(next_options.values())
    ) * 100

    return {

        "current_tower":
        current_tower,

        "predicted_tower":
        predicted,

        "confidence":
        round(confidence, 2)

    }