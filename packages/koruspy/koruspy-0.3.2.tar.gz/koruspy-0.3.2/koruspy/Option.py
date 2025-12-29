from __future__ import annotations
from typing import TypeVar, Generic, Callable
from .errors import OptionUnwrapError

T = TypeVar("T")
U = TypeVar("U")


class Some(Generic[T]):

    __match_args__ = ("value",)

    def unwrap_or_else(self, func: Callable[[], U]):
        return self.value
        
    def flatti(self):
        if isinstance(self.value, Some, _NoneOption):
            return self.value
        return self    

    def on_nothing(self, func):
        return self

    def and_then(self, func: Callable[[T], "Option[U]"]):
        try:
            return func(self.value)
        except Exception:
            return nothing

    def Filter(self, condition: Callable[[T], bool]):
        try:
            if condition(self.value):
                return self
            return nothing
        except Exception:
            return nothing

    def getattr(self, attr_name):
        try:
            val = getattr(self.value, attr_name)
            return Some(val)
        except AttributeError:
            return nothing

    def __init__(self, value: T):
        self.value = value

    def unwrap_or(self, default):
        return self.value

    def finalize(self):
        return self.value

    def __repr__(self):
        return f"\033[92m{self.value}\033[0m"

    def if_present(self, func):
        return func(self.value)

    def to_int(self):
        try:
            return Some(int(self.value))
        except ValueError:
            return _NoneOption()
    def to_float(self):
           try:
               return Some(float(self.value))  
           except (ValueError, TypeError):
               return _NoneOption()      

    def map(self, func: Callable[[T], U]) -> Some[U]:
        return Some(func(self.value))

    def get_value(self) -> Some[T] | _NoneOption():
        return Some(self.value)

    def is_present(self):
        return True


class _NoneOption(Generic[T]):
    
    def to_float(self):
        return self

    def unwrap_or_else(self, func: Callable[[], U]):
        return func()

    def flatti(self):
        return self

    def on_nothing(self, func: Callable[[], None]):
        func()
        return self

    def Filter(self, condition: Callable[[T], bool]):
        return self

    def and_then(self, func: Callable[[T], Option[U]]):
        return self

    def getattr(self, attr_name):
        return self
   
    def unwrap_or(self, default):
        return default

    def finalize(self):
        raise OptionUnwrapError("Option doesnt has a value, try using `unwrap_or()` or `unwrap_or_else()` for fallback value")

    def __repr__(self):
        return "\033[1;91mNone\033[0m"

    def if_present(self, func):
        return self

    def to_int(self):
        return self

    def map(self, func):
        return self

    def get_value(self):
        return self

    def is_present(self):
        return False


nothing = _NoneOption()

def option_of(value, default):
    if value is None or value is nothing:
       return Some(default) if default is not None else nothing
    return Some(value)
