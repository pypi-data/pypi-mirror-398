import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from .hypothesis import Hypothesis
from .utilities import prepare_vars, interpret_dw, plot_assump, load_output
from .check import check_dw_resids


class Independence(Hypothesis):  
    """
    Independence checker using:
    - Durbin-Watson statistic
    - Residuals vs Order plot
    """
    def fit(self):
        self.model.fit(self.x_cons, self.y)
        self.fitted, self.residuals = prepare_vars(self.model, self.x_cons, self.y)
        self.fit_done = True
        return self
        
    def test(self):
        """
        Perform Durbin-Watson autocorrelation test.
        """
        if not getattr(self, "fit_done", False):
            raise NotFittedError("Call fit() before test().")

        check_dw_resids(self.residuals)
        dw_stat = durbin_watson(self.residuals.ravel())
        self.result = dw_stat
        print("Durbin-Watson Test for Independence")
        print(f"DW-statistic: {dw_stat:.4f}")
        print("\nInterpretation:\n")
        interpretation = interpret_dw(dw_stat)
        print("\n" + interpretation)
   
    def plot(self):
        """
        Plot residuals vs observation order.
        """
        figure, axes = plot_assump(self.fitted,self.residuals, "independence")
        print("\nInterpretation:\n")
        print(load_output("indepplot_interpretation_guide.txt"))
        return figure, axes
