import os
from tempfile import NamedTemporaryFile

from .exception import DiskError, FileDestinationInvalid, FileNotSeekableError


class FileParts:
    def __init__(self, dest: str, size: int) -> None:
        self.tmp = NamedTemporaryFile('wb', delete=False)
        self.dest = dest

        if not self.tmp.seekable():
            raise FileNotSeekableError(self.tmp)

        self.tmp.truncate(size)

    def __enter__(self) -> NamedTemporaryFile:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.tmp.close()

        try:
            if exc_type is not None:
                os.remove(self.tmp.name)
            else:
                os.replace(self.tmp.name, self.dest)
        except FileNotFoundError:
            raise FileDestinationInvalid(self.tmp, self.dest)

        return False

    def write(self, offset: int, chunk: bytes) -> None:
        try:
            self.tmp.seek(offset)
            self.tmp.write(chunk)
        except OSError as err:
            if err.errno == 28:
                raise DiskError()
