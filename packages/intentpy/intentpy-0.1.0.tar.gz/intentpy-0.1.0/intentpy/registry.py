CONDITIONS = {}
FALLBACKS = {}


def condition(name: str):
    """
    Register a named precondition.
    """
    def decorator(fn):
        CONDITIONS[name] = fn
        return fn
    return decorator


def fallback(name: str):
    """
    Register a named fallback handler.
    """
    def decorator(fn):
        FALLBACKS[name] = fn
        return fn
    return decorator
