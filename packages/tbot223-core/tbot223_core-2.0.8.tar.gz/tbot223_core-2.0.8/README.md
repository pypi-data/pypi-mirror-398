# Core
It provides various utility functions. Return values ​​are always returned in a Result object (except for internal functions). Functions such as file writing and reading have been implemented to ensure stable operation.

## Result

'''python
Result
    (
    success: bool,
    error: Optional[str],
    context: Optional[str],
    data: Any
    )

error_info(Result.data)

    {
        "success": bool,
        "error": {
            "type": "ExceptionType",
            "message": "Exception message"
        },
        "location": {
            "file": "filename",
            "line": X,
            "function": "function_name"
        },
        "timestamp": "YYYY-MM-DD HH:MM:SS",
        "input_context": {
            "user_input": user_input,
            "params": params
        },
        "traceback": traceback.format_exc(),
        "computer_info": {
            "OS": "OS name",
            "OS_version": "OS version",
            "Release": "OS release",
            "Architecture": "Machine architecture",
            "Processor": "Processor info",
            "Python_Version": "Python version",
            "Python_Executable": "Path to Python executable",
            "Current_Working_Directory": "Current working directory"
        }
    }
