from . import docker_compose


def is_running() -> bool:
    return docker_compose.is_running('safehouse_services')
