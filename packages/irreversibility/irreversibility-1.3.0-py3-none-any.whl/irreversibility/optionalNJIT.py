
try:
    from numba import njit
    numba_installed = True
except ImportError:
    numba_installed = False

forceNoNumba = False

def optional_njit(*args, **kwargs):
    def decorator(func):
        if numba_installed and not forceNoNumba:
            return njit(*args, **kwargs)(func)
        else:
            return func
    return decorator


