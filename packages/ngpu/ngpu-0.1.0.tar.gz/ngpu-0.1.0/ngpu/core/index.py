from .loader import load_json

_DATA = load_json("states_lgas_wards_pus.json")


class Index:
    """Hierarchical access to Nigeria polling unit data."""

    @staticmethod
    def states():
        return list(_DATA.keys())

    @staticmethod
    def lgas(state: str):
        return list(_DATA.get(state, {}).keys())

    @staticmethod
    def wards(state: str, lga: str):
        return list(_DATA.get(state, {}).get(lga, {}).keys())

    @staticmethod
    def polling_units(state: str, lga: str, ward: str):
        return _DATA.get(state, {}).get(lga, {}).get(ward, [])