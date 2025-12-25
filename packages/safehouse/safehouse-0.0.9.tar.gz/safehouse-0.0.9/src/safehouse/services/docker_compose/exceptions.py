
class DockerComposeError(Exception):
    def __init__(self, detail: str):
        super().__ini__(detail)
