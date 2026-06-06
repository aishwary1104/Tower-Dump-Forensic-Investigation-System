import pandas as pd

def load_data(file_path):
    # Load CSV
    df = pd.read_csv(file_path)

    # Convert timestamp to proper datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Sort values for clean forensic flow
    df = df.sort_values(by=['device_id', 'timestamp'])

    # Reset index for cleanliness
    df = df.reset_index(drop=True)

    return df


def show_data(df):
    print("\n📡 Tower Dump Data Loaded:\n")
    print(df)


if __name__ == "__main__":
    file_path = "data.csv"

    df = load_data(file_path)
    show_data(df)