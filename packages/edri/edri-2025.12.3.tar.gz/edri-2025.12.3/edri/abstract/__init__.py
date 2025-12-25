from .manager.manager_base import ManagerBase
from .manager.manager_priority_base import ManagerPriorityBase


def request(func=None, /, *, cache: str = None):
    def wrapper(func):
        func.__purpose__ = "request"
        func.__cache__ = cache
        return func

    if func is None:
        return wrapper

    return wrapper(func)


def response(func):
    func.__purpose__ = "response"
    return func


__all__ = ["ManagerBase", "ManagerPriorityBase", "request", "response"]
