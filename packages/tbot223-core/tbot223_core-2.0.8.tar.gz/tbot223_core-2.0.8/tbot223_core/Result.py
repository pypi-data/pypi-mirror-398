#external Modules
from typing import Any, NamedTuple, Optional

#internal Modules

class Result(NamedTuple):
    """
    Class representing operation results in CoreV2

    NamedTuple version

    Attributes:
        success (bool): Indicates if the operation was successful.
        error (Optional[str]): Error message if the operation failed.
        context (Optional[str]): Additional context about the operation.
        data (Any): Data returned from the operation.
    """
    success: bool
    error: Optional[str]
    context: Optional[str]
    data: Any