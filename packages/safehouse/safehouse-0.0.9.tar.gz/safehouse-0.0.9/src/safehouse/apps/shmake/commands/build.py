import logging
import os

from . import command
from .. import config


logger = logging.getLogger()


class Build(command.Command):
    def __init__(self):
        super().__init__()
        self.configuration = config.configuration

    def __str__(self) -> str:
        return f"configure {self.configuration}"

    def configureFromArguments(self):
        super().configureFromArguments()

    @property
    def description(self) -> str:
        return 'build the current directory'

    def initialize_options(self):
        pass

    @property
    def name(self) -> str:
        return 'build'

    def run(self) -> bool:
        print(self)
        os.system('make')
        return True
