from typing import List

from ..exceptions import CommandError
from . import down, up


def run(args: List[str]):
    if len(args) < 1:
        raise CommandError(usage())
    command = args[0]
    if command == 'down':
        down.run()
    elif command == 'up':
        up.run(detach=True)
    else:
        raise CommandError(usage())
        

def usage() -> str:
    return "safehouse services <up|down>"
