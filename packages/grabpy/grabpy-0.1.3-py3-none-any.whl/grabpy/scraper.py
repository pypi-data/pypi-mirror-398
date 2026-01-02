import logging
from functools import lru_cache

from .exception import GrabpyException, HTTPStreamingError
from .io import FileParts
from .request import Requester, Session
from .robots import RobotsParser


class DisallowedError(Exception):
    def __init__(self, url: str, user_agent: str):
        super().__init__(f"Access to {url} disallowed by robots.txt")
        self.url = url
        self.user_agent = user_agent


class Grabber:
    def __init__(self, useragent: str, retries: int = 3) -> None:
        """Set retries to -1 to retry indefinitely"""

        self._robots_parser = RobotsParser(useragent)
        self._requester = Requester(useragent, retries)

    def __enter__(self) -> 'Grabber':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    @lru_cache(maxsize=8, typed=True)
    def get(self, url: str) -> bytes:
        parser = self._robots_parser.get_parser(url)

        if not self._robots_parser.can_scrape(parser, url):
            raise DisallowedError(url, self._robots_parser.useragent)

        delay: float = self._robots_parser.scrape_delay(parser)
        session: Session = self._requester.session()

        return self._requester.fetch(session, url, delay)

    def download(self, url: str, fp: str) -> bool:
        parser = self._robots_parser.get_parser(url)

        if not self._robots_parser.can_scrape(parser, url):
            raise DisallowedError(url, self._robots_parser.useragent)

        delay: float = self._robots_parser.scrape_delay(parser)
        session: Session = self._requester.session()

        try:
            content_length: int = self._requester.get_content_length(session, url, delay)

            with FileParts(fp, content_length) as file:
                for offset, chunk in self._requester.stream(session, url, content_length, delay):
                    if offset is None:
                        raise HTTPStreamingError(url, chunk)

                    file.write(offset, chunk)
        except GrabpyException as err:
            logging.error('%s', err)
            return False
        else:
            return True
