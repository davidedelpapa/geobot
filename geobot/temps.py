from uuid import uuid4
from os import remove
from shutil import rmtree
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class TempDir:
    base_path: str = field(default=None)
    name: str = field(default=None)

    def __post_init__(self):
        ids = uuid4()
        self.base_path = '/tmp' if self.base_path is None else self.base_path.rstrip("/")
        self.name = str(ids) if self.name is None else self.name
        self.id=ids
        self.path = f"{self.base_path}/{self.name}"
        Path(self.path ).mkdir(parents=True, exist_ok=True)
    
    def remove(self):
        rmtree(self.path)

@dataclass
class TempFile:
    dir: str = field(default=None)
    name: str = field(default=None)
    ext:  str = field(default=None)
    mode: str = field(default=None, repr=False)

    def __post_init__(self):
        ids = uuid4()
        self.dir = '/tmp' if self.dir is None else self.dir.rstrip("/")
        self.name = str(ids) if self.name is None else self.name
        path_ext = ""
        if self.ext is not None:
            self.ext = self.ext.lstrip(".")
            path_ext = f".{self.ext}"
        self.mode = 'wb' if self.mode is None else self.mode
        self.id=ids
        self.path = f"{self.dir}/{self.name}{path_ext}"
        open(self.path, self.mode).close()

    def remove(self):
        remove(self.path)