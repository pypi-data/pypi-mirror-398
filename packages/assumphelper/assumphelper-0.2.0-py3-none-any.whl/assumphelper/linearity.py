import statsmodels.api as sm
from statsmodels.stats.diagnostic import linear_reset
from .hypothesis import Hypothesis
from .utilities import prepare_vars, interpret_pval, plot_assump, load_output


class Linearity(Hypothesis):
    """
    Linearity assumption checker using:
    - Ramsey RESET test
    - Residuals vs Fitted plot
    """
    def fit(self):
        self.model.fit(self.x_cons, self.y)
        self.fitted, self.residuals = prepare_vars(self.model, self.x_cons, self.y)
        self.fit_done = True
        return self
        
   
    def test(self):
        """
        Perform Ramsey RESET test for linearity.
        """
        if not getattr(self, "fit_done", False):
            raise NotFittedError("Call fit() before test().")
            
        reset_model = sm.OLS(self.y,self.x_cons).fit()
        reset_result = linear_reset(reset_model, power=3,test_type="fitted")
        result_fstat, result_pval = reset_result.statistic, reset_result.pvalue
        print("RESET Test for Linearity")
        print(f"F-statistic: {result_fstat:.4f}      p-value: {result_pval:.4f}")
        print("\nInterpretation:\n")
        interpretation = interpret_pval(result_pval, "linearity")
        print("\n" + interpretation)
  
    def plot(self):
        
        """
        Plot linearity diagnostics.
        """
        figure, axes = plot_assump(self.fitted, self.residuals,"linearity")
        print("Interpretation Guide:\n")
        print(load_output("linplot_interpretation_guide.txt"))
        return figure, axes
