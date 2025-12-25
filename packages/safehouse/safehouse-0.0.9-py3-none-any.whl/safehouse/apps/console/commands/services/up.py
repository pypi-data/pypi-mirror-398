from safehouse.services import docker_compose

def run(detach: bool=False):
    docker_compose.up(detach=detach)
