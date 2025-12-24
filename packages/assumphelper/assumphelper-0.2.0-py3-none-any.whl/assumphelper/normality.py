import statsmodels.api as sm
import scipy.stats as sp
from .hypothesis import Hypothesis
from .utilities import prepare_vars, interpret_pval, plot_assump, load_output
from .check import check_shapiro_resids

class Normality(Hypothesis): 
    """
    Normality checker using:
    - Shapiro-Wilk test
    - Q-Q plot
    """
    def fit(self):
        self.model.fit(self.x_cons, self.y)
        self.fitted, self.residuals = prepare_vars(self.model, self.x_cons, self.y)
        self.fit_done = True
        return self
   
    def test(self):
        """
        Perform Shapiro-Wilk test.
        """
        if not getattr(self, "fit_done", False):
            raise NotFittedError("Call fit() before test().")

        check_shapiro_resids(self.residuals)
        shapiro_stat, shapiro_pval = sp.shapiro(self.residuals)
        self.result = shapiro_pval
        print("Shapiro-Wilk Test for Normality")
        print(f"W-statistic: {shapiro_stat:.4f}      p-value: {shapiro_pval:.4f}")
        print("\nInterpretation:\n")
        interpretation = interpret_pval(shapiro_pval, "normality")
        print("\n" + interpretation)
        
    
    def plot(self):
        """
        Plot Q-Q plot.
        """
        figure, axes = plot_assump(self.fitted, self.residuals, "normality")
        print("Interpretation Guide:\n")
        print(load_output("normplot_interpretation_guide.txt"))
        return figure, axes
