from dataclasses import dataclass
from typing import Callable

def default_error_presenter(error: Exception) -> bool:
    return False # let caller re-raise error

@dataclass
class CurliConfig:
    error_presenter: Callable[[Exception], bool] = default_error_presenter
