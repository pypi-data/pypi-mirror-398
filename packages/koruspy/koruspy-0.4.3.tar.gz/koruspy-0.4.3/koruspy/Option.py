from __future__ import annotations
from typing import TypeVar, Generic, Callable
from .errors import OptionUnwrapError
import asyncio
import inspect

T = TypeVar("T")
U = TypeVar("U")


class Some(Generic[T]):

    __match_args__ = ("value",)

    async def map_async(self, func: Callable[[T], U]) -> Some[U]:
        value = func(self.value)
        if inspect.isawaitable( value):
            value = await value
        if value is None:
            return nothing
        return Some(value)

    async def unwrap_or_else_async(self, func):
        return self.value

    def unwrap_or_else(self, func: Callable[[], U]):
        return self.value
        
    def flatti(self):
        if isinstance(self.value, Some, _NoneOption):
            return self.value
        return self    

    async def on_nothing_async(self, func):
        return self

    def on_nothing(self, func):
        return self

    def and_then(self, func: Callable[[T], Option[U]]):
        try:
            return func(self.value)
        except Exception:
            return nothing

    async def Filter_async(self, condition: Callable[[T], bool]):
        if await condition(self.value):
            return self
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

    async def if_present_async(self, func):
         return await func(self.value)

    def if_present(self, func):
        return func(self.value)

    def to_int(self):
        try:
            return Some(int(self.value))
        except ValueError:
            return nothing
    def to_float(self):
           try:
               return Some(float(self.value))  
           except (ValueError, TypeError):
               return nothing   

    def map(self, func: Callable[[T], U]) -> Some[U]:
        result = func(self.value)
        if result is None:
            return nothing
        return Some(result)    

    def get_value(self) -> Some[T] | nothing:
        return Some(self.value)

    async def get_value_async(self) -> Some[T] | nothing:
        return Some(self.value)

    def is_present(self):
        return True


class _NoneOption(Generic[T]):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def to_float(self):
        return nothing

    async def unwrap_or_else_async(self, func: Callable[[], U]):
        return await func()
    
    def unwrap_or_else(self, func: Callable[[], U]):
        return func()

    def flatti(self):
        return nothing

    async def on_nothing_async(self, func: Callable[[], None]):
        await func()
        return nothing

    def on_nothing(self, func: Callable[[], None]):
        func()
        return nothing

    async def Filter_async(self, condition):
        return  nothing

    def Filter(self, condition: Callable[[T], bool]):
        return nothing

    def and_then(self, func: Callable[[T], Option[U]]):
        return nothing

    def getattr(self, attr_name):
        return nothing
   
    def unwrap_or(self, default):
        return default

    def finalize(self):
        raise OptionUnwrapError("Option doesnt has a value, try using `unwrap_or()` or `unwrap_or_else()` for fallback value")

    def __repr__(self):
        return "\033[1;91mNone\033[0m"

    async def if_present_async(self, func):
        return nothing

    def if_present(self, func):
        return nothing 

    def to_int(self):
        return nothing

    async def map_async(self, func):
        return nothing

    def map(self, func):
        return nothing

    def get_value(self):
        return nothing

    async def get_value_async(self):
        return nothing

    def is_present(self):
        return False

nothing = _NoneOption()


def option_of(value, default):
    if value is None or value is nothing:
       return Some(default) if default is not None else nothing
    return Some(value)
