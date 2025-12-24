import time
from contextlib import ContextDecorator
from typing import Callable, Any, Dict, Optional

class Benchmarker(ContextDecorator):
    """
    A tool for measuring execution time and throughput, with GenAI workflows
    in mind.
    
    Can be used as a decorator, a context manager, or a functional wrapper.
    """

    def __init__(self):
        self.start_time = 0
        self.execution_time = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.execution_time = time.perf_counter() - self.start_time

    @staticmethod
    def measure_execution_time(func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Wraps a function call to measure its execution time.

        Args:
            func (Callable): The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Dict[str, Any]: A dictionary containing 'function_output' and 'execution_time'.
        """
        start = time.perf_counter()
        function_output = func(*args, **kwargs)
        duration = time.perf_counter() - start
        
        return {
            "function_output": function_output,
            "execution_time": duration
        }

    def calculate_throughput(self, unit_count: int, duration: float | None = None, dp: int = 2) -> float:
        """
        Calculates throughput (e.g., tokens per second, time per image, etc.).

        Args:
            unit_count (int): The number of units processed (e.g., token count).
            duration (float): The time taken in seconds. Defauls to self.execution_time
            dp (int): Number of decimal places to round output to. Default 2.

        Returns:
            float: Units per second, rounded to dp decimal places.
        """
        if not duration:
            duration = self.execution_time
        if duration <= 0:
            return 0.0

        throughput = round(unit_count / duration, dp)
        
        return throughput