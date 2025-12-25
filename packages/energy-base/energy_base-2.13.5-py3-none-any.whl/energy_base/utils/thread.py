import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Any, Iterable, Tuple, Dict, Union


class ThreadPoolException(Exception):
    """Exception to wrap the error in each task."""

    def __init__(self, func: str, exception: Exception):
        self.func = func
        self.exception = exception
        super().__init__(f"Exception in {func}: {exception}")


def parallel_execute(
        *tasks: Union[
            Callable,  # func
            Tuple[Callable, Iterable],  # (func, args)
            Tuple[Callable, Iterable, Dict[str, Any]]  # (func, args, kwargs)
        ],
        max_workers: int = None
) -> list[Any]:
    """
    Executes multiple functions in parallel.
    Each can be without arguments or with args/kwargs.

    Example:
        parallel_execute(func1, func2)
        parallel_execute((func1, (1, 2)), (func2, (), {"x": 5}))

    The sequence is preserved.

    :return: Result list or ThreadPoolException objects
    """
    if not tasks:
        return []

    cpu_count = multiprocessing.cpu_count()
    max_workers = max_workers or min(cpu_count * 10, len(tasks))
    results = [None] * len(tasks)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for i, task in enumerate(tasks):
            # Task unpacking
            if callable(task):
                func, args, kwargs = task, (), {}
            elif isinstance(task, tuple):
                func = task[0]
                args = task[1] if len(task) > 1 else ()
                kwargs = task[2] if len(task) > 2 else {}
            else:
                raise ValueError(f"Invalid task format: {task}")

            futures[executor.submit(func, *args, **kwargs)] = i

        for future in as_completed(futures):
            idx = futures[future]
            func = tasks[idx][0] if isinstance(tasks[idx], tuple) else tasks[idx]
            func_name = getattr(func, "__name__", str(func))
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = ThreadPoolException(func=func_name, exception=e)

    return results
