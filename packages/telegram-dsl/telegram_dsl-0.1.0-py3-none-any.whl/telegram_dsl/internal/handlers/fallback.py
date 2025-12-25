from collections import defaultdict

# Maintain a fallback per group, with a global fallback as default.
_fallbacks = defaultdict(lambda: None)
_fallbacks["__global__"] = None


def register_fallback(func=None, *, group="__global__"):
    if func is None:
        return lambda f: register_fallback(f, group=group)
    _fallbacks[group] = func
    return func


def get_fallback(group="__global__"):
    return _fallbacks.get(group) or _fallbacks["__global__"]
