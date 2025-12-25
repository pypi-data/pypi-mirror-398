#external Modules
from typing import List, Union, Any, Optional
from pathlib import Path
import tempfile
import json
import shutil
import stat
import os
import logging
if os.name != 'nt':
    import fcntl
else:
    import msvcrt

#internal Modules
from tbot223_core.Result import Result
from tbot223_core.Exception import ExceptionTracker
from tbot223_core import Utils, LogSys

class FileManager:
    """
    The FileManager class provides various file management functionalities such as reading, writing, deleting files and directories, and listing files.

    Attributes:
        - is_logging_enabled (bool): Flag to enable or disable logging.
        - is_debug_enabled (bool): Flag to enable or disable debug mode.
        - base_dir (Union[str, Path]): Base directory for file operations.
        - logger_manager_instance (LogSys.LoggerManager): Instance of LoggerManager for logging.
        - logger (Any): Logger instance for logging messages.
        - log_instance (LogSys.Log): Instance of Log for logging messages.
        - Utils_instance (Utils.Utils): Instance of Utils for utility functions.

    Methods:
        - atomic_write(file_path, data) -> Result:
            Atomically write data to a file.

        - read_file(file_path, as_bytes=False) -> Result:
            Read the content of a file.

        - write_json(file_path, data, indent=4) -> Result:
            Write JSON serializable data to a file in JSON format.

        - read_json(file_path) -> Result:
            Read JSON content from a file and parse it into a Python object.

        - list_of_files(dir_path, extensions=None, only_name=False) -> Result:
            List all files in a directory, optionally filtering by extensions.
            
        - delete_file(file_path) -> Result:
            Delete a file.

        - delete_directory(dir_path) -> Result:
            Delete a directory and all its contents.

        - create_directory(dir_path) -> Result:
            Create a directory.
    """

    def __init__(self, is_logging_enabled: bool=True, is_debug_enabled: bool=False,
                 base_dir: Union[str, Path]=None,
                 logger_manager_instance: Optional[LogSys.LoggerManager]=None, logger: Optional[logging.Logger]=None, 
                 log_instance: Optional[LogSys.Log]=None, Utils_instance: Optional[Utils.Utils]=None):
        
        # Initialize paths
        self._BASE_DIR = Path(base_dir) if base_dir is not None else Path.cwd()

        # Initialize Flags
        self.is_logging_enabled = is_logging_enabled
        self.is_debug_enabled = is_debug_enabled

        # Initialize classes
        self._exception_tracker = ExceptionTracker()
        self._logger_manager = None
        self.logger = None
        if self.is_logging_enabled:
            self._logger_manager = logger_manager_instance or LogSys.LoggerManager(base_dir=self._BASE_DIR / "logs", second_log_dir="file_manager")
            self._logger_manager.make_logger("FileManagerLogger")
            self.logger = logger or self._logger_manager.get_logger("FileManagerLogger").data
        self.log = log_instance or LogSys.Log(logger=self.logger)
        self._utils = Utils_instance or Utils.Utils()

        self.log.log_message("INFO", "FileManager initialized.")

    # internal Methods
    @staticmethod
    def _handle_exc(func, path, exc_info):
        """
        Handle exceptions during file operations by changing file permissions and retrying.
        Args:
            - func : The function to retry.
            - path : The path to the file or directory.
            - exc_info : Exception information.
            
        Example:
            >>> file_manager._handle_exc(os.remove, "some/protected/file.txt", exc_info)
        """
        exc_type, exc_value, exc_tb = exc_info
        if not issubclass(exc_type, PermissionError):
            raise exc_value
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def _str_to_path(self, path: Any) -> Path:
        """
        Convert string path to Path object

        Args:
            - path : The path to convert.

        Returns:
            Path: The converted Path object.

        Example:
            >>> path_obj = file_manager._str_to_path("some/directory/file.txt")
            >>> print(type(path_obj))
            >>> # Output: <class 'pathlib.Path'>
        """
        if isinstance(path, Path):
            return path
        return self._utils.str_to_path(path).data
    
    @staticmethod
    def _lock(file: Path, mode: int):
        """
        Lock a file using fcntl (Unix) or msvcrt (Windows).

        Args:
            - file : The file object to lock.
            - mode : The lock mode (fcntl.LOCK_EX, fcntl.LOCK_SH for Unix; msvcrt.LK_LOCK, msvcrt.LK_RLCK for Windows, 1 is lock, 0 is unlock).

        Returns:
            This method does not return any value.

        Example:
            >>> with open("example.txt", "r+") as f:
            >>>     file_manager._lock(f, 1)  # Lock the file
            >>>     # Perform file operations
            >>>     file_manager._lock(f, 0)  # Unlock the file
        """
        if os.name != 'nt':
            if mode == 1:
                fcntl.flock(file, fcntl.LOCK_EX)
            else:
                fcntl.flock(file, fcntl.LOCK_UN)
        else:
            if mode == 1:
                msvcrt.locking(file.fileno(), msvcrt.LK_LOCK, os.path.getsize(file.name))
            else:
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, os.path.getsize(file.name))
            

    def atomic_write(self, file_path: Union[str, Path], data: Any) -> Result:
        """
        Atomically write "data" to "file_path"

        - If data is bytes, write in binary mode; if str, write in text mode with utf-8 encoding.
        - Use a temporary file in the same directory and rename it to ensure atomicity.
        - Ensure that the parent directory of file_path exists; create it if it does not.
        - Flush and sync data to disk before renaming to minimize data loss risk.

        Args:
            - file_path : The path to the file where data will be written.
            - data : The data to write to the file. Can be str or bytes.

        Returns:
            Result: A Result object indicating success or failure of the write operation.

        Example:
            >>> result = file_manager.atomic_write("example.txt", "Hello, World!")
            >>> if result.success:
            >>>     print("Write successful!")
            >>> else:
            >>>     print(f"Write failed: {result.error_message}")
        """
        try:
            temp_path = None
            file_path = self._str_to_path(file_path)
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            is_bytes = isinstance(data, bytes)
            mode = 'wb' if is_bytes else 'w'
            encoding = None if is_bytes else 'utf-8'

            def replace_temp_with_target(temp_path: Path, target_path: Path):
                if os.name == 'nt':
                    os.replace(temp_path, target_path)
                    return
                with open(target_path, "a+b") as f:
                    self._lock(f, 1)
                    try:
                        os.replace(temp_path, target_path)
                    finally:
                        self._lock(f, 0)

            with tempfile.NamedTemporaryFile(mode, delete=False, dir=str(file_path.parent), encoding=encoding) as temp:
                temp_path = Path(temp.name)
                temp.write(data)
                temp.flush()
                try:
                    os.fsync(temp.fileno())
                except (AttributeError, OSError):
                    pass  # os.fsync not available on some platforms
                temp.close()
                replace_temp_with_target(temp_path, file_path)

            self.log.log_message("INFO", f"Successfully wrote to {file_path}")
            return Result(True, None, None, f"Successfully wrote to {file_path}")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to write to {file_path}: {e}")
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    self.log.log_message("INFO", f"Temporary file {temp_path} deleted.")
            except Exception as ex:
                self.log.log_message("ERROR", f"Failed to delete temporary file {temp_path}: {ex}")
            return self._exception_tracker.get_exception_return(e)
        
    def read_file(self, file_path: Union[str, Path], as_bytes: bool=False) -> Result:
        """
        Read the content of the file at "file_path"

        - If as_bytes is True, read in binary mode; otherwise, read in text mode with utf-8 encoding.
        - Return the content in the data field of the Result object.
        - Use file locking to ensure safe read operations.

        Args:
            - file_path : The path to the file to read.
            - as_bytes (bool, optional): If True, read the file in binary mode.
            
        Returns:
            Result: A Result object containing the file content in the data field.

        Example:
            >>> result = file_manager.read_file("example.txt")
            >>> if result.success:
            >>>     print(result.data)
            >>> else:
            >>>     print(f"Read failed: {result.error_message}")
        """
        try:
            file_path = self._str_to_path(file_path)

            mode = 'rb' if as_bytes else 'r'
            encoding = None if as_bytes else 'utf-8'
            LOCK = (os.path.getsize(file_path) > 1024 * 1024 * 10)  # Lock files larger than 10MB

            def safe_read(f, lock):
                if lock:
                    self._lock(f, 1)
                try:
                    content = f.read()
                finally:
                    if lock:
                        self._lock(f, 0)
                return content
            
            with open(file_path, mode, encoding=encoding) as f:
                content = safe_read(f, LOCK)

            self.log.log_message("INFO", f"Successfully read from {file_path}")
            return Result(True, None, None, content)
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to read from {file_path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def write_json(self, file_path: Union[str, Path], data: Any, indent: int=4) -> Result:
        """
        Write JSON serializable "data" to "file_path" in JSON format

        - Use atomic_write to ensure atomicity.
        - Pretty-print JSON with specified indentation.

        Args:
            - file_path : The path to the file where JSON data will be written.
            - data : The JSON serializable data to write to the file.
            - indent (int, optional): Number of spaces for indentation in the JSON file. Defaults to 4.
        
        Returns:
            Result: A Result object indicating success or failure of the write operation.

        Example:
            >>> data = {"name": "Alice", "age": 30}
            >>> result = file_manager.write_json("data.json", data)
            >>> if result.success:
            >>>     print("JSON write successful!")
            >>> else:
            >>>     print(f"JSON write failed: {result.error_message}")
        """
        try:
            file_path = self._str_to_path(file_path)
            json_data = json.dumps(data, indent=indent, ensure_ascii=False)
            write_result = self.atomic_write(file_path, json_data)
            if not write_result.success:
                return write_result
            
            self.log.log_message("INFO", f"Successfully wrote JSON to {file_path}")
            return Result(True, None, None, f"Successfully wrote JSON to {file_path}")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to write JSON to {file_path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def read_json(self, file_path: Union[str, Path]) -> Result:
        """
        Read JSON content from "file_path" and parse it into a Python object

        - Return the parsed object in the data field of the Result object.

        Args:
            - file_path : The path to the JSON file to read.

        Returns:
            Result: A Result object containing the parsed JSON data in the data field.

        Example:
            >>> result = file_manager.read_json("data.json")
            >>> if result.success:
            >>>     print(result.data)
            >>> else:
            >>>     print(f"JSON read failed: {result.error_message}")
        """
        try:
            file_path = self._str_to_path(file_path)
            if file_path.exists() is False:
                raise FileNotFoundError(f"File not found: {file_path}")
            if file_path.suffix.lower() != '.json':
                raise ValueError("File extension is not .json")

            read_result = self.read_file(file_path)
            if not read_result.success:
                return read_result
            
            self.log.log_message("INFO", f"Successfully read JSON from {file_path}")
            return Result(True, None, None, json.loads(read_result.data))
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to read JSON from {file_path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def list_of_files(self, dir_path: Union[str, Path], extensions: List[str]=None, only_name: bool = False) -> Result:
        """
        List all files in the directory at "dir_path"

        - If "extension" is provided, filter files by the given extension (case-insensitive).
        - Return the list of file paths in the data field of the Result object.
        - If only_name is True, return only file names instead of full paths.

        Args:
            - dir_path : The path to the directory to list files from.
            - extensions : List of file extensions to filter by. Defaults to None (no filtering).
            - only_name : If True, return only file names instead of full paths. Defaults to False.
            
        Returns:
            Result: A Result object containing the list of file paths or names in the data field.

        Example:
            >>> result = file_manager.list_of_files("some/directory", extensions=[".txt", ".md"], only_name=True)
            >>> if result.success:
            >>>     print(result.data)
            >>> else:
            >>>     print(f"Listing files failed: {result.error_message}")
        """
        try:
            dir_path = self._str_to_path(dir_path)
            extensions = [ext.lower() for ext in extensions] if extensions else []

            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")

            def is_matching_file(item: Path, list_obj: list):
                if extensions == [] or item.suffix.lower() in extensions:
                    list_obj.append(item.stem if only_name else str(item))

            files = []
            for item in dir_path.iterdir():
                if item.is_dir():
                    continue
                is_matching_file(item, files)

            self.log.log_message("INFO", f"Successfully listed files in {dir_path}")
            return Result(True, None, None, files)
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to list files in {dir_path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def exist(self, path: Union[str, Path]) -> Result:
        """
        Check if the file or directory at "path" exists

        Args:
            - path : The path to the file or directory to check.

        Returns:
            Result: A Result object containing a boolean in the data field indicating existence.

        Example:
            >>> result = file_manager.exist("some/file_or_directory")
            >>> if result.success:
            >>>     if result.data:
            >>>         print("Path exists!")
            >>>     else:
            >>>         print("Path does not exist.")
            >>> else:
            >>>     print(f"Existence check failed: {result.error_message}")
        """
        try:
            path = self._str_to_path(path)
            exists = path.exists()

            self.log.log_message("INFO", f"Existence check for {path}: {exists}")
            return Result(True, None, None, exists)
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to check existence for {path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def delete_file(self, file_path: Union[str, Path]) -> Result:
        """
        Delete the file at "file_path"

        - If the file does not exist, raise FileNotFoundError.

        Args:
            - file_path : The path to the file to delete.

        Returns:
            Result: A Result object indicating success or failure of the delete operation.
        
        Example:
            >>> result = file_manager.delete_file("example.txt")
            >>> if result.success:
            >>>     print("File deleted successfully!")
            >>> else:
            >>>     print(f"File deletion failed: {result.error_message}")
        """
        try:
            file_path = self._str_to_path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            try:
                file_path.unlink()
            except PermissionError:
                self.log.log_message("ERROR", f"Permission denied when deleting {file_path}, attempting to change permissions and retry.")  
                os.chmod(file_path, stat.S_IWRITE)
                file_path.unlink()
                
            self.log.log_message("INFO", f"Successfully deleted {file_path}")
            return Result(True, None, None, f"Successfully deleted {file_path}")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to delete {file_path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def delete_directory(self, dir_path: Union[str, Path]) -> Result:
        """
        Delete the directory at "dir_path" and all its contents

        - If the directory does not exist, raise FileNotFoundError.

        Args:
            - dir_path : The path to the directory to delete.
            
        Returns:
            Result: A Result object indicating success or failure of the delete operation.

        Example:
            >>> result = file_manager.delete_directory("some/directory")
            >>> if result.success:
            >>>     print("Directory deleted successfully!")
            >>> else:
            >>>     print(f"Directory deletion failed: {result.error_message}")
        """
        try:
            dir_path = self._str_to_path(dir_path)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")

            try:
                shutil.rmtree(dir_path)
            except PermissionError:
                self.log.log_message("ERROR", f"Permission denied when deleting {dir_path}, attempting to change permissions and retry.")
                shutil.rmtree(dir_path, onexc=self._handle_exc)

            self.log.log_message("INFO", f"Successfully deleted directory {dir_path}")
            return Result(True, None, None, f"Successfully deleted directory {dir_path}")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to delete directory {dir_path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    def create_directory(self, dir_path: Union[str, Path]) -> Result:
        """
        Create the directory at "dir_path"

        - If the directory already exists, do nothing.

        Args:
            - dir_path : The path to the directory to create.

        Returns:
            Result: A Result object indicating success or failure of the create operation.

        Example:
            >>> result = file_manager.create_directory("some/new/directory")
            >>> if result.success:
            >>>     print("Directory created successfully!")
            >>> else:
            >>>     print(f"Directory creation failed: {result.error_message}")
        """
        try:
            dir_path = self._str_to_path(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)

            self.log.log_message("INFO", f"Successfully created directory {dir_path}")
            return Result(True, None, None, f"Successfully created directory {dir_path}")
        except Exception as e:
            self.log.log_message("ERROR", f"Failed to create directory {dir_path}: {e}")
            return self._exception_tracker.get_exception_return(e)
        
    # __enter__ and __exit__
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        pass