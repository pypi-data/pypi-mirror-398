import sys
import traceback


class AppException(Exception):

    def __init__(self, error_message, wrapping_function_name=None):
        error_message = str(error_message)
        super().__init__(error_message)
        exc_type, _, exc_traceback = sys.exc_info()

        # Handle case where there's no active exception context
        if exc_traceback is not None:
            tb = traceback.extract_tb(exc_traceback)
            if tb:
                last_call = tb[-1]
                self.filename = last_call.filename
                self.lineno = last_call.lineno
                self.function_name = last_call.name
            else:
                self.filename = "Unknown"
                self.lineno = 0
                self.function_name = "Unknown"
        else:
            # No active exception context - this happens when AppException is created manually
            self.filename = "Unknown"
            self.lineno = 0
            self.function_name = "Unknown"

        self.wrapping_function_name = wrapping_function_name
        self.error_message = error_message
        self.error_type = exc_type if exc_type else type(None)

    def __str__(self):
        return (
            f"({self.error_type.__name__})\n"
            f"Wrapping function name:    {self.wrapping_function_name}\n"
            f"Error thrown by:           {self.function_name}\n"
            f"Filename:                  {self.filename}\n"
            f"Line no:                   {self.lineno}\n"
            f"-----------------------\n"
            f"{self.error_message}"
        )

    def to_dict(self):
        return {
            "wrapping_function_name": self.wrapping_function_name,
            "function_name": self.function_name,
            "filename": self.filename,
            "lineno": self.lineno,
            "error_type": self.error_type.__name__,
            "error_message": self.error_message,
        }


class CriticalException(Exception):
    """Exception raised for critical errors."""

    def __init__(self, message="Critical error"):
        super().__init__(message, "CriticalException")
