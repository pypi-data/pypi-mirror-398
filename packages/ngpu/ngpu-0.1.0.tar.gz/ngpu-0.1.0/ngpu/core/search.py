from rapidfuzz import process
from .index import Index


class Search:
    """Fuzzy search utilities for hierarchical names."""

    @staticmethod
    def states(query, limit=5):
        return process.extract(query, Index.states(), limit=limit)

    @staticmethod
    def lgas(state, query, limit=5):
        return process.extract(query, Index.lgas(state), limit=limit)