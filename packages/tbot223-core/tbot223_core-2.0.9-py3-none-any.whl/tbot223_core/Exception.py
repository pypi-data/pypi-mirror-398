# external modules
import sys
import os
import platform
import time
import traceback
from typing import Any

# internal modules
from tbot223_core.Result import Result

class ExceptionTracker():
    """
    The ExceptionTracker class provides functionality to track location information when exceptions occur and return related information.
    
    1. Exception Location Tracking: Provides functionality to track where exceptions occur and return related information.
        - get_exception_location: Returns the location where the exception occurred.

    2. Exception Information Tracking: Provides functionality to track exception information and return related information.
        - get_exception_info: Returns information about the exception.
    """

    def __init__(self):
        # Cache system information
        # Safely get current working directory
        try:
            cwd = os.getcwd()
        except Exception:
            cwd = "<Permission Denied or Unavailable>"

        self._system_info = {
            "OS": platform.system(),
            "OS_version": platform.version(),
            "Release": platform.release(),
            "Architecture": platform.machine(),
            "Processor": platform.processor(),
            "Python_Version": platform.python_version(),
            "Python_Executable": sys.executable,
            "Current_Working_Directory": cwd
        }

    def get_exception_location(self, error: Exception) -> Result:
        """
        Function to track where exceptions occurred and return related information

        Args:
            - error (Exception): The exception object to track.

        Returns:
            Result: A Result object containing the location information where the exception occurred.
                - Format (str): '{file}', line {line}, in {function}'

        Example:
            >>> try:
            >>>     1 / 0
            >>> except Exception as e:
            >>>     location_result = tracker.get_exception_location(e)
            >>>     print(location_result.data)
            >>> # Output: 'script.py', line 10, in <module>
        """
        try:
            tb = traceback.extract_tb(error.__traceback__)
            frame = tb[-1]  # Most recent frame
            return Result(True, None, None, f"'{frame.filename}', line {frame.lineno}, in {frame.name}")
        except Exception as e:
            print("An error occurred while handling another exception. This may indicate a critical issue.")
            return Result(False, f"{type(e).__name__} :{str(e)}", "Core.ExceptionTracker.get_exception_location, R23-54", traceback.format_exc())

    def get_exception_info(self, error: Exception, user_input: Any=None, params: dict=None, masking: bool=False) -> Result:
        """
        Function to track exception information and return related information
        
        The error data dict includes traceback, location information, occurrence time, input context, etc.
        If masking is True, computer information will be masked.

        Args:
            - error (Exception): The exception object to track.
            - user_input (Any, optional): User input context related to the exception. Defaults to None.
            - params (dict, optional): Additional parameters related to the exception. Defaults to None.
            - masking (bool, optional): If True, computer information will be masked. Defaults to False.

        Returns:
            Result: A Result object containing detailed information about the exception.
                - data (dict): A dictionary containing detailed exception information. ( Please see Readme.md for more details on the structure of error_info )

        Example:
            >>> try:
            >>>     def divide(a, b):
            >>>         return a / b
            >>>     a, b = 10, 0
            >>>     # This will raise a ZeroDivisionError
            >>>     divide(a, b)
            >>> except Exception as e:
            >>>     info_result = tracker.get_exception_info(e, user_input="Divide operation", params={"a": a, "b": b}, masking=False)
            >>>     print(info_result.data)
            >>> # Output: ( error_info dict, see Readme.md for structure )
        """
        try:
            tb = traceback.extract_tb(error.__traceback__)
            frame = tb[-1]  # Most recent frame
            error_info = {
                "success": False,
                "error":{
                    "type": type(error).__name__ if error else "UnknownError", 
                    "message": str(error) if error else "No exception information available"
                },
                "location": {
                    "file": frame.filename if frame else "Unknown",
                    "line": frame.lineno if frame else -1,
                    "function": frame.name if frame else "Unknown"
                },
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "input_context": {
                    "user_input": user_input,
                    "params": params
                },
                "traceback": traceback.format_exc(),
                "computer_info": self._system_info if not masking else "<Masked>"
            }
            return Result(True, None, None, error_info)
        except Exception as e:
            print("An error occurred while handling another exception. This may indicate a critical issue.")
            return Result(False, f"{type(e).__name__} :{str(e)}", "Core.ExceptionTracker.get_exception_info, R56-90", traceback.format_exc())
        
    def get_exception_return(self, error: Exception, user_input: Any=None, params: dict=None, masking: bool=False) -> dict:
        """
        A convenience function to standardize the return of exception information. It's designed to be used in exception handling blocks.
        ( Includes exception type, message, location, and detailed info. )

        I recommend that the caller return the return value of this function as is.

        If masking is True, Exception information will be masked.

        Args:
            - error (Exception): The exception object to track.
            - user_input (Any, optional): User input context related to the exception. Defaults to None.
            - params (dict, optional): Additional parameters related to the exception. Defaults to None.
            - masking (bool, optional): If True, exception information will be masked. Defaults to False.

        Returns:
            Result: A dictionary containing detailed information about the exception.

        Example:
            >>> try:
            >>>     1 / 0
            >>> except Exception as e:
            >>>     print(tracker.get_exception_return(e, user_input="Divide operation", params={"a":1, "b":0}, True))
            >>> Result(False, 'ZeroDivisionError :division by zero', "'script.py', line 10, in <module>", '<Masked>')
        """
        try:
            return Result(False, f"{type(error).__name__} :{str(error)}", self.get_exception_location(error).data, self.get_exception_info(error, user_input, params).data if not masking else "<Masked>")
        except Exception as e:
            print("An error occurred while handling another exception. This may indicate a critical issue.")
            return Result(False, f"{type(e).__name__} :{str(e)}", "Core.ExceptionTracker.get_exception_return, R92-105", traceback.format_exc())
        
class ExceptionTrackerDecorator():
    """
    Decorator for wrapping functions with ExceptionTracker.

    - Tracks exceptions and returns a safe value via ExceptionTracker.
    - Use only for non-critical functions (adds overhead).
    - Not suitable if logging or side effects are required. 
    
    Example:
        >>> tracker = ExceptionTracker()
        >>> @ExceptionTrackerDecorator(masking=True, tracker=tracker)
        >>> def risky_function(x, y):
        >>>     return x / y
        >>> print(risky_function(10, 0))
        >>> # Output: Result(False, 'ZeroDivisionError :division by zero', "'script.py', line 10, in risky_function", '<Masked>')
    """
    def __init__(self, masking: bool=False, tracker: ExceptionTracker=None):
        self.tracker = tracker or ExceptionTracker()
        self.masking = masking

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return self.tracker.get_exception_return(error=e, params=kwargs, masking=self.masking)
        return wrapper
    