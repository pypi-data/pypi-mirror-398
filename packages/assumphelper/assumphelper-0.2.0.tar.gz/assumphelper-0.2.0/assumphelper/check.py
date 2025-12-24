from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_is_fitted
import numpy as np
from .exceptions import InvalidModelError, NotFittedError, InvalidArrayError, UndefinedTestError

def check_sklearn_regressor(model):
    if not isinstance(model, BaseEstimator):
        raise InvalidModelError("Model must be a scikit-learn estimator.")
    if not isinstance(model, RegressorMixin):
        raise InvalidModelError("Model must be a scikit-learn regressor.")
    try:
        check_is_fitted(model)
    except Exception:
        raise NotFittedError("Model must be fitted before diagnostics.")

def check_array(arr, name="array"):
    if not isinstance(arr, np.ndarray):
        raise InvalidArrayError(f"{name} must be a NumPy array.")

def check_resid_var(residuals):
    if np.var(residuals) == 0:
        raise UndefinedTestError(
            "Breusch–Pagan test is undefined because residual variance is zero "
            "(perfect model fit)."
        )
def check_shapiro_resids(residuals):
    n = len(residuals)

    if n < 3:
        raise UndefinedTestError(
            "Shapiro–Wilk test requires at least 3 observations."
        )

    if np.var(residuals) == 0:
        raise UndefinedTestError(
            "Shapiro–Wilk test is undefined because residuals are constant."
        )
def check_dw_resids(residuals):
    n = len(residuals)

    if n < 2:
        raise UndefinedTestError(
            "Durbin–Watson test requires at least 2 residuals."
        )

    if np.var(residuals) == 0:
        raise UndefinedTestError(
            "Durbin–Watson test is undefined because residuals are constant "
            "(perfect model fit)."
        )
