# external Modules
import os
from typing import Union, Any, Optional
from pathlib import Path
import logging
import time

# internal Modules
from tbot223_core.Result import Result
from tbot223_core.Exception import ExceptionTracker

class LoggerManager:
    """
    Logger Manager class to create and manage logger instances

    Attributes:
        - base_dir : Base directory for logs.
        - second_log_dir : Subdirectory name within the base log directory.

    Methods:
        - make_logger(logger_name, log_level, time) -> Result
            Create logger instance

        - get_logger(logger_name) -> Result
            Get logger instance by name
    """
    def __init__(self, base_dir: Union[str, Path]=None, second_log_dir: Union[str, Path]="default"):
        """
        Initialize logger manager
        """
        # Dictionary to hold logger instances
        self._loggers = {}
        
        # Initialize base directory for logs
        self._BASE_DIR = Path(base_dir) if base_dir is not None else Path.cwd() / "logs"
        os.makedirs(self._BASE_DIR, exist_ok=True)
        self.second_log_dir = str(second_log_dir)

        # Record start time for log filenames
        self._started_time = time.strftime("%Y-%m-%d_%Hh-%Mm-%Ss", time.localtime())

    def make_logger(self, logger_name: str, log_level: int=logging.INFO, time: Any = None) -> Result:
        """
        Create logger instance

        Args:
            - logger_name : Name of the logger.
            - log_level : Logging level (default: logging.INFO).
            - time : Time string to include in log filename. Defaults to None
            
        Returns:
            Result: A Result object indicating success or failure of logger creation.

        Example:
            >>> logger_manager = LoggerManager()
            >>> result = logger_manager.make_logger("my_logger", logging.DEBUG)
            >>> if result.success:
            >>>     print(result.data) # Logger 'my_logger' created successfully.
            >>> else:
            >>>     print(result.error)
        """
        try:
            # Duplicate check
            if logger_name in self._loggers:
                raise ValueError(f"Logger with name '{logger_name}' already exists.")

            # Always create a new logger instance
            self._loggers[logger_name] = logging.getLogger(logger_name)
            logger = self._loggers[logger_name]
            logger.setLevel(log_level)
            logger.propagate = False  # Prevent duplicate log output

            # Create a log file
            log_filename = self._BASE_DIR / self.second_log_dir / f"{time or self._started_time}_log" / f"{logger_name}.log"
            os.makedirs(os.path.dirname(log_filename), exist_ok=True)

            # Prevent duplicate handlers
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

            # Set formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            # Set file handler
            file_handler = logging.FileHandler(log_filename)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Set console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            return Result(True, None, None, f"Logger '{logger_name}' created successfully.")
        except Exception as e:
            return ExceptionTracker().get_exception_return(e)
        
    def get_logger(self, logger_name: str) -> Result:
        """
        Get logger instance by name

        Args:
            - logger_name : Name of the logger to retrieve.
        
        Returns:
            Result: A Result object containing the logger instance if found.

        Example:
            >>> logger_manager = LoggerManager()
            >>> logger_manager.make_logger("my_logger", logging.DEBUG)
            >>> result = logger_manager.get_logger("my_logger")
            >>> if result.success:
            >>>     logger = result.data
            >>>     logger.info("This is a test log message.")
            >>> else:
            >>>     print(result.error)        
        """
        try:
            if logger_name not in self._loggers:
                raise ValueError(f"Logger with name '{logger_name}' does not exist.")
            return Result(True, None, None, self._loggers[logger_name])
        except Exception as e:
            return ExceptionTracker().get_exception_return(e)
        
class Log:
    """
    Log class for logging messages

    Attributes:
        - logger : Logger instance for logging messages.

    Methods:
        - log_message(level, message) -> Result
            Log a message with the specified log level.
    """

    def __init__(self, logger: logging.Logger = None):
        """
        Initialize Log class with a logger instance.
        """
        self.logger = logger
        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

    def log_message(self, level: Optional[Union[int, str]], message: str) -> Result:
        """
        Log a message with the specified log level.

        Args:
            - level : Log level as an integer or string ('INFO').
            - message : The message to log.

        Returns:
            Result: A Result object indicating success or failure of the logging operation.

        Example:
            >>> logger_manager = LoggerManager()
            >>> logger_result = logger_manager.make_logger("app_logger", logging.INFO)
            >>> if logger_result.success:
            >>>     logger = logger_result.data
            >>>     log_system = Log(logger)
            >>>     log_result = log_system.log_message('INFO', "This is an info message.")
            >>>     if log_result.success:
            >>>         print("Log message sent successfully.")
            >>>     else:
            >>>         print(log_result.error)
            >>> else:
            >>>     print(logger_result.error)
        """
        if self.logger is None:
            return Result(False, None, None, "Logger is not initialized.")
        try:
            if isinstance(level, str):
                level = self.log_levels.get(level.upper(), logging.INFO)

            self.logger.log(level, message)
            return Result(True, None, None, "Log message sent successfully.")
        except Exception as e:
            return ExceptionTracker().get_exception_return(e)
        
class SimpleSetting:
    """
    Simple setting class for LoggerManager and Log
    
    Attributes:
        - logger_manager : Instance of LoggerManager.
        - log : Instance of Log.
        - logger : Logger instance.
        
    Methods:
        - get_instance() -> Tuple[LoggerManager, Log, logging.Logger]
            Get instances of LoggerManager, Log, and Logger.
    """
    def __init__(self, base_dir: Union[str, Path], second_log_dir: Union[str, Path], logger_name: str):
        """
        Simple setting for LoggerManager and Log
        """
        self.logger_manager = LoggerManager(base_dir, second_log_dir)
        result = self.logger_manager.make_logger(logger_name)
        if result.success:
            self.logger = result.data
        else:
            self.logger = None
        self.log = Log(self.logger)

    def get_instance(self):
        """
        Get instances of LoggerManager, Log, and Logger.
        
        Args:
            None
            
        Returns:
            Tuple[LoggerManager, Log, logging.Logger]: Instances of LoggerManager, Log, and Logger.
            
        Example:
            >>> setting = SimpleSetting("logs", "default", "app_logger")
            >>> logger_manager, log, logger = setting.get_instance()
        """
        return self.logger_manager, self.log, self.logger