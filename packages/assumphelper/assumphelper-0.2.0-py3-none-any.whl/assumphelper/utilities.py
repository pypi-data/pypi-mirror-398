"""
Utility Functions for AssumpHelp
"""
import numpy as np
import scipy.stats as sp
from scipy.stats import f
import statsmodels.api as sm
from sklearn.base import BaseEstimator, RegressorMixin
import matplotlib.pyplot as plt
import sklearn as sk
import os
from .check import check_sklearn_regressor, check_array

def prepare_vars(model: BaseEstimator, x:np.ndarray , y: np.ndarray):
    """
    Prepares fitted and residual values
    """ 
    check_sklearn_regressor(model)
    check_array(x,"x")
    check_array(y,"y")
    
    fitted = model.predict(x) #fitted
    
    if fitted.ndim == 1:
        fitted = fitted.reshape(-1, 1)
    if y.ndim == 1:
        y = y.reshape(-1, 1)

    residuals = y - fitted
    
    return fitted, residuals

def interpret_pval(pval , assump):
    if pval > 0.05:
        return f"If alpha = 0.05 and p-value > 0.05: Assumption of {assump.capitalize()} is NOT VIOLATED.\n"
    else:
        return f"If alpha = 0.05 and p-value < 0.05: Assumption of {assump.capitalize()} is VIOLATED.\n"

def plot_assump(fitted: np.ndarray, residuals: np.ndarray,assumption: str):

    # Linearity: Residuals vs Fitted
    if assumption.lower() == "linearity":
        figure, axes =  plt.subplots(figsize=(8,6))
        axes.scatter(fitted, residuals, alpha=0.5)
        axes.axhline(0, linestyle = "--")
        axes.set_xlabel("Fitted Values")
        axes.set_ylabel("Residuals")
        axes.set_title("Residuals vs Fitted Plot")

    # Homoscedasticity: Scale-Location Plot
    elif assumption.lower() == "homoscedasticity":
        std_resid = residuals / np.std(residuals)
        figure, axes = plt.subplots(figsize=(8,6))
        axes.scatter(fitted, np.sqrt(np.abs(std_resid)), alpha=0.5)
        axes.set_xlabel("Fitted Values")
        axes.set_ylabel("Sqrt(|Standardized Residuals|)")
        axes.set_title("Scale-Location Plot")


    # Normality: Q-Q Plot
    elif assumption.lower() == "normality":
        figure = plt.figure(figsize=(8,6))
        axes = figure.add_subplot(111)
        sm.qqplot(residuals, line='s', ax=axes)
        axes.set_title("Q-Q Plot")

    # Independence: 
    elif assumption.lower() == "independence":
        order = np.arange(1, len(residuals) + 1)
        figure, axes = plt.subplots(figsize=(8, 6))
        axes.scatter(order, residuals, alpha=0.5)
        axes.set_xlabel("Observation Order")
        axes.set_ylabel("Residuals")
        axes.set_title("Residuals vs Order Plot")
        
    else:
        raise ValueError("Invalid Assumption. Please double-check spelling.")


    plt.show()

    return figure, axes

def interpret_dw(dw_stat: float):
    """
    For Durbin-Watson Stat Comparitson
    """
    if 1.5 <= dw_stat <= 2.5:
        return("DW statistic close to 2 indicates no autocorrelation assumption NOT VIOLATED.")
    elif 1.5 > dw_stat:
        return("DW statistic significantly less than 2 indicates positive autocorrelation VIOLATED.")
    elif dw_stat > 2.5:
        return("DW statistic significantly greater than 2 indicates negative autocorrelation VIOLATED.")


def load_output(path):
    with open(path, "r") as f:
        return f.read()
