import pandas as pd

def build_device_timelines(df):
    timelines = {}

    # Group by device
    grouped = df.groupby("device_id")

    for device, group in grouped:
        sorted_group = group.sort_values(by="timestamp")
        timeline = list(sorted_group["tower_id"])
        timelines[device] = timeline

    return timelines


def print_timelines(timelines):
    print("\n🧭 Device Movement Timelines:\n")

    for device, path in timelines.items():
        print(f"{device} → {' → '.join(path)}")


if __name__ == "__main__":
    df = pd.read_csv("data.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    timelines = build_device_timelines(df)
    print_timelines(timelines)