from safehouse import projects, utils

project = None
safehouse_dir = None

def init():
    global project, safehouse_dir
    safehouse_dir = utils.find_directory_in_parent_dirs('.safehouse')
    project = projects.from_safehouse_dir(safehouse_dir) if safehouse_dir else None

init()
