#!/usr/bin/env python
from importlib import metadata
import logging
import sys
from typing import Dict

from safehouse.apps.console import commands
from safehouse.apps.console.commands.types import Runnable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


supported_commands: Dict[str, Runnable] = {
    'orgs': commands.orgs,
    'projects': commands.projects,
    'services': commands.services,
    'users': commands.users,
}

def run():
    print(f"safehouse-{metadata.version('safehouse')}")
    args = [arg.lower() for arg in sys.argv[1:]]
    if len(args) > 0:
        command_name = args[0]
        command = supported_commands.get(command_name)
        if not command:
            logger.error(f"'safehouse {command_name}' not supported")
            logger.info(usage())
            sys.exit(-1)
        try:
            command.run(args[1:])
        except commands.exceptions.CommandError as e:
            logger.error(e)
            sys.exit(-1)
        except Exception as e:
            logger.exception(e)
            sys.exit(-1)
    else:
        print(usage())
        sys.exit(0)


def usage() -> str:
    return f"usage: safehouse <{'|'.join(supported_commands.keys())}>"

if __name__ == "__main__":
    run()
