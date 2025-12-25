from abc import ABC, abstractmethod
import os
from pathlib import Path
import subprocess


class Builder(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def build(self, build_dir: Path, command: str):
        pass

    def connect(self):
        '''
        Connect to the guest os for the builder (if there is one)
        '''
        pass

class LocalBuilder(Builder):
    def __init__(self):
        super().__init__()

    def build(self, build_dir: Path, command: str):
        prev_dir = os.getcwd()
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)
        os.chdir(build_dir)
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        if p:
            output, _ = p.communicate()
            print(output)
        os.chdir(prev_dir)


class LinuxBuilder(Builder):
    def __init__(self):
        super().__init__()

    def build(self, build_dir: Path, command: str):
        '''
        download linux builder image if it doesn't locally
        run builder in container:
        - mount the build dir as /src
        - command to run is command passed in to function
        '''
        pass

# NOTE: cd into directory invoked from for `shmake builder connect`
# When configuring or running a linux build from a non-linux host, prompt to start container, if not fail.
# - start container with tail -f /dev/null, then issue it the build command
local = LocalBuilder()
