import urllib.parse
from functools import lru_cache
from urllib.robotparser import RobotFileParser


class RobotsParser:
    def __init__(self, useragent: str) -> None:
        self.useragent: str = useragent

    def __str__(self) -> str:
        return f'RobotsParser-{self.useragent}'

    @staticmethod
    def _extract_url_base(url: str) -> str:
        result = urllib.parse.urlparse(url)
        netloc = result.netloc
        scheme = result.scheme

        if not all([netloc, scheme]):
            raise ValueError(f'Invalid url schema: {url}')

        return f'{scheme}://{netloc}'

    @lru_cache(maxsize=128, typed=True)
    def get_parser(self, url: str) -> RobotFileParser:
        base = self._extract_url_base(url)
        url = urllib.parse.urljoin(base, 'robots.txt')

        rp = RobotFileParser()
        rp.set_url(url)
        rp.read()

        return rp

    def can_scrape(self, parser: RobotFileParser, url: str) -> bool:
        return parser.can_fetch(self.useragent, url)

    def scrape_delay(self, parser: RobotFileParser) -> float:
        delay = parser.crawl_delay(self.useragent)
        return float(0 if not delay else delay)
