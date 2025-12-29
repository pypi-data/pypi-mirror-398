# -*- coding: utf-8 -*-
import time


class Result:
    def __init__(self, e):
        self.e = e


def measure_(func, *args, **kwargs):
    """
    Measures the execution time of a function and returns the result along with elapsed time in a dictionary.

    :param func: The function to be measured.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: A dict containing 'result' (either return value or exception) and 'elapsed_time' (in seconds).
    """
    return_result = {}
    start_time = time.time()

    try:
        result = func(*args, **kwargs)
    except Exception as e:
        end_time = time.time()
        elapsed_time = f"{end_time - start_time:.2f}"
        return_result['result'] = Result(str(e))
        return_result['elapsed_time'] = elapsed_time
    else:
        end_time = time.time()
        elapsed_time = f"{end_time - start_time:.2f}"
        return_result['result'] = result
        return_result['elapsed_time'] = elapsed_time

    return return_result
