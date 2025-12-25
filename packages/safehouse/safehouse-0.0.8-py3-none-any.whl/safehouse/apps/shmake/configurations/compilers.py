from typing import Optional

from . import targets


class Compiler:
    def __init__(self, name, version):
        self.name = name
        self.version = version

    def __eq__(self, other: 'Compiler') -> bool:
        return (self.name == other.name) and (self.version == other.version)

    def __str__(self) -> str:
        return f"{self.name}-{self.version}"

    @property
    def aggregates_targets(self) -> bool:
        return self.name == 'vs'

    def name_is(self, name: str) -> bool:
        return self.name == name

    def supports_architecture(architecture: str) -> bool:
        return architecture == 'x86_64'

    @property
    def versioned_name(self) -> str:
        return f"{self.name}-{self.version}"


supported_compilers = (
    Compiler('gcc', '4.2'),
    Compiler('llvm', '19'),
    Compiler('vs', '2017'),
    Compiler('vs', '2022'),
)
names = [ compiler.name for compiler in supported_compilers ]


def from_name_and_version(name: str, version: str) -> Optional[Compiler]:
    for compiler in supported_compilers:
        if compiler.name == name and compiler.version == version:
            return compiler
    return None


def from_versioned_name(versioned_name: Optional[str]) -> Optional[Compiler]:
    if not versioned_name:
        return None
    tokens = versioned_name.split('-')
    if len(tokens) != 2:
        return None
    return from_name_and_version(tokens[0], tokens[1])
