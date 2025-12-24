import pandas as pd
import numpy as np


def generate_features(df: pd.DataFrame):
    """
    Generate additional features for the dataset.

    Parameters:
      - df: DataFrame containing the initial columns ["APS", "Data", "Atendimentos Totais"].

    Returns:
      - DataFrame with new features added.
    """
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y")
    df = df.sort_values(["APS", "Data"]).reset_index(drop=True)

    df["ano"] = df["Data"].dt.year
    df["ano_encoded"] = df["ano"].astype("category").cat.codes
    
    df["mes"] = df["Data"].dt.month
    df["trimestre"] = df["Data"].dt.quarter
    df["contagem_dias"] = (df["Data"] - df["Data"].min()).dt.days

    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)

    df["aps_encoded"] = df["APS"].astype("category").cat.codes
    

    def obter_estacao(m):
        if m in [12, 1, 2]:
            return 0
        if m in [3, 4, 5]:
            return 1
        if m in [6, 7, 8]:
            return 2
        return 3

    df["estacao_encoded"] = df["mes"].apply(obter_estacao)

    df_aux = df[["APS", "ano", "mes", "Atendimentos Totais"]].copy()
    df_aux["ano_alvo"] = df_aux["ano"] + 1

    df = df.merge(
        df_aux.drop(columns=["ano"]),
        left_on=["APS", "ano", "mes"],
        right_on=["APS", "ano_alvo", "mes"],
        how="left",
        suffixes=("", "_temp"),
    )
    df.rename(
        columns={"Atendimentos Totais_temp": "valor_12_meses_atras"}, inplace=True
    )

    df["valor_mes_anterior"] = df.groupby("APS")["Atendimentos Totais"].shift(1)
    # this can be useful for short seasonal trends
    df["media_movel_3_meses"] = df.groupby("APS")["Atendimentos Totais"].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    df["desvio_movel_3_meses"] = (
        df.groupby("APS")["Atendimentos Totais"]
        .transform(lambda x: x.rolling(window=3, min_periods=1).std())
        .fillna(0)
    )
    # this can be useful for medium seasonal trends
    df["media_movel_6_meses"] = df.groupby("APS")["Atendimentos Totais"].transform(
        lambda x: x.rolling(window=6, min_periods=1).mean()
    )
    df["desvio_movel_6_meses"] = (
        df.groupby("APS")["Atendimentos Totais"]
        .transform(lambda x: x.rolling(window=6, min_periods=1).std())
        .fillna(0)
    )

    df.drop(columns=["ano", "mes", "ano_alvo"], inplace=True)

    return df
