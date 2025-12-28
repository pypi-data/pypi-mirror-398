import json
import sys
from dataclasses import dataclass
from typing import Any, Callable, Union


@dataclass
class Task:
    task_id: str
    task_type: str
    task_data: dict
    attempt: int


@dataclass
class Success:
    result: Any


@dataclass
class Error:
    error: str
    retryable: bool = False


Result = Union[Success, Error]


def run(handler: Callable[[Task], Result]) -> None:
    for line in sys.stdin:
        task = Task(**json.loads(line))
        try:
            result = handler(task)
            if isinstance(result, Success):
                response = {"status": "success", "result": result.result}
            else:
                response = {"status": "error", "error": result.error, "retryable": result.retryable}
        except Exception as e:
            response = {"status": "error", "error": str(e), "retryable": False}
        print(json.dumps(response), flush=True)
