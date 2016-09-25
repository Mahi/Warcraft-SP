"""A module with :func`cooldown` function for method cooldowns."""

# Python 3 imports
import functools
import time

__all__ = (
    'cooldown',
    )


def _static_cooldown(cooldown):
    """Return a cooldown.

    Used to convert a static integer cooldown into a function.
    """
    return cooldown


def cooldown(cooldown, fail_callback=None):
    """Decorate a method with a cooldown.

    :param int|callable cooldown:
        A static cooldown or a function for getting the cooldown
    :param callable|None fail_callback:
        A function to call if the method is still on cooldown
    """
    def decorator(method):
        nonlocal cooldown
        if isinstance(cooldown, int):
            cooldown = functools.partial(_static_cooldown, cooldown)
        return _UnboundMethodWrapper(method, cooldown, fail_callback)
    return decorator


class _MethodWrapper:
    """A base class for method wrappers.

    Wraps a method to provide it with a cooldown. This class exists
    simply to reduce duplicate :meth:`__init__` methods from the two
    main method wrapper classes, which both need the same information.
    """

    def __init__(self, method, cooldown_func, fail_callback):
        """Initialize the wrapper around a method.

        :param callable method:
            Method to wrap
        :param callable cooldown_func:
            A function for getting the cooldown
        :param callable|None fail_callback:
            A function to call if the method is still on cooldown
        """
        self.method = method
        self.__doc__ = method.__doc__
        self.cooldown_func = cooldown_func
        self.fail_callback = fail_callback


class _UnboundMethodWrapper(_MethodWrapper):
    """A wrapper around unbound methods to add a cooldown to them.

    Handles the binding of a method to an object whenever the object
    accesses the method through the dot operator (``.``).
    Binds the two together using :class:`_BoundMethodWrapper` which
    handles the actual calling and cooldown of the method.
    """

    @functools.wraps(_MethodWrapper.__init__)
    def __init__(self, method, cooldown_func, fail_callback):
        super().__init__(method, cooldown_func, fail_callback)
        self._bindings = {}

    def __get__(self, obj, type_=None):
        """Get a bound method wrapper for an object.

        Binds the accessing ``obj`` to :attr:`method` and returns
        a :class:`_BoundMethodWrapper` instance wrapped around them.
        """
        if obj is None:
            return self
        bound = self._bindings.get(id(obj), None)
        if bound is None:
            bound = self._bindings[id(obj)] = _BoundMethodWrapper(
                obj, self.method, self.cooldown_func, self.fail_callback)
        return bound


class _BoundMethodWrapper(_MethodWrapper):
    """A wrapper around bound methods to handle their calling.

    When called, checks the cooldown situation and either calls
    the original :attr:`method` or :attr:`fail_callback` if the method
    was still on cooldown (and :attr:`fail_callback` is not ```None``).

    Implements the :attr:`cooldown` property for getting and setting
    the methods's remaining cooldown. Also implements
    the :meth:`get_max_cooldown` method for getting the method's
    maximum cooldown (which might be dynamic, thus the method),
    and a read-only :attr:`previous_cooldown` which contains the current
    cooldown which was calculated during the previous call to the method
    (again, because the cooldown might be dynamic).
    """

    def __init__(self, obj, method, cooldown_func, fail_callback):
        """Initialize the wrapper around a method.

        :param object obj:
            Object calling the method
        :param callable method:
            Method to wrap
        :param callable cooldown_func:
            A function for getting the cooldown
        :param callable|None fail_callback:
            A function to call if the method is still on cooldown
        """
        self.obj = obj
        super().__init__(method, cooldown_func, fail_callback)
        self._last_cooldown = 0
        self._last_call_time = 0

    @property
    def remaining_cooldown(self):
        dt = time.time() - self._last_call_time
        return max(0, self._last_cooldown - dt)

    @remaining_cooldown.setter
    def remaining_cooldown(self, value):
        self._last_cooldown = value
        self._last_call_time = time.time()

    def get_max_cooldown(self, *args, **kwargs):
        """Get the method's maximum cooldown.

        Forwards the provided arguments as well as the bound object
        to :attr:`cooldown_func` and returns whatever it returned.
        """
        return self.cooldown_func(self.obj, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Attempt to call the wrapped method.

        Forwards the calling object to the original wrapped method
        (as the ``self`` argument) if the method is not on cooldown,
        or calls :attr:`fail_callback` if it is still on cooldown.
        """
        if self.remaining_cooldown > 0:
            self.fail_callback(self.obj, *args, **kwargs)
        else:
            self.remaining_cooldown = self.get_max_cooldown(*args, **kwargs)
            self.method(self.obj, *args, **kwargs)
