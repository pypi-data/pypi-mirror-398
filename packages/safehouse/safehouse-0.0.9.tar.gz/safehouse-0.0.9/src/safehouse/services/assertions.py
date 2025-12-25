from . import exceptions, local


def local_services_running():
    if not local.is_running():
        raise exceptions.ServicesError("local services are not running")
