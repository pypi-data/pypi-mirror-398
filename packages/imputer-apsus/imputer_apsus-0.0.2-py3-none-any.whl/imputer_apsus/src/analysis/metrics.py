import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error


def evaluate_imputation(true_values, imputed_values):
    """
    Evaluate imputation performance using MSE, RMSE, and MAE metrics.

    Parameters:
      - true_values: Series or array of true values.
      - imputed_values: Series or array of imputed values.
      - method: String indicating the imputation method used.
    """
    mse = mean_squared_error(true_values, imputed_values)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(true_values, imputed_values)

    return mse, rmse, mae
