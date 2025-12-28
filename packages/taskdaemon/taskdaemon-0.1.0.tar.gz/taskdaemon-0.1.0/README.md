# TaskDaemon Python SDK

## Installation

```bash
pip install taskdaemon
```

## Usage

```python
from taskdaemon import run, Task, Success, Error

def handler(task: Task) -> Success | Error:
    message = task.task_data.get("message", "")
    return Success({"echoed": message})

run(handler)
```

## Dockerfile

```dockerfile
FROM python:3.11-slim
COPY handler.py /handler.py
CMD ["python", "-u", "/handler.py"]
```
