from sklearn.preprocessing import OrdinalEncoder


class PollingUnitEncoder:
    """
    Ordinal encoder for hierarchical categorical features.
    """

    def __init__(self, level="polling_unit"):
        self.level = level
        self.encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value", unknown_value=-1
        )

    def fit(self, df):
        self.encoder.fit(df[[self.level]])
        return self

    def transform(self, df):
        return self.encoder.transform(df[[self.level]])

    def fit_transform(self, df):
        return self.fit(df).transform(df)