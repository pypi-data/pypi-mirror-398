class Target:
    def __init__(self, name):
        self.name = name

    def __str__(self) -> str:
        return self.name


supported_targets = (
    Target('debug'),
    Target('minsizerel'),
    Target('release'),
    Target('relwithdb'),
)

names = [ target.name for target in supported_targets]


def from_name(name: str) -> Target:
    for target in supported_targets:
        if target.name == name:
            return target 
    return None
