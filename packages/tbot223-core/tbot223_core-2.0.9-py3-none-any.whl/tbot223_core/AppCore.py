#external Modules
import os
import subprocess
import sys
from typing import Any, Callable, List, Dict, Tuple, Union, Optional, Generator
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import logging

#internal Modules
from tbot223_core.Result import Result
from tbot223_core.Exception import ExceptionTracker
from tbot223_core import FileManager, LogSys

class AppCore:
    """
    Provides core functionalities for application management.

    Attributes:
        is_logging_enabled (bool): Flag to enable or disable logging.
        is_debug_enabled (bool): Flag to enable or disable debug mode.
        default_lang (str): Default language code for localization. (Fallback language)
        base_dir (Union[str, Path]): Base directory for the application.
        logger_manager_instance (LogSys.LoggerManager): Instance of LoggerManager for logging.
        logger (logging.Logger): Logger instance for logging messages.
        log_instance (LogSys.Log): Instance of Log for logging messages.
        filemanager (FileManager.FileManager): Instance of FileManager for file operations.

    Methods:
        thread_pool_executor(data, workers, override, timeout) -> Result:
            Execute functions in parallel using ThreadPoolExecutor.

        process_pool_executor(data, workers, override, timeout) -> Result:
            Execute functions in parallel using ProcessPoolExecutor.
        
        get_text_by_lang(key, lang) -> Result:
            Retrieve localized text for the given key and language.

        clear_console() -> Result:
            Clear the console screen.

        exit_application(code) -> Result:
            Exit the application with the specified exit code. ( Returns Only On Failure )

        restart_application() -> Result:
            Restart the current application. ( Returns Only On Failure )
    """
    
    def __init__(self, is_logging_enabled: bool=True, is_debug_enabled: bool=False, default_lang: str="en",
                 base_dir: Union[str, Path]=None,
                 logger_manager_instance: Optional[LogSys.LoggerManager]=None, logger: Optional[logging.Logger]=None, 
                 log_instance: Optional[LogSys.Log]=None, filemanager: Optional[FileManager.FileManager]=None):

        # Initialize paths
        self._PARENT_DIR = Path(base_dir) if base_dir is not None else Path.cwd()
        self._LANG_DIR = self._PARENT_DIR / "Languages"
        Path.mkdir(self._LANG_DIR, exist_ok=True)

        # Initialize Flags
        self.is_logging_enabled = is_logging_enabled
        self.is_debug_enabled = is_debug_enabled

        # Initialize classes
        self._exception_tracker = ExceptionTracker()
        self._logger_manager = None
        self.logger = None
        if self.is_logging_enabled:
            self._logger_manager = logger_manager_instance or LogSys.LoggerManager(base_dir=self._PARENT_DIR / "logs", second_log_dir="app_core")
            self._logger_manager.make_logger("AppCoreLogger")
            self.logger = logger or self._logger_manager.get_logger("AppCoreLogger").data
        self.log = log_instance or LogSys.Log(logger=self.logger)
        self._file_manager  = filemanager or FileManager.FileManager(is_logging_enabled=False, base_dir=self._PARENT_DIR)
        
        # Initialize internal variables
        self._lang_cache = {}
        self._default_lang = default_lang
        self._supported_langs = self._file_manager.list_of_files(self._LANG_DIR, extensions=['.json'], only_name=True).data
        if self._supported_langs is None or len(self._supported_langs) == 0:
            self.log.log_message("WARNING", "No language files found in Languages directory.")

        self.log.log_message("INFO", f"AppCore initialized. Supported languages: {self._supported_langs}")
    
    # internal Methods
    @staticmethod
    def _check_executable(data: List[Tuple[Callable[ ... , Any], Dict]], workers: int, override: bool, timeout: float, chunk_size: Optional[int] = None) -> Union[bool, str]:
        """
        Check if the functions in data and workers are valid for execution.
        
        Args:
            data : List of tuples containing functions and their parameters.
            workers : Number of worker threads/processes.
            override : If True, allows workers to exceed the number of tasks.
            timeout : Maximum time to wait for each function to complete.

        Returns:
            Tuple (is_valid: bool, error_message: str)

        Example:
            >>> # I'm not recommending to call this method directly, it's for internal use.
            >>> data = [(func1, {'arg1': val1}), (func2, {'arg2': val2})]
            >>> is_valid, error_message = app_core._check_executable(data, workers=4, override=False, timeout=10)
            >>> if not is_valid:
            >>>     print(error_message)
            >>> else:
            >>>     print("Data and workers are valid for execution.")
        """
        if not isinstance(data, list) or len(data) == 0:
            return False, "Data must be a non-empty list"
        for item in data:
            if not (isinstance(item, tuple) and len(item) == 2 and callable(item[0]) and isinstance(item[1], dict)):
                return False, "Each item in data must be a tuple of (function, kwargs_dict)"
        if workers is None or not isinstance(workers, int) or workers <= 0:
            return False, "workers must be a positive integer"
        if workers > len(data) and not override:
            return False, f"workers {workers} exceeds number of tasks {len(data)}"
        if timeout is None or not isinstance(timeout, (int, float)) or timeout <= 0.1:
            return False, "timeout must be a positive number"
        if chunk_size is not None and (not isinstance(chunk_size, int) or chunk_size <= 0):
            return False, "chunk_size must be a positive integer"
        return True, None
    
    def _generic_executor(self, data: List[Tuple[Callable[ ... , Any], Dict]], workers: int, timeout: float, type: str) -> List[Result]:
        """
        Generic executor method to be used by both thread and process pool executors.

        Args:
            data : List of tuples containing functions and their parameters.
            workers : Number of worker threads/processes.
            timeout : Maximum time to wait for each function to complete.
            type : 'thread' for ThreadPoolExecutor, 'process' for ProcessPoolExecutor.

        Returns:
            indexed list of Result objects corresponding to each function execution.

        Example:
            >>> # I'm not recommending to call this method directly, it's for internal use.
            >>> data = [(func1, {'arg1': val1}), (func2, {'arg2': val2})]
            >>> results = app_core._generic_executor(data, workers=4, timeout=10, type='thread')
            >>> for res in results:
            >>>     print(res.success, res.data)
        """
        results = [None] * len(data)

        executor_type = ThreadPoolExecutor if type == 'thread' else ProcessPoolExecutor
        with executor_type(max_workers=workers) as executor:
            future_to_task = {executor.submit(func, **params): idx for idx, (func, params) in enumerate(data)}

            for future in as_completed(future_to_task):
                idx = future_to_task[future]
                try:
                    result = future.result(timeout=timeout)
                    results[idx] = Result(True, None, None, result)
                except Exception as e:
                    self.log.log_message("ERROR", f"Error executing task at index {idx}: {str(e)}")
                    results[idx] = self._exception_tracker.get_exception_return(e, params=data[idx][1])
                    
            try:
                executor.shutdown(wait=True)
            except Exception as e:
                self.log.log_message("ERROR", f"Error during executor shutdown: {str(e)}")
        return results
    
    def _chunk_list(self, data_list: List, chunk_size: int) -> Generator[List, None, None]:
        """
        Helper method to split a list into smaller chunks.

        Args:
            data_list : The list to be chunked.
            chunk_size : The size of each chunk.

        Returns:
            A list of chunks (sublists).

        Example:
            >>> # I'm not recommending to call this method directly, it's for internal use.
            >>> my_list = [1, 2, 3, 4, 5, 6, 7]
            >>> chunks = app_core._chunk_list(my_list, chunk_size=3)
            >>> print(chunks)  # Output: [[1, 2, 3], [4, 5, 6], [7]]
        """
        for i in range(0, len(data_list), chunk_size):
            yield data_list[i:i + chunk_size]

    # external Methods
    def thread_pool_executor(self, data: List[Tuple[Callable[ ... , Any], Dict]], workers: int = None, override: bool = False, timeout: float = None) -> Result:
        """
        Execute functions in parallel using ThreadPoolExecutor.

        Args:
            data : 
            workers : Number of worker threads to use. Defaults to os.cpu_count() * 2.
            override : If True, allows workers to exceed the number of tasks.
            timeout : Maximum time to wait for each function to complete. ( 0.1 seconds minimum )

        Returns:
            indexed list of Result objects corresponding to each function execution.

        Example:
            >>> data = [(func1, {'arg1': val1}), (func2, {'arg2': val2})]
            >>> result = app_core.thread_pool_executor(data, workers=4, override=False, timeout=10)
            >>> for res in result.data:
            >>>     print(res.success, res.data)
        """
        try:
            is_valid, error_message = self._check_executable(data, workers, override, timeout)
            if not is_valid:
                self.log.log_message("ERROR", f"Thread pool executor validation failed: {error_message}")
                return Result(False, error_message, None, None)
            workers = min(workers or os.cpu_count() * 2, os.cpu_count() * 2)
            results = self._generic_executor(data, workers, timeout, type='thread')

            self.log.log_message("INFO", f"Thread pool executor completed with {len(results)} tasks.")
            return Result(True, None, None, results)
        except Exception as e:
            self.log.log_message("ERROR", f"Error in thread pool executor: {str(e)}")
            return self._exception_tracker.get_exception_return(e)

    def process_pool_executor(self, data: List[Tuple[Callable[ ... , Any], Dict]], workers: int = None, override: bool = False, timeout: float = None, chunk_size: Optional[int] = None) -> Result:
        """
        Execute functions in parallel using ProcessPoolExecutor.

        Args:
            data : List of tuples, Each containing a function and a dictionary of arguments. Example: [(func1, {'arg1': val1}), (func2, {'arg2': val2})]
            workers : Number of worker processes to use. Defaults to os.cpu_count() * 2.
            override : If True, allows workers to exceed the number of tasks.
            timeout : Maximum time to wait for each function to complete. ( 0.1 seconds minimum )

        Returns:
            indexed list of Result objects corresponding to each function execution.

        Example:
            >>> data = [(func1, {'arg1': val1}), (func2, {'arg2': val2})]
            >>> result = app_core.process_pool_executor(data, workers=4, override=False, timeout=10)
            >>> for res in result.data:
            >>>     print(res.success, res.data)
        """
        try:
            is_valid, error_message = self._check_executable(data, workers, override, timeout, chunk_size)
            if not is_valid:
                self.log.log_message("ERROR", f"Process pool executor validation failed: {error_message}")
                return Result(False, error_message, None, None)
            workers = min(workers or os.cpu_count() * 2, os.cpu_count() * 2)
            chunks = list(self._chunk_list(data, chunk_size or int(len(data)/workers)))
            results = []
            for chunk in chunks:
                chunk_results = self._generic_executor(chunk, workers, timeout, type='process')
                results.extend(chunk_results)

            self.log.log_message("INFO", f"Process pool executor completed with {len(results)} tasks.")
            return Result(True, None, None, results)
        except Exception as e:
            self.log.log_message("ERROR", f"Error in process pool executor: {str(e)}")
            return self._exception_tracker.get_exception_return(e)
        
    def get_text_by_lang(self, key: str, lang: str) -> Result:
        """
        Retrieve localized text for the given key and language.

        - If the key does not exist in the language file, return an error.

        Args:
            key : The key for the desired text.
            lang : The language code (e.g., 'en', 'fr').
        
        Returns:
            The localized text corresponding to the key and language.

        Example:
            >>> result = app_core.get_text_by_lang('greeting', 'en')
            >>> if result.success:
            >>>     print(result.data)  # Output: "Hello"
            >>> else:
            >>>     print(result.error)
        """

        try:
            if lang not in self._supported_langs:
                lang = self._default_lang

            if lang not in self._lang_cache:
                self.log.log_message("INFO", f"Loading language file for '{lang}'.")
                lang_file_path = self._LANG_DIR / f"{lang}.json"
                read_result = self._file_manager.read_json(lang_file_path)
                if not read_result.success:
                    self.log.log_message("ERROR", f"Failed to read language file for '{lang}': {read_result.error}")
                    return read_result
                self._lang_cache[lang] = read_result.data

            if key not in self._lang_cache[lang]:
                self.log.log_message("ERROR", f"Key '{key}' not found in language '{lang}'.")
                raise KeyError(f"Key '{key}' not found in language '{lang}'.")
            
            self.log.log_message("INFO", f"Retrieved text for key '{key}' in language '{lang}'.")
            return Result(True, None, None, self._lang_cache[lang][key])
        except Exception as e:
            self._lang_cache.pop(lang, None)
            self.log.log_message("ERROR", f"Error in get_text_by_lang: {str(e)}")
            return self._exception_tracker.get_exception_return(e)
        
    def clear_console(self) -> Result:
        """
        Clear the console screen using the appropriate command based on the operating system.

        Returns:
            Result object indicating success or failure of the operation.

        Example:
            >>> result = app_core.clear_console() # then console is cleared
        """
        try:
            command = 'cls' if os.name == 'nt' else 'clear'
            subprocess.run(command, shell=True, check=True)

            self.log.log_message("INFO", "Console cleared successfully.")
            return Result(True, None, None, "Console cleared successfully.")
        except Exception as e:
            self.log.log_message("ERROR", f"Error in clear_console: {str(e)}")
            return self._exception_tracker.get_exception_return(e)
        
    def exit_application(self, code: int=0, pause: bool=False) -> Result:
        """
        Exit the application with the specified exit code.

        Args:
            code : Exit code to return to the operating system. Default is 0.

        Returns:
            returns only on failure with a Result object indicating the error.

        Example:
            >>> result = app_core.exit_application(0) # then application exits with code 0
        """
        try:
            self.log.log_message("INFO", f"Exiting application with code {code}.")
            if pause:
                input("Press Enter to exit...")
            sys.exit(code)
        except Exception as e:
            self.log.log_message("ERROR", f"Error in exit_application: {str(e)}")
            return self._exception_tracker.get_exception_return(e)
    
    def restart_application(self, pause: bool=False) -> Result:
        """
        Restart the current application.

        Returns:
            returns only on failure with a Result object indicating the error.

        Example:
            >>> result = app_core.restart_application() # then application restarts
        """
        try:
            python = sys.executable
            self.log.log_message("INFO", "Restarting application.")
            if pause:
                input("Press Enter to restart...")
            os.execl(python, python, * sys.argv)
        except Exception as e:
            self.log.log_message("ERROR", f"Error in restart_application: {str(e)}")
            return self._exception_tracker.get_exception_return(e)
        
    def safe_CLI_input(self, prompt: str="", input_type: type=str, valid_options: List[str]=None, case_sensitive: bool=False, allow_empty: bool=False) -> Result:
        """
        Safely get user input from the command line with validation.

        Args:
            prompt : The prompt message to display to the user.
            valid_options : A list of valid options. If provided, input must match one of these options.
            case_sensitive : If True, input validation is case sensitive.
            allow_empty : If True, allows empty input.
        
        Returns:
            The user input if it passes validation.

        Example:
            >>> result = app_core.safe_CLI_input(prompt="Enter your choice: ", valid_options=["yes", "no"], case_sensitive=False)
            >>> if result.success:
            >>>     print(f"You entered: {result.data}")
            >>> else:
            >>>     print(result.error)
        """
        try:
            def validate_input(user_input: str) -> bool:
                if not allow_empty and user_input == "":
                    return False
                if valid_options:
                    comparison_input = user_input if case_sensitive else user_input.lower()
                    comparison_options = valid_options if case_sensitive else map(str.lower, valid_options)
                    return comparison_input in comparison_options
                return True
            
            while True:
                user_input = input(prompt)
                if validate_input(user_input):
                    try:
                        converted_input = input_type(user_input)
                        self.log.log_message("INFO", f"User input received and validated: {converted_input}")
                        return Result(True, None, None, converted_input)
                    except ValueError:
                        self.log.log_message("WARNING", f"Input conversion to {input_type} failed for input: {user_input}")
                        print(f"Invalid input type. Please enter a value of type {input_type.__name__}.")
                else:
                    self.log.log_message("WARNING", f"User input validation failed: {user_input}")
                    if valid_options:
                        print(f"Invalid option. Please choose from: {', '.join(valid_options)}")
                    else:
                        print("Invalid input. Please try again.")
        except Exception as e:
            self.log.log_message("ERROR", f"Error in safe_CLI_input: {str(e)}")
            return self._exception_tracker.get_exception_return(e)
        
class ResultWrapper:
    """
    A decorator class that ensures the return value of an existing function is wrapped in a Result object.

    - DO NOT use ExceptionTrackerDecorator with ResultWrapper, as ResultWrapper already handles exceptions.
    - if the decorated function already returns a Result object, it will be returned as is.
    - If an exception occurs during the function execution, it will be caught and a Result object indicating failure will be returned.
    - Use for Non-critical functions where you want to ensure a Result object is always returned.

    Example:
        >>> @ResultWrapper()
        >>> def my_function(x, y):
        >>>     return x + y
        >>> result = my_function(5, 10)
        >>> print(result.success)  # Output: True
        >>> print(result.data)     # Output: 15
    """
    def __init__(self):
        pass

    def __call__(self, func: Callable[..., Any]) -> Result:
        def wrapper(*args, **kwargs) -> Result:
            try:
                result = func(*args, **kwargs)
                if isinstance(result, Result):
                    return result
                
                return Result(True, None, None, result)
            except Exception as e:
                tracker = ExceptionTracker()
                return tracker.get_exception_return(e)
        return wrapper