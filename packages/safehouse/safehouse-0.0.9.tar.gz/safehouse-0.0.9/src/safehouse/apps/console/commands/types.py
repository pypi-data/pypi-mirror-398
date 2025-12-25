from typing import List, Protocol


class Runnable(Protocol):
    def run(args: List[str]):
        pass
