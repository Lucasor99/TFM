import sys

from typing import  Any  
from mypy_extensions import NoReturn  


def warn(fmt: str, *args: Any) -> None:
    sys.stderr.write(("WARNING: " + fmt) % args)
    sys.stderr.write("\n")


def panic(x: str) -> NoReturn:
    if not x.endswith("\n"):
        x += "\n"
    sys.stderr.write("\n" + chr(27) + "[32m" + x + chr(27) + "[0m\n")
    sys.exit(1)


