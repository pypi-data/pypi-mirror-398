from typing import IO


class GrabpyException(Exception):
    """Base Exception class for Grabpy package."""

    def __init__(self, msg: str) -> None:
        self.message: str = msg

    def __str__(self) -> str:
        return self.message


class HTTPError(GrabpyException):
    """HTTP Exception class for Grabpy package."""

    def __init__(self, msg: str, url: str) -> None:
        super().__init__(msg)
        self.url: str = url

    def __str__(self) -> str:
        return f'[{self.url}] {self.message}'


class FileError(GrabpyException):
    """File Exception class for Grabpy package."""

    def __init__(self, msg: str, file: IO) -> None:
        super().__init__(msg)
        self.file: IO = file

    def __str__(self) -> str:
        return f'[{self.file.name}] {self.message}'


class DiskError(GrabpyException):
    """File Exception class for Grabpy package."""

    def __init__(self) -> None:
        super().__init__('Not enough space on disk.')

    def __str__(self) -> str:
        return self.message


class HTTPStatusError(HTTPError):
    """HTTP Exception Status class for Grabpy package."""

    def __init__(self, msg: str, url: str, code: int) -> None:
        super().__init__(msg, url)
        self.code = code

    def __str__(self) -> str:
        return f'[{self.url}<code:{self.code}>] {self.message}'


class FileNotSeekableError(FileError):
    """Exception raised when file.seekable() returns False."""

    def __init__(self, file: IO) -> None:
        super().__init__('Not seekable.', file)


class FileDestinationInvalid(FileError):
    """Exception raised when temp file cannot be moved to desired destination."""

    def __init__(self, file: IO, dest: str) -> None:
        super().__init__(f'Destination is invalid.', file)
        self.dest = dest

    def __str__(self) -> str:
        return f'[{self.dest}] {self.message}'


class HTTPTimeoutError(HTTPError):
    """Exception raised when request times out."""

    def __init__(self, url: str, timeout: float | tuple[float, float]) -> None:
        super().__init__('Timed out.', url)
        self.timeout: float = timeout

    def __str__(self) -> str:
        return f'[{self.url}<timeout:{self.timeout}>] {self.message}'


class HTTPNotFoundError(HTTPStatusError):
    """Exception raised when server returns a 404 status code."""

    def __init__(self, url: str) -> None:
        super().__init__('Not found.', url, 404)


class HTTPStreamingError(HTTPError):
    """Exception raised when streaming fails critically."""

    def __init__(self, url: str, chunk: tuple[int, int]) -> None:
        super().__init__(f'Streaming chunk [{chunk[0]}:{chunk[1]}] failed.', url)
        self.chunk = chunk

    def __str__(self) -> str:
        return f'[{self.url}] {self.message}'

