import pandas as pd


def hierarchy_presence_features(df: pd.DataFrame):
    """
    Generates binary indicators for hierarchical completeness.
    """
    return pd.DataFrame(
        {
            "has_state": df["state"].notna().astype(int),
            "has_lga": df["lga"].notna().astype(int),
            "has_ward": df["ward"].notna().astype(int),
            "has_polling_unit": df["polling_unit"].notna().astype(int),
        }
    )