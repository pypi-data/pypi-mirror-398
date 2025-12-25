import os
from typing import List, Optional


class Project:
    def __init__(
            self,
            *,
            dependencies: Optional[List['Project']]=[],
            name,
            relative_filepath: Optional[str]=None,
            source_directory: Optional[str]=None,
    ):
        # TODO - make sure there aren't recursive dependencies
        self.name = name
        self.dependencies = dependencies
        self.relative_filepath = relative_filepath
        self.source_directory = source_directory

    @property
    def is_installed(self, build_prefix: str) -> bool:
        return False

    def missing_dependencies(self, build_prefix: str) -> List['Project']:
        '''
        Return dependent projects that haven't been built under build_prefix
        '''
        return []

    @property
    def relative_build_path(self) -> str:
        '''
        The build path for this project relative to SHMAKE_SOURCE
        '''
        if self.relative_filepath:
            return os.path.join(self.relative_filepath, self.name)
        return self.name

    @property
    def relative_source_path(self) -> str:
        '''
        The source code path for this project relative to SHMAKE_SOURCE
        '''
        path = self.name
        if self.relative_filepath:
            path = os.path.join(self.relative_filepath, path)
        if self.source_directory:
            path = os.path.join(path, self.source_directory)
        return path
    
    @property
    def source_available(self, source_prefix: str) -> bool:
        '''
        Return True if the source code for this project exists where expected, False if not.
        '''
        return False


external_project = Project(name='external', relative_filepath='shared')
shared_project = Project(name='shared', dependencies=[external_project])
engine_project = Project(
    name='ion',
    dependencies=[external_project, shared_project],
    source_directory='code',
)


supported_projects = (
    external_project,
    shared_project,
    engine_project,
)


names = [ project.name for project in supported_projects ]


def from_name(project_name: str) -> Project:
    for project in supported_projects:
        if project.name == project_name:
            return project 
    return None
