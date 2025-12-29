from typing import Any
from .Option import _NoneOption, Some
from .Result import Err, Okay
import json
white = "\033[37m"
reset = "\033[0m"


def println(*args: Any, decimalRepr: int = None, newLine: bool = True):
    printar = []
    sep = "\n" if newLine else " "
    for arg in args:
        match arg:
            case int():
                output = f"\033[34m{arg}\033[0m"
            case str():
                output = f"\033[32m{arg}\033[0m"
            case float():
                formatado = format(arg, f'.{decimalRepr}f') if decimalRepr is not None else repr(arg)
                output = f"\033[1;93m{formatado}\033[0m"
            case dict() | list() | tuple():
                output = json.dumps(arg, indent=4, ensure_ascii=False)
            case set():
                output = json.dumps(arg, indent=4, ensure_ascii=False)
            case Err():
                output = str(arg)
            case Okay():
                output = str(arg)
            case Some():
                output = str(arg)
            case _NoneOption():
                output = str(arg)
            case _ if hasattr(arg, "__dict__"):
                output = json.dumps(arg.__dict__, indent=4, ensure_ascii=False)
            case range():
                output = list(arg)
            case _: 
                output = arg
        printar.append(str(output))
    texto_final = sep.join(printar)
    print(f"{texto_final}")