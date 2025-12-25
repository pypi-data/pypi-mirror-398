import time
import psutil

_scale = {'KB': 1024, 'MB': 1024 * 1024, 'GB': 1024 * 1024 * 1024, }


def get_virtual_memory(unit='GB'):
    memory_tuple = psutil.virtual_memory()
    _key = unit.upper()
    memory_dict = {
        "total": (memory_tuple[0] / _scale[_key], _key),
        "available": (memory_tuple[1] / _scale[_key], _key),
        "percent": (memory_tuple[2], '%'),
        "used": (memory_tuple[3] / _scale[_key], _key),
        "free": (memory_tuple[4] / _scale[_key], _key),
    }
    return memory_dict


def elapsed_since(start):
    return time.strftime("%H:%M:%S", time.gmtime(time.time() - start))


def get_process_memory(unit='MB'):
    return psutil.Process().memory_info().rss / _scale[unit.upper()]


def _profile(func):
    """
    注意，这个装饰器只能得到函数推出后的内存增量，而要函数内的内存增量不应用此装饰器
    若要方便调试对函数的使用，请使用 memory_profiler这个包
    from memory_profiler import profile
    @profile
    def func():
        ...
    """

    def wrapper(*args, **kwargs):
        _key = "MB"
        mem_before = get_process_memory(_key)
        start = time.time()
        result = func(*args, **kwargs)
        elapsed_time = elapsed_since(start)
        mem_after = get_process_memory(_key)
        print(
            f"{func.__name__}: memory before: {mem_before:.2f} {_key}, after: {mem_after:.2f} {_key}, consumed: {mem_after - mem_before:.2f} {_key}; exec time: {elapsed_time}"
        )
        return result

    return wrapper

