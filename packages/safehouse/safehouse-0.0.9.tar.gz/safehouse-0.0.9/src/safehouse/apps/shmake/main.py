#!/usr/bin/env python3

from importlib import metadata
import logging
from pathlib import Path
import sys

from . import commands, config


logger = logging.getLogger()


COMMANDS = { 
    'configure': commands.Configure,
    'build': commands.Build,
}


def run():
    print(f"shmake-{metadata.version('safehouse')}")
    logging.basicConfig(
        filename=Path('/tmp/shmake.log'),
        level=logging.INFO,
    )
    command_class = None
    if len(sys.argv) > 1:
        command_class_from_args = COMMANDS.get(sys.argv[1], command_class)
        if command_class_from_args:
            command_class = command_class_from_args
    if not command_class:
        command_class = commands.Build if config.configuration else commands.Configure
    try:
        command: commands.Command = command_class()
        command.configureFromArguments()
        command.run()
    except Exception as e:
        print(e)
        print("run shmake --help for more information")
        raise(e)

if __name__ == "__main__":
    run()
