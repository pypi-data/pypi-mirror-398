from sklearn.preprocessing import MinMaxScaler, StandardScaler


def standard_scale(df, features_to_normalize):
    """
    Apply Standard Scaling to the specified features of the DataFrame.

    Parameters:
        - df: DataFrame containing the features to be normalized.
        - features_to_normalize: List of column names to be normalized.

    """
    scaler_standard = StandardScaler()
    df[features_to_normalize] = scaler_standard.fit_transform(df[features_to_normalize])

    return df


def min_max_scale(df, features_to_normalize):
    """
    Apply Min-Max Scaling to the specified features of the DataFrame.

    Parameters:
        - df: DataFrame containing the features to be normalized.
        - features_to_normalize: List of column names to be normalized.
    """
    scaler_minmax = MinMaxScaler()
    df[features_to_normalize] = scaler_minmax.fit_transform(df[features_to_normalize])

    return df
