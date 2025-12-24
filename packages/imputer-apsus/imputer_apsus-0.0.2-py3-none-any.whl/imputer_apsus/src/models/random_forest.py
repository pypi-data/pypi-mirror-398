import pandas as pd
from sklearn.ensemble import RandomForestRegressor


def random_forest_imputer(df_nulls, col_to_impute, features) -> pd.DataFrame:
    """
    Impute missing values in the specified column using a Random Forest Regressor.

    Parameters:
        - df: DataFrame containing the data with missing values.
        - col_to_impute: Name of the column to be imputed.
        - features: List of column names to be used as features for the model.
        - original_atendimentos: Series with the original values of the atendimentos.
        - missing_indices_temp: Indices of the missing values to be imputed.


    """
    print("\nRANDOM FOREST IMPUTER, IS RUNNING ")
    df_rf = df_nulls.copy()

    features_rf = features
    X = df_rf[features_rf]

    mask_not_null = ~df_rf[col_to_impute].isna()
    X_train = X[mask_not_null]
    y_train = df_rf[col_to_impute][mask_not_null]

    model_rf = RandomForestRegressor(random_state=42, n_estimators=100)
    model_rf.fit(X_train, y_train)

    mask_null = df_rf[col_to_impute].isna()
    X_predict = X[mask_null]
    df_rf.loc[mask_null, col_to_impute] = model_rf.predict(X_predict)

    return df_rf
