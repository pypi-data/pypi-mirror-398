from importlib.resources import files
from typing import List

from python_on_whales import DockerClient

from .exceptions import DockerComposeError
from .types import Container


docker_compose_file = files('safehouse.data').joinpath('docker-compose.yaml')
docker = DockerClient(compose_files=[docker_compose_file])
if not docker.compose.is_installed():
    raise DockerComposeError("Please install docker (https://docs.docker.com/get-started/get-docker/)")

docker.run.__doc__

def down():
    docker.compose.down()


def is_running(service_name) -> bool:
    return service_name in [container.name for container in ps()]
 

def ps() -> List[Container]:
    return docker.ps()
 

def up(detach: bool=False):
    docker.compose.up(detach=detach)
