from .errors import ResultUnwrapError 
class Okay:
    __match_args__ = ("value",)
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def unwrap(self):
        return self.value

    def map(self, func):
        try:
            return Okay(func(self.value))
        except Exception as e:
            return Err(e)

    def __repr__(self):
        return f"\033[92mOkay({self.value})\033[0m"

    def is_okay(self):
        return True

    def is_err(self):
        return False


class Err:
    __match_args__ = ("error",)

    def __init__(self, error):
        self.error = error

    def unwrap(self):
        raise ResultUnwrapError(f"tried to access Err: {self.error}")

    def map(self, func):
        return self

    def __repr__(self):
        return f"\033[31mErr({self.error})\033[0m"

    def is_okay(self):
        return False

    def is_err(self):
        return True