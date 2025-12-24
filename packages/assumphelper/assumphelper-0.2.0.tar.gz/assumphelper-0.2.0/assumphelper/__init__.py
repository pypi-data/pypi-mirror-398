"""
AssumpHelp init
"""

from .hypothesis import Hypothesis
from .linearity import Linearity
from .homoscedasticity import Homoscedasticity
from .normality import Normality
from .independence import Independence

from .utilities import (
    prepare_vars,
    interpret_pval,
    interpret_dw,
    plot_assump,
    load_output
)

from .exceptions import InvalidModelError, NotFittedError, InvalidArrayError, UndefinedTestError
from .check import check_sklearn_regressor, check_array, check_resid_var, check_shapiro_resids, check_dw_resids


__all__ = [
    "InvalidModelError",
    "NotFittedError",
    "InvalidArrayError",
    "UndefinedTestError",
    "check_sklearn_regressor",
    "check_array",
    "check_resid_var",
    "check_shapiro_resids",
    "check_dw_resids",
    "Hypothesis",
    "Linearity",
    "Homoscedasticity",
    "Normality",
    "Independence",
    "prepare_vars",
    "interpret_pval",
    "plot_assump",
    "interpret_dw",
    "load_output",
]
