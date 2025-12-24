class InvalidModelError(TypeError):
    """Raised when the model is not a scikit-learn estimator."""
    pass

class NotFittedError(RuntimeError):
    """Raised when the model has not been fitted yet."""
    pass

class InvalidArrayError(TypeError):
    """Raised when an input is not a valid NumPy array."""
    pass
    
class UndefinedTestError(RuntimeError):
    """Raised when a statistical test is undefined (e.g., zero residual variance)."""
    pass
