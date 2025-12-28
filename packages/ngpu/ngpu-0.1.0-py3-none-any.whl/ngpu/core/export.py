import pandas as pd
from .loader import load_json


def to_dataframe():
    """
    Returns a flat DataFrame with columns:
    state, lga, ward, polling_unit
    """
    data = load_json("states_lgas_wards_pus.json")
    rows = []

    for state, lgas in data.items():
        for lga, wards in lgas.items():
            for ward, pus in wards.items():
                for pu in pus:
                    rows.append(
                        {
                            "state": state,
                            "lga": lga,
                            "ward": ward,
                            "polling_unit": pu,
                        }
                    )

    return pd.DataFrame(rows)