"""
Validation-specific exceptions for PyHelios.

Provides ValidationError that extends HeliosInvalidArgumentError with
enhanced error messaging and context information.
"""

class ValidationError(ValueError):
    """
    Validation-specific error with standardized messaging.
    
    Raised when parameter validation fails, with clear error messages that include:
    - Parameter name and expected type/range
    - Actual value provided and its type
    - Actionable solution or correct usage example
    
    Following PyHelios's fail-fast philosophy, validation errors are raised
    immediately at API boundaries before reaching C++ code.
    """
    
    def __init__(self, message: str, param_name: str = None, function_name: str = None, 
                 expected_type: str = None, actual_value=None):
        """
        Initialize validation error with enhanced context.
        
        Args:
            message: Primary error message
            param_name: Name of the parameter that failed validation
            function_name: Name of the function where validation failed
            expected_type: Expected type or range description
            actual_value: The actual value that failed validation
        """
        # Build enhanced error message with context
        enhanced_message = message
        
        if function_name:
            enhanced_message = f"{function_name}(): {enhanced_message}"
            
        if param_name and expected_type and actual_value is not None:
            enhanced_message += f" (Parameter '{param_name}' expected {expected_type}, got {actual_value} of type {type(actual_value).__name__})"
        elif param_name:
            enhanced_message += f" (Parameter: '{param_name}')"
            
        super().__init__(enhanced_message)
        
        # Store context for programmatic access
        self.param_name = param_name
        self.function_name = function_name
        self.expected_type = expected_type
        self.actual_value = actual_value


def create_validation_error(message: str, param_name: str = None, 
                          function_name: str = None, expected_type: str = None, 
                          actual_value=None, suggestion: str = None) -> ValidationError:
    """
    Factory function for creating ValidationError with consistent formatting.
    
    Args:
        message: Core error message
        param_name: Parameter name that failed
        function_name: Function where validation failed
        expected_type: Description of expected type/range
        actual_value: Actual value provided
        suggestion: Helpful suggestion for fixing the error
        
    Returns:
        ValidationError with enhanced message
    """
    full_message = message
    if suggestion:
        full_message += f" {suggestion}"
        
    return ValidationError(
        full_message,
        param_name=param_name,
        function_name=function_name,
        expected_type=expected_type,
        actual_value=actual_value
    )