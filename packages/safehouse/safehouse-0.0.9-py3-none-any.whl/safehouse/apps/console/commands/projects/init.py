import logging
from pathlib import Path
from typing import List

from safehouse import config, projects
from ..exceptions import CommandError


logger = logging.getLogger()


def run(args: List[str]) -> projects.Project:
    if config.project:
        raise CommandError(f"project already exists: {config.project}")
    if len(args) != 1:
        raise CommandError(usage())
    tokens = args[0].split('.')
    if len(tokens) != 2:
        raise CommandError(usage())
    organization, project = tokens
    project_dir: Path = Path.cwd()
    config_dir = project_dir / '.safehouse'
    try:
        project = projects.Project(filepath=config_dir, name=project, org_name=organization)
    except projects.exceptions.ProjectError as e:
        raise CommandError(e)
    Path.mkdir(config_dir, exist_ok=True)
    project.save()
    config.init()
    logger.info(f"succesfully initialized {project}")
    return project


def usage() -> str:
    return "usage: safehouse init <organization.project>"
