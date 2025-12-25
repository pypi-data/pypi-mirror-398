from typing import List

from ..exceptions import CommandError
from . import init


def run(args: List[str]):
    if len(args) != 2:
        raise CommandError(usage())
    command = args[0]
    if command == 'init':
        init.run(args[1:])
    else:
        raise CommandError(f"unsupported projects command '{command}'")


def usage() -> str:
    return "safehouse projects init <organization.project>"
 