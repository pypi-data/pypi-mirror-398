import pandas as pd

from .src.models.random_forest import random_forest_imputer
from .src.features.encode import generate_features
from .src.features.normalize import standard_scale


def impute_dataframe(
    df: pd.DataFrame,
    col_to_impute: str = "Atendimentos Totais",
    method: str = "random_forest",
) -> pd.DataFrame:
    """
    Impute missing values in a DataFrame with exactly this columns ["APS", "Data", "Atendimentos Totais"].

    Parameters:
        df: Input DataFrame with missing values.
        col_to_impute: Column name to impute (default: "Atendimentos Totais").
        method: Imputation method ("random_forest" supported).
        features: List of feature columns for the model.
        features_to_normalize: List of columns to apply feature normalization.

    """

    df = df.copy()
    df = generate_features(df)
    features = [
        "contagem_dias",
        "aps_encoded",
        "mes_sin",
        "mes_cos",
        "trimestre",
        "valor_mes_anterior",
        "valor_12_meses_atras",
        "media_movel_3_meses",
        "desvio_movel_3_meses",
        "media_movel_6_meses",
        "desvio_movel_6_meses",
        "estacao_encoded",
    ]

    features_to_normalize = [
        "contagem_dias",
        "valor_mes_anterior",
        "valor_12_meses_atras",
        "media_movel_3_meses",
        "desvio_movel_3_meses",
        "media_movel_6_meses",
        "desvio_movel_6_meses",
    ]

    # Apply normalization
    df = standard_scale(df, features_to_normalize)

    if method == "random_forest":

        df_imputed = random_forest_imputer(
            df_nulls=df, col_to_impute=col_to_impute, features=features
        )
        # clean columns
        result = df_imputed.drop(columns=features + ["ano_encoded"])
        return result

    else:
        raise NotImplementedError(
            f"Method '{method}' not implemented. Supported: 'random_forest'"
        )
