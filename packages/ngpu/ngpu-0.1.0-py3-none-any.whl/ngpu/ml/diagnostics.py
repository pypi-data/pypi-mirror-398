class CoverageReport:
    """
    Diagnose hierarchical coverage and missingness.
    """

    def __init__(self, df, key="polling_unit"):
        self.df = df
        self.key = key

    def missing_rate(self):
        return self.df[self.key].isna().mean()

    def coverage_by_state(self):
        return (
            self.df.groupby("state")[self.key]
            .apply(lambda x: x.notna().mean())
            .reset_index(name="coverage_rate")
        )