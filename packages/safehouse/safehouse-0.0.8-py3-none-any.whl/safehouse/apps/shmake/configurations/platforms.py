from typing import List

from . import compilers

# How to easily articulate the supported versions of compilers per platform?


class Platform:
    def __init__(self, name: str):
        self.name = name
        self.compilers: List[compilers.Compiler] = []
        self.default_compiler = None

    def add_compiler(self, compiler: compilers.Compiler, *, default: bool=False):
        self.compilers.append(compiler)
        if default:
            self.default_compiler = compiler
        
    def supports_compiler(self, compiler: compilers.Compiler) -> bool:
        return compiler in self.compilers

    def __str__(self) -> str:
        return self.name


linux_platform = Platform('linux')
osx_platform = Platform('darwin')
windows_platform = Platform('windows')


supported_platforms = (
    linux_platform,
    osx_platform,
    windows_platform,
)

names = [ platform.name for platform in supported_platforms ]


def from_name(platform_name: str) -> Platform:
    for platform in supported_platforms:
        if platform.name == platform_name:
            return platform
    return None
