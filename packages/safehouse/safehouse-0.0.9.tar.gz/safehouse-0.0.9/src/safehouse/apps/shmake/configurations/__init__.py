import argparse
import json
import logging
import os
from pathlib import Path
from typing import Optional

from safehouse import config
from safehouse.apps.shmake import projects
from . import compilers, platforms, targets
from .compilers import Compiler
from .platforms import Platform
from .targets import Target


logger = logging.getLogger()


class Configuration:
    def __init__(
            self,
            *,
            compiler: Compiler,
            platform: Platform,
            project: projects.Project,
            target: Target,
    ):
        self.architecture = 'x86_68'
        self.compiler = compiler
        self.platform = platform
        self.project = project
        self.target = target
        self.validate()

    @property
    def output_directory(self) -> str:
        '''
        Returns root directory for the build artifacts.
        '''
        if self.compiler.aggregates_targets:
            return os.path.join(
                self.trunk_directory,
                f"builds/{self.platform.name}/",
                f"{self.compiler.versioned_name}/",
                self.project.relative_build_path,
            )
        return os.path.join(
            self.trunk_directory,
            f"builds/{self.platform.name}/",
            f"{self.compiler.versioned_name}/",
            f"{self.target}/",
            self.project.relative_build_path,
        )
    
    @property
    def build_directory(self) -> Path:
        '''
        Returns the root directory for the build.
        '''
        path = Path(self.trunk_directory) / f"builds/{self.platform.name}" / self.compiler.versioned_name
        if not self.compiler.aggregates_targets:
            path = path / self.target.name
        path = path / self.project.relative_source_path
        return path
    
    def save(self):
        data = {
            'architecture': self.architecture,
            'compiler': f"{self.compiler.name}-{self.compiler.version}",
            'platform': self.platform.name,
            'project': self.project.name,
            'target': self.target.name,
        }
        try:
            build_configuration_directory = self.build_directory / '.shmake'
            print(f"build_configuration_directory=={build_configuration_directory}")
            with open(build_configuration_directory, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            logger.error(e)

    @property
    def source_directory(self) -> Path:
        return Path(self.trunk_directory) / self.project.relative_source_path

    def validate(self):
        if not config.project:
            raise Exception(f"no trunk directory found, please run `safehouse init` in your trunk directory")
        self.config_directory = config.project.filepath
        self.trunk_directory = self.config_directory.parent
        print(f"trunk directory == {self.trunk_directory}")
        # make sure compiler, platform and target play well together and if so generate the build for this configuration. if not raise exception
        if not self.platform.supports_compiler(self.compiler):
            raise Exception(f"compiler {self.compiler} unsupported on {self.platform}")
        #if not self.compiler.supports_target(self.target):
        #    raise Exception(f"compiler {self.compiler} doesn't support target {self.target}")
        
    def __str__(self) -> str:
        return f"{self.architecture} {self.target} build on {self.platform} using " \
               f"{self.compiler} from {self.trunk_directory}"
        

# =============================================================================
# Define supported compiler versions
# =============================================================================
gcc_4_2 = compilers.from_name_and_version('gcc', '4.2')
llvm_19 = compilers.from_name_and_version('llvm', '19')
vs_2017 = compilers.from_name_and_version('vs', '2017')
vs_2022 = compilers.from_name_and_version('vs', '2022')
# =============================================================================


# =============================================================================
# Define supported platforms and the compilers they support
# =============================================================================
linux_platform = platforms.from_name('linux')
linux_platform.add_compiler(gcc_4_2)
linux_platform.add_compiler(llvm_19, default=True)

osx_platform = platforms.from_name('darwin')
osx_platform.add_compiler(gcc_4_2, default=True)

windows_platform = platforms.from_name('windows')
windows_platform.add_compiler(vs_2017)
windows_platform.add_compiler(vs_2022, default=True)
# =============================================================================


def configuration_for(
        *,
        compiler_name: Optional[str]=None,
        platform_name: Optional[str]=None,
        project_name: str,
        target_name: Optional[str]=None,
) -> Configuration:
    configured_project = projects.from_name(project_name)
    if not project_name:
        raise Exception(f"project {project_name} is not supported")
    #if platform_name != platform.system().lower():
    #    raise Exception("cross-compiling not yet supported")
    configured_platform = platforms.from_name(platform_name)
    if not configured_platform:
        raise Exception(f"platform {platform_name} is not supported")
    compiler = compilers.from_versioned_name(compiler_name)
    if compiler_name and not compiler:
        raise Exception(f"unknown compiler'{compiler_name}")
    compiler = compiler if compiler else configured_platform.default_compiler
    target_name = target_name if target_name else 'debug'
    target = targets.from_name(target_name)
    if not target:
        raise Exception(f"unknown target '{target_name}'")
    return Configuration(
        compiler=compiler,
        platform=configured_platform,
        project=configured_project,
        target=target,
    )


def from_options(options: argparse.Namespace) -> Configuration:
    return configuration_for(
        compiler_name=options.compiler,
        platform_name=options.platform,
        project_name=options.project,
        target_name=options.target,
    )


# Move to build?
def from_file(filepath: Path) -> Configuration:
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        compiler = data.get('compiler')
        platform = data.get('platform')
        project = data.get('project')
        target = data.get('target')
        return configuration_for(
            compiler_name=compiler,
            platform_name=platform,
            project_name=project,
            target_name=target,
        )
    except FileNotFoundError:
        logger.error(f"file '{filepath} not found")
    except json.JSONDecodeError:
        logger.error(f"couldn't decode JSON from '{filepath}")
    