from safehouse import utils

from . import configurations

configuration = None
safehouse_dir = None

def init():
    global configuration
    config_file = utils.find_file_in_parent_dirs('.shmake')
    if config_file:
        configuration = configurations.from_file(config_file)

init()
