import hashlib
import pandas as pd


def hash_device_id(device_id):

    return hashlib.sha256(
        str(device_id).encode()
    ).hexdigest()[:12]


def anonymize_dataframe(df):

    temp = df.copy()

    temp["device_id"] = temp[
        "device_id"
    ].apply(
        hash_device_id
    )

    return temp


def create_mapping(df):

    mapping = []

    for device in df["device_id"].unique():

        mapping.append({

            "original_id": device,

            "hashed_id":
            hash_device_id(device)

        })

    return pd.DataFrame(mapping)