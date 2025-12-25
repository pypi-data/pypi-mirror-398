from abc import ABC, abstractmethod
from argparse import ArgumentParser
import platform

from ..configurations import platforms


class Command(ABC):
    def __init__(self):
        self.parser = ArgumentParser(prog=f"schmake {self.name}")

    @abstractmethod
    def configureFromArguments(self):
        self.parser.add_argument(
            'command',
            default=self.name,
            nargs='?',
            help='command to run',
        )
        # TIM - move to configure
        self.parser.add_argument(
            '--platform',
            default=platform.system().lower(),
            choices=platforms.names,
            dest='platform',
            required=False,
        )
        self.options = self.parser.parse_args()
        self.initialize_options()

    @property
    @abstractmethod
    def description(self) -> str:
        return 'abstract description'

    @property
    @abstractmethod
    def name(self) -> str:
        return 'abstract name'

    def print_usage(self):
        self.parser.print_usage()

    @abstractmethod
    def run(self) -> bool:
        return False

    @abstractmethod
    def initialize_options(self):
        pass

    def __str__(self) -> str:
        return f"{self.name}"
