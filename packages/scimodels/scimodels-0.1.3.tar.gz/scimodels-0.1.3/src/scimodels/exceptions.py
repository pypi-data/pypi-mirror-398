from scimodels.abstract import Model

class DependencyError(Exception):
    """Error raised when a Dependency is not installed"""
    def __init__(self, dep_name):
        message = f"""Dependency '{dep_name}' is not installed. Please try running: 
        
        pip install {dep_name}
        """
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"
    
class MissingParameterError(Exception):
    def __init__(self, class_: Model, param_name: str):
        message = f"Class {class_.__class__.__name__} instance missing required parameter '{param_name}'."
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"