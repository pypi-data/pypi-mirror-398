import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from .hypothesis import Hypothesis
from .utilities import prepare_vars, interpret_pval, plot_assump, load_output
from .check import check_resid_var

class Homoscedasticity(Hypothesis):
    """
    Homoscedasticity checker using:
    - Breusch-Pagan test
    - Scale-Location plot
    """
    def fit(self):
        self.model.fit(self.x_cons, self.y)
        self.fitted, self.residuals = prepare_vars(self.model, self.x_cons, self.y)
        self.fit_done = True
        return self
   
    def test(self):
        """
        Perform Breusch-Pagan test.
        """
        if not getattr(self, "fit_done", False):
            raise NotFittedError("Call fit() before test().")
             
        check_resid_var(self.residuals)
        bp_test = het_breuschpagan(self.residuals, self.x_cons)
        bp_stat, bp_pval, _, _ = bp_test
        self.result = bp_pval
        print("Breusch-Pagan Test for Homoscedasticity")
        print(f"BP-statistic: {bp_stat:.4f}      p-value: {bp_pval:.4f}")
        print("\nInterpretation:\n")
        interpretation = interpret_pval(bp_pval, "homoscedasticity")
        print("\n" + interpretation)

    def plot(self):
        """
        Plot homoscedasticity diagnostics.
        """
        figure, axes = plot_assump(self.fitted, self.residuals, "homoscedasticity")
        print("Interpretation Guide:\n")
        print(load_output("homplot_interpretation_guide.txt"))
        return figure, axes
