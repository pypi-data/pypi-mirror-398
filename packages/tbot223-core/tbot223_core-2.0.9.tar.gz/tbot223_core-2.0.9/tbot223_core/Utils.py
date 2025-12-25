# external Modules
from pathlib import Path
from typing import Optional, Union, List, Any, Dict, Callable
import time
import hashlib, secrets
import logging
import threading

# internal Modules
from tbot223_core.Result import Result
from tbot223_core.Exception import ExceptionTracker
from tbot223_core import LogSys

class Utils:
    """
    Utility class providing various helper functions.

    Methods:
        - str_to_path(path_str) -> Result
            Convert a string to a Path object.
        
        - encrypt(data, algorithm) -> Result
            Encrypt a string using the specified algorithm.

        - pbkdf2_hmac(password, algorithm, iterations, salt_size) -> Result
            Generate a PBKDF2 HMAC hash of the given password.

        - verify_pbkdf2_hmac(password, salt_hex, hash_hex, iterations, algorithm) -> Result
            Verify a PBKDF2 HMAC hash of the given password.

        - insert_at_intervals(data, interval, insert, at_start) -> Result
            Insert a specified element into a list or string at regular intervals.

        - find_keys_by_value(dict_obj, threshold, comparison, nested) -> Result
            Find keys in a dictionary based on value comparisons.
    """
    
    def __init__(self, is_logging_enabled: bool=False,
                 base_dir: Union[str, Path]=None,
                 logger_manager_instance: Optional[LogSys.LoggerManager]=None, logger: Optional[logging.Logger]=None, 
                 log_instance: Optional[LogSys.Log]=None):
        """
        Initialize Utils class.
        """
        # Initialize Paths
        self._BASE_DIR = Path(base_dir or Path.cwd())

        # Initialize Flags
        self.is_logging_enabled = is_logging_enabled

        # Initialize Classes
        self._exception_tracker = ExceptionTracker()
        self._logger_manager = None
        self._logger = None
        if self.is_logging_enabled:
            self._logger_manager = logger_manager_instance or LogSys.LoggerManager(base_dir=self._BASE_DIR / "logs", second_log_dir="utils")
            self._logger_manager.make_logger("UtilsLogger")
            self._logger = logger or self._logger_manager.get_logger("UtilsLogger").data
        self.log = log_instance or LogSys.Log(logger=self._logger)

        self.log.log_message("INFO", "Utils initialized.")

    # Internal Methods
    def _check_pbkdf2_params(self, password: str, algorithm: str, iterations: int, salt_size: int = 32) -> None:
        """
        Check parameters for PBKDF2 HMAC functions.

        Args:
            - password : The password string.
            - algorithm : The hashing algorithm to use.
            - iterations : Number of iterations.
            - salt_size : Size of the salt in bytes (default: 32).

        Raises:
            ValueError: If any parameter is invalid.
        
        Example:
            >>> I'm Not recommending to call this method directly, It's for internal use.
            >>> utils = Utils()
            >>> utils._check_pdkdf2_params("my_password", "sha256", 100000, 32)
            >>> # No exception raised for valid parameters.
        """
        if not isinstance(password, str):
            raise ValueError("password must be a string")
        if algorithm not in ['sha1', 'sha256', 'sha512']:
            raise ValueError("Unsupported algorithm. Supported algorithms: 'sha1', 'sha256', 'sha512'")
        if not isinstance(iterations, int) or iterations <= 0:
            raise ValueError("iterations must be a positive integer")
        if not isinstance(salt_size, int) or salt_size <= 0:
            raise ValueError("salt_size must be a positive integer")
        
    def _lookup_dict(self, dict_obj: Dict, threshold: Union[int, float, str, bool], comparison_func: Callable, comparison_type: str, nested: bool, nest_mark: str = "") -> List:
        """
        Helper method to recursively look up keys in a dictionary based on a comparison function.

        Args:
            dict_obj : The dictionary to search.
            threshold : The value to compare against.
            comparison_func : A callable that takes a value and returns True if it meets the condition.
            comparison_type : The type of comparison being performed.
            nested : If True, search within nested dictionaries.

        Returns:
            A list of keys that meet the comparison criteria.

        Example:
            >>> # I'm not recommending to call this method directly, it's for internal use.
            >>> my_dict = {'a': 10, 'b': 20, 'c': 30}
            >>> found_keys = app_core._lookup_dict(my_dict, threshold=20, comparison_func=lambda x: x > 20, comparison_type='gt', nested=False)
            >>> print(found_keys)  # Output: ['c']
        """
        found_keys = []
        for key, value in dict_obj.items():
            if isinstance(value, (str, bool)) != isinstance(threshold, (str, bool)) and comparison_type in ['eq', 'ne']:
                continue
            if isinstance(value, (tuple, list)):
                continue
            if comparison_func(value):
                found_keys.append(f"{nest_mark}{key}")
                self.log.log_message("DEBUG", f"Key '{nest_mark}{key}' matches the condition.")
            if nested and isinstance(value, dict):
                self.log.log_message("DEBUG", f"Searching nested dictionary at key '{key}'.")
                found_keys.extend(self._lookup_dict(value, threshold, comparison_func, comparison_type, nested, f"{nest_mark}{key}."))
        return found_keys

    # external Methods
    def str_to_path(self, path_str: str) -> Path:
        """
        Convert a string to a Path object.

        Args:
            - path_str : The string representation of the path.
            
        Returns:
            Result: A Result object containing the Path object.
        
        Example:
            >>> result = utils.str_to_path("/home/user/documents")
            >>> if result.success:
            >>>     path = result.data # Path object
            >>>     print(path.exists())
            >>> else:
            >>>     print(result.error)
        """
        try:
            if not isinstance(path_str, str):
                return Result(True, "already a Path object", None, path_str)

            return Result(True, None, None, Path(path_str))
        except Exception as e:
            return self._exception_tracker.get_exception_return(e)
        
    def encrypt(self, data: str, algorithm: str='sha256') -> Result:
        """
        Encrypt a string using the specified algorithm.
        Supported algorithms: 'md5', 'sha1', 'sha256', 'sha512'

        Args:
            - data : The string to encrypt.
            - algorithm : The hashing algorithm to use. Defaults to 'sha256'

        Returns:
            Result: A Result object containing the encrypted string in hexadecimal format.

        Example:
            >>> result = utils.encrypt("my_secret_data", algorithm='sha256')
            >>> if result.success:
            >>>     encrypted_data = result.data
            >>>     print(encrypted_data)
            >>> else:
            >>>     print(result.error)
        """
        try:
            if not isinstance(data, str):
                raise ValueError("data must be a string")
            if algorithm not in ['md5', 'sha1', 'sha256', 'sha512']:
                raise ValueError("Unsupported algorithm. Supported algorithms: 'md5', 'sha1', 'sha256', 'sha512'")

            hash_func = getattr(hashlib, algorithm)()
            hash_func.update(data.encode('utf-8'))
            encrypted_data = hash_func.hexdigest()

            self.log.log_message("INFO", f"Data encrypted using {algorithm}.")
            return Result(True, None, None, encrypted_data)
        except Exception as e:
            self.log.log_message("ERROR", f"Encryption failed: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def pbkdf2_hmac(self, password: str, algorithm: str, iterations: int, salt_size: int) -> Result:
        """
        Generate a PBKDF2 HMAC hash of the given password.
        Supported algorithms: 'sha1', 'sha256', 'sha512'

        This function returns a dict containing the salt (hex), hash (hex), iterations, and algorithm used.

        Args:
            - password : The password string.
            - algorithm : The hashing algorithm to use.
            - iterations : Number of iterations.
            - salt_size : Size of the salt in bytes.

        Returns:
            Result: A Result object containing a dict with the following keys:
        
        Example:
            >>> result = utils.pbkdf2_hmac("my_password", "sha256", 100000, 32)
            >>> if result.success:
            >>>     hash_info = result.data
            >>>     print(hash_info)
            >>> else:
            >>>     print(result.error)
        """
        try:
            self._check_pbkdf2_params(password, algorithm, iterations, salt_size)
            
            salt = secrets.token_bytes(salt_size)
            hash_bytes = hashlib.pbkdf2_hmac(algorithm, password.encode('utf-8'), salt, iterations)

            salt_hex = salt.hex()
            hash_hex = hash_bytes.hex()
            result = {
                "salt_hex": salt_hex,
                "hash_hex": hash_hex,
                "iterations": iterations,
                "algorithm": algorithm
            }

            self.log.log_message("INFO", f"PBKDF2 HMAC hash generated using {algorithm} with {iterations} iterations.")
            return Result(True, None, None, result)
        except Exception as e:
            self.log.log_message("ERROR", f"PBKDF2 HMAC hash generation failed: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def verify_pbkdf2_hmac(self, password: str, salt_hex: str, hash_hex: str, iterations: int, algorithm: str) -> Result:
        """
        Verify a PBKDF2 HMAC hash of the given password.
        Supported algorithms: 'sha1', 'sha256', 'sha512'

        This function returns True if the password matches the hash, False otherwise.

        Args:
            - password : The password string to verify.
            - salt_hex : The salt in hexadecimal format.
            - hash_hex : The hash in hexadecimal format.
            - iterations : Number of iterations.
            - algorithm : The hashing algorithm to use.

        Returns:
            Result: A Result object containing a boolean indicating whether the password matches the hash.

        Example:
            >>> hash_info = {
            >>>     "salt_hex": "a1b2c3d4e5f6...",
            >>>     "hash_hex": "abcdef123456...",
            >>>     "iterations": 100000,
            >>>     "algorithm": "sha256"
            >>> }
            >>> result = utils.verify_pbkdf2_hmac("my_password", hash_info["salt_hex"], hash_info["hash_hex"], hash_info["iterations"], hash_info["algorithm"])
            >>> if result.success:
            >>>     is_valid = result.data
            >>>     print(is_valid)  # True or False
            >>> else:
            >>>     print(result.error)
        """
        try:
            self._check_pbkdf2_params(password, algorithm, iterations)
            if not isinstance(salt_hex, str) or not isinstance(hash_hex, str):
                raise ValueError("salt_hex and hash_hex must be strings")
            
            salt = bytes.fromhex(salt_hex)
            hash_bytes = hashlib.pbkdf2_hmac(algorithm, password.encode('utf-8'), salt, iterations)
            computed_hash_hex = hash_bytes.hex()

            is_valid = computed_hash_hex == hash_hex
            self.log.log_message("INFO", f"PBKDF2 HMAC hash verification using {algorithm} with {iterations} iterations. Result: {is_valid}")
            return Result(True, None, None, is_valid)
        except Exception as e:
            self.log.log_message("ERROR", f"PBKDF2 HMAC hash verification failed: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def insert_at_intervals(self, data: Union[List, str], interval: int, insert: Any, at_start: bool=True) -> Result:
        """
        Insert a specified element into a list or string at regular intervals.

        Args:
            - data (list or str): The original list or string where elements will be inserted.
            - interval (int): The interval at which to insert the element. (must be a positive integer)
            - insert (Any): The element to insert into the list or string. (if data is a string, using object like callable is not recommended as it will be converted to string)
            - at_start (bool, optional): If True, insertion starts at the beginning (index 0). If False, insertion starts after the first interval. Defaults to True.

        Returns:
            Result: A Result object containing the modified list or string.

        Example:
            >>> utils = Utils()
            >>> data_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            >>> result = utils.insert_at_intervals(data_list, 3, 'X', at_start=True)
            >>> if result.success:
            >>>    print(result.data)  # Output: ['X', 1, 2, 3, 'X', 4, 5, 6, 'X', 7, 8, 9]
            >>> else:
            >>>    print(result.error)
        """
        try:
            if not isinstance(data, (list, str)):
                raise ValueError("data must be a list or string")
            if not isinstance(interval, int) or interval <= 0:
                raise ValueError("interval must be a positive integer")
            if not isinstance(at_start, bool):
                raise ValueError("at_start must be a boolean value")
        
            original_type_is_str = False
            if isinstance(data, str):
                original_type_is_str = True
                data = list(data)

            at_start = 0 if at_start else interval
            for i in range(at_start, len(data)+at_start, interval+1):
                data[i:i] = [insert]

            if original_type_is_str:
                data = ''.join(map(str, data))
            return Result(True, None, None, data)
        except Exception as e:
            return self._exception_tracker.get_exception_return(e)
    
    def find_keys_by_value(self, dict_obj: Dict, threshold: Union[int, float, str, bool],  comparison: str='eq', nested: bool=False) -> Result:
        """
        Find keys in dict_obj where their values meet the threshold based on the comparison operator.

        [bool, str] - [int, float] comparisons are only supported for 'eq' and 'ne'.

        Args:
            dict_obj : The dictionary to search.
            threshold : The value to compare against.
            comparison : The comparison operator as a string. Default is 'eq' (equal).
            nested : If True, search within nested dictionaries.

        Returns:
            A list of keys that meet the comparison criteria.

        Example:
            >>> my_dict = {'a': 10, 'b': 20, 'c': 30}
            >>> result = app_core.find_keys_by_value(my_dict, threshold=20, comparison='gt', nested=False)
            >>> print(result.data)  # Output: ['c']

        Supported comparison operators:
        - 'eq': equal to
        - 'ne': not equal to
        - 'lt': less than
        - 'le': less than or equal to
        - 'gt': greater than
        - 'ge': greater than or equal to
        """
        comparison_operators = {
            'eq': lambda x: x == threshold,
            'ne': lambda x: x != threshold,
            'lt': lambda x: x < threshold,
            'le': lambda x: x <= threshold,
            'gt': lambda x: x > threshold,
            'ge': lambda x: x >= threshold,
        }

        try:
            if comparison not in comparison_operators:
                raise ValueError(f"Unsupported comparison operator: {comparison}")
            if isinstance(dict_obj, dict) is False:
                raise ValueError("Input data must be a dictionary")
            if isinstance(threshold, (str, bool, int, float)) is False:
                raise ValueError("Threshold must be of type str, bool, int, or float")
            
            comparison_func = comparison_operators[comparison]
            found_keys = self._lookup_dict(dict_obj, threshold, comparison_func, comparison, nested)

            self.log.log_message("INFO", f"find_keys_by_value found {len(found_keys)} keys matching criteria.")
            return Result(True, None, None, found_keys)
        except Exception as e:
            self.log.log_message("ERROR", f"Error in find_keys_by_value: {str(e)}")
            return self._exception_tracker.get_exception_return(e)
        
class DecoratorUtils:
    """
    This class provides utility decorators for various purposes.

    Methods:
        - count_runtime() -> function
            Decorator to measure and print the execution time of a function.
    """

    
    def __init__(self):
        self._exception_tracker = ExceptionTracker()

    # Internal Methods

    # external Methods
    @staticmethod
    def count_runtime():
        """
        Decorator to measure and print the execution time of a function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                run_time = end_time - start_time
                print(f"This ran for {run_time:.4f} seconds.")
                return result
            return wrapper
        return decorator
    
class GlobalVars:
    """
    This class manages global variables in a controlled manner.

    Recommended usage:
    - Beginners use explicit methods.
    - Advanced users can use attribute access or call syntax.

    Methods:
        - set(key: str, value: object, overwrite) -> Result
            Set a global variable.
        
        - get(key: str) -> Result
            Get a global variable.

        - delete(key: str) -> Result
            Delete a global variable.

        - clear() -> Result
            Clear all global variables.

        - list_vars() -> Result
            List all global variables.

        - exists(key: str) -> Result
            Check if a global variable exists.

        # internal Methods
        - __getattr__(name) 
            Get a global variable by attribute access.

        - __setattr__(name, value)
            Set a global variable by attribute access.  

        - __call__(key: str, value: Optional[object], overwrite: bool) -> Result 
            Get or set a global variable using call syntax.

    Example:
        >>> globals = GlobalVars()
        >>> globals.set("api_key", "12345", overwrite=True)
        >>> result = globals.get("api_key")
        >>> if result.success:
        >>>     print(result.data)  # Output: 12345
        >>> else:
        >>>     print(result.error)

        >>> # or using attribute access:

        >>> globals.api_key = "12345"
        >>> print(globals.api_key)  # Output: 12345
        
        >>> # or using call syntax:

        >>> globals("api_key", "12345", overwrite=True)
        >>> print(globals("api_key").data)  # Output: 12345
    """
    
    def __init__(self, is_logging_enabled: bool=False, base_dir: Union[str, Path]=None,
                 logger_manager_instance: Optional[LogSys.LoggerManager]=None, logger: Optional[logging.Logger]=None, 
                 log_instance: Optional[LogSys.Log]=None):
        
        # Set initialization flag to bypass __setattr__ during __init__
        object.__setattr__(self, '__initializing__', True)
        object.__setattr__(self, '__vars__', {})
        object.__setattr__(self, '__lock__', threading.RLock())
        
        # Initialize Paths
        self._BASE_DIR = Path(base_dir) if base_dir is not None else Path.cwd()

        # Initialize Flags
        self.is_logging_enabled = is_logging_enabled

        # Initialize Classes
        self._exception_tracker = ExceptionTracker()
        self._logger_manager = None
        self._logger = None
        if self.is_logging_enabled:
            self._logger_manager = logger_manager_instance or LogSys.LoggerManager(base_dir=self._BASE_DIR / "logs", second_log_dir="global_vars")
            self._logger_manager.make_logger("GlobalVarsLogger")
            self._logger = logger or self._logger_manager.get_logger("GlobalVarsLogger").data
        self.log = log_instance or LogSys.Log(logger=self._logger)
        
        # Initialization complete
        object.__setattr__(self, '__initializing__', False)
        
    def set(self, key: str, value: object, overwrite: bool=False) -> Result:
        """
        Set a global variable.
        
        Args:
            - key : The name of the global variable.
            - value : The value to set.
            - overwrite : If True, overwrite existing variable. Defaults to False.

        Returns:
            Result: A Result object indicating success or failure.
        
        Example:
            >>> globals = GlobalVars()
            >>> result = globals.set("api_key", "12345", overwrite=True)
            >>> if result.success:
            >>>     print(result.data)  # Output: Global variable 'api_key' set.
            >>> else:
            >>>     print(result.error)
        """
        try:
            with self.__lock__:
                if self.exists(key).data and not overwrite:
                    raise KeyError(f"Global variable '{key}' already exists.")
                if key is None or not isinstance(key, str) or key.strip() == "":
                    raise ValueError("key must be a non-empty string.")
                
                self.__vars__[key] = value
                self.log.log_message("INFO", f"Global variable '{key}' set.")
                return Result(True, None, None, f"Global variable '{key}' set.")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to set global variable '{key}': {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def get(self, key: str) -> Result:
        """
        Get a global variable.

        Args:
            - key : The name of the global variable.

        Returns:
            Result: A Result object containing the value of the global variable.

        Example:
            >>> globals = GlobalVars()
            >>> globals.set("api_key", "12345", overwrite=True)
            >>> result = globals.get("api_key")
            >>> if result.success:
            >>>     print(result.data)  # Output: 12345
            >>> else:
            >>>     print(result.error)
        """
        try:
            with self.__lock__:
                if not self.exists(key):
                    raise KeyError(f"Global variable '{key}' does not exist.")
                
                self.log.log_message("INFO", f"Global variable '{key}' accessed.")
                return Result(True, None, None, self.__vars__[key])
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to get global variable '{key}': {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def delete(self, key: str) -> Result:
        """
        Delete a global variable.

        Args:
            - key : The name of the global variable.
        
        Returns:
            Result: A Result object indicating success or failure.

        Example:
            >>> globals = GlobalVars()
            >>> globals.set("api_key", "12345", overwrite=True)
            >>> result = globals.delete("api_key")
            >>> if result.success and not globals.exists("api_key").data:
            >>>     print("api_key deleted successfully.")
            >>> else:
            >>>     print("Failed to delete api_key.")
        """
        try:
            with self.__lock__:
                if not self.exists(key):
                    raise KeyError(f"Global variable '{key}' does not exist.")
                
                del self.__vars__[key]
                self.log.log_message("INFO", f"Global variable '{key}' deleted.")
                return Result(True, None, None, f"Global variable '{key}' deleted.")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to delete global variable '{key}': {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def clear(self) -> Result:
        """
        Clear all global variables.

        Returns:
            Result: A Result object indicating success or failure.

        Example:
            >>> globals = GlobalVars()
            >>> globals.set("api_key", "12345", overwrite=True)
            >>> globals.set("user_id", "user_01", overwrite=True)
            >>> result = globals.clear()
            >>> if result.success and len(globals.list_vars().data) == 0:
            >>>     print("All global variables cleared.")
            >>> else:
            >>>     print(result.error)
        """
        try:
            with self.__lock__:
                for name in list(self.__vars__.keys()):
                    del self.__vars__[name]

                self.log.log_message("INFO", "All global variables cleared.")
                return Result(True, None, None, "All global variables cleared.")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to clear global variables: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def list_vars(self) -> Result:
        """
        List all global variables.

        Returns:
            Result: A Result object containing a list of global variable names.

        Example:
            >>> globals = GlobalVars()
            >>> globals.set("api_key", "12345", overwrite=True)
            >>> globals.set("user_id", "user_01", overwrite=True)
            >>> result = globals.list_vars()
            >>> if result.success:
            >>>     print(result.data)  # Output: ['api_key', 'user_id']
            >>> else:
            >>>     print(result.error)
        """
        try:
            with self.__lock__:
                self.log.log_message("INFO", "Listing all global variables.")
                return Result(True, None, None, list(self.__vars__.keys()))
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to list global variables: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def exists(self, key: str) -> Result:
        """
        Check if a global variable exists.

        Args:
            - key : The name of the global variable.

        Returns:
            Result: A Result object containing a boolean indicating existence.

        Example:
            >>> globals = GlobalVars()
            >>> globals.set("api_key", "12345", overwrite=True)
            >>> result = globals.exists("api_key")
            >>> if result.success:
            >>>     print(result.data)  # Output: True
            >>> else:
            >>>     print(result.error)
        """
        try:
            with self.__lock__:
                exists = key in self.__vars__
                self.log.log_message("INFO", f"Checked existence of global variable '{key}': {exists}")
                return Result(True, None, None, exists)
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to check existence of global variable '{key}': {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def __getattr__(self, name):
        """
        Get a global variable by attribute access.

        Args:
            - name : The name of the global variable.

        Returns:
            The value of the global variable.

        Example:
            >>> globals = GlobalVars()
            >>> globals.api_key = "12345"
            >>> print(globals.api_key)  # Output: 12345 ( this part uses __getattr__ )
        """
        try:
            with object.__getattribute__(self, '__lock__'):
                if not self.exists(name).data:
                    raise KeyError(f"Global variable '{name}' does not exist.")
                return self.__vars__[name]
        except Exception as e:
            return self._exception_tracker.get_exception_return(e)
        
    def __setattr__(self, name, value):
        """
        Set a global variable by attribute access.

        Args:
            - name : The name of the global variable.
            - value : The value to set.

        Returns:
            Result: A Result object indicating success or failure.

        Example:
            >>> globals = GlobalVars()
            >>> globals.api_key = "12345" ( this part uses __setattr__ )
            >>> print(globals.api_key)  # Output: 12345
        """
        # During initialization, use normal attribute setting
        try:
            if object.__getattribute__(self, '__initializing__'):
                object.__setattr__(self, name, value)
                return
        except AttributeError:
            # __initializing__ not set yet, must be during early init
            object.__setattr__(self, name, value)
            return
        
        # After initialization, store in __vars__ dict
        try:
            with object.__getattribute__(self, '__lock__'):
                if name is None or not isinstance(name, str) or name.strip() == "":
                    raise ValueError("name must be a non-empty string.")
                
                vars_dict = object.__getattribute__(self, '__vars__')
                vars_dict[name] = value
        except Exception as e:
            exception_tracker = object.__getattribute__(self, '_exception_tracker')
            return exception_tracker.get_exception_return(e)
        
    def __call__(self, key: str, value: Optional[object]=None, overwrite: bool=False) -> Result:
        """
        Get or set a global variable using call syntax.
        If value is provided, set the variable; otherwise, get it.

        Args:
            - key : The name of the global variable.
            - value : The value to set (optional).
            - overwrite : If True, overwrite existing variable when setting. Defaults to False.

        Returns:
            Result: A Result object containing the value when getting, or indicating success/failure when setting

        Example:
            >>> globals = GlobalVars()
            >>> globals("api_key", "12345", overwrite=True)  # Set api_key
            >>> result = globals("api_key")  # Get api_key
            >>> if result.success:
            >>>     print(result.data)  # Output: 12345
            >>> else:
            >>>     print(result.error)
        """
        try:
            if value is not None:
                return self.set(key, value, overwrite)
            else:
                return self.get(key)
        except Exception as e:
            return self._exception_tracker.get_exception_return(e)