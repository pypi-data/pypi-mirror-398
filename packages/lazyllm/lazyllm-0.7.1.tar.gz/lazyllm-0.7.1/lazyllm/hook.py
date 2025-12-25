from abc import ABC, abstractmethod
import inspect
import ast

class LazyLLMHook(ABC):
    """Abstract base class for LazyLLM's hook system, used to insert custom logic before and after function or method execution.

This class is an abstract base class (ABC) that defines the basic interface for the hook system. By inheriting from this class and implementing its abstract methods, you can create custom hooks to monitor, log, or modify function execution processes.

Args:
    obj: The object to monitor (usually a function or method). This object will be stored in the hook instance for use by other methods.

**Note**: This class is an abstract base class and cannot be instantiated directly. You must inherit from this class and implement all abstract methods to use it.
"""

    @abstractmethod
    def __init__(self, obj):
        pass

    @abstractmethod
    def pre_hook(self, *args, **kwargs):
        """Pre-hook method, called before the monitored function executes.

This is an abstract method and must be implemented in subclasses.

Args:
    *args: Positional arguments passed to the monitored function.
    **kwargs: Keyword arguments passed to the monitored function.
"""
        pass

    @abstractmethod
    def post_hook(self, output):
        """Post-hook method, called after the monitored function executes.

This is an abstract method and must be implemented in subclasses.

Args:
    output: The return value of the monitored function.
"""
        pass

    def report():  # This is not an abstract method, but it is required to be implemented in subclasses.
        """Generate a report of the hook execution.

This is an abstract method and must be implemented in subclasses.
"""
        raise NotImplementedError


def _check_and_get_pre_assign_number(func):
    func_node = ast.parse(inspect.getsource(func)).body[0]

    yield_nodes = [n for n in ast.walk(func_node) if isinstance(n, ast.Yield)]
    yield_count = len(yield_nodes)
    if yield_count == 0: return
    elif yield_count > 1: raise ValueError('function can have at most one yield')

    left_count = 0
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign):
            if any(isinstance(sub, ast.Yield) for sub in ast.walk(node.value)):
                target = node.targets[0]
                left_count = len(target.elts) if isinstance(target, ast.Tuple) else 1
                if left_count > 1: raise ValueError('function can have at most one pre-assign')
                break
    return left_count


class LazyLLMFuncHook(LazyLLMHook):
    """Helper class for hooking functions. if the function is a generator function, statements before yield
will be executed as pre_hook, and statements after yield will be executed as post_hook.

Args:
    func: The function to hook.
"""
    def __init__(self, func):
        self._func = func
        self._isgeneratorfunction = inspect.isgeneratorfunction(func)
        if self._isgeneratorfunction:
            self._left_count = _check_and_get_pre_assign_number(func)

    def pre_hook(self, *args, **kwargs):
        if self._isgeneratorfunction:
            self._generator = self._func(*args, **kwargs)
            next(self._generator)
        else:
            self._func(*args, **kwargs)

    def post_hook(self, output):
        assert self._isgeneratorfunction, 'post_hook is only supported for generator functions'
        try:
            self._generator.send(output) if self._left_count == 1 else next(self._generator)
        except StopIteration: pass
