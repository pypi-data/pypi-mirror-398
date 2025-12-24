import time
import numpy as np
from typing import Callable


def format_time(nanoseconds: float) -> str:
    if nanoseconds < 1e3:
        return f"{nanoseconds:.2f} ns"
    elif nanoseconds < 1e6:
        return f"{nanoseconds / 1e3:.2f} μs"
    elif nanoseconds < 1e9:
        return f"{nanoseconds / 1e6:.2f} ms"
    else:
        return f"{nanoseconds / 1e9:.2f} s"


def bench(name: str, func: Callable[[], None], num_iterations: int = 10_000) -> None:
    func()
    elapseds = np.zeros(num_iterations)
    for i in range(num_iterations):
        start = time.perf_counter_ns()
        func()
        elapseds[i] = time.perf_counter_ns() - start
    mean = elapseds.mean()
    std = elapseds.std()
    min = elapseds.min()
    max = elapseds.max()
    print(name)
    print(
        f"mean: {format_time(mean)}, min: {format_time(min)}, max: {format_time(max)}, stddev: {format_time(std)}"
    )
