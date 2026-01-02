import logging
import os
import time
from queue import Empty, Queue
from threading import Event, Thread
from typing import Callable

from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout, RetryError
from urllib3.util.retry import Retry

from .exception import GrabpyException, HTTPError, HTTPNotFoundError, HTTPTimeoutError

POOL_SIZE: int = (os.cpu_count() or 1) * 2

logger = logging.getLogger(__name__)
stop_streaming = Event()


def http(func):
    """Decorator to catch Grabpy HTTP Exceptions and wrap them."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError:
            raise
    return wrapper


class Requester:
    def __init__(self, useragent: str, retries: int):
        self.useragent: str = useragent
        self.retries: int = retries

    @staticmethod
    def _int_to_unit(i: int) -> str:
        gb: int = 1_073_741_824
        mb: int = 1_048_576
        kb: int = 1024

        if i >= gb:
            return f'{(i / gb):.2f}Gb'
        elif i >= mb:
            return f'{(i / mb):.2f}Mb'
        elif i >= kb:
            return f'{(i / kb):.2f}Kb'
        else:
            return str(i)

    @staticmethod
    def _get_chunk_size(content_length: int | None) -> int:
        mb = 1024 * 1024

        if not content_length:
            return 1 * mb

        return max(1 * mb, min(content_length // 100, 16 * mb))

    @staticmethod
    def _request(
        callback: Callable,
        delay: float,
        url: str,
        stream: bool,
        timeout: float | tuple[float, float],
        headers: dict[str, str]
    ) -> Response:
        """All requests go through this function which respects the wishes of the robots file"""

        ok: int = 206 if stream else 200
        not_found: int = 404

        time.sleep(delay)

        try:
            response: Response = callback(url, stream=stream, timeout=timeout, headers=headers)
        except (Timeout, ConnectionError, RetryError):
            logger.debug('Timed out. "%s"', url)
        else:
            if response.status_code == ok:
                return response

            if response.status_code == not_found:
                raise HTTPNotFoundError(url)

        raise HTTPTimeoutError(url, timeout)

    @staticmethod
    def _iter_content(response: Response, chunk_size: int) -> bytes:
        try:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue

                yield chunk
        except (ChunkedEncodingError, ConnectionError):
            raise

    @staticmethod
    def _get_content_ranges(content_length: int | None, chunk_size: int) -> tuple[int, Queue]:
        queue = Queue()
        end: int = -1
        limit: int = content_length - 1
        count: int = 0

        while end < limit:
            start = end + 1
            end = min(start + chunk_size, limit)
            count += 1
            queue.put((start, end))

        return count, queue

    @http
    def _fetch(self, session: Session, delay: float, url: str) -> Response:
        return self._request(
            session.get,
            delay,
            url,
            stream=False,
            timeout=10,
            headers={}
        )

    @http
    def _stream(self, session: Session, delay: float, url: str, start: int, end: int) -> Response:
        return self._request(
            session.get,
            delay,
            url,
            stream=True,
            timeout=(10, 60),
            headers={'Range': f'bytes={start}-{end}'}
        )

    @http
    def _head(self, session: Session, delay: float, url: str) -> Response:
        return self._request(
            session.head,
            delay,
            url,
            stream=False,
            timeout=10,
            headers={}
        )

    def _download_worker(self, session: Session, output: Queue, ranges: Queue, chunk_size: int, url: str, delay: float) -> None:
        while not stop_streaming.is_set():
            try:
                start, end = ranges.get_nowait()
            except Empty:
                break

            logger.debug('Streaming "%s" [%ld:%ld]', url, start, end)

            try:
                response: Response = self._stream(session, delay, url, start, end)
            except HTTPError as err:
                logger.error(err)
                stop_streaming.set()
                output.put((None, (start, end)))
                break

            result = b''

            try:
                for chunk in self._iter_content(response, chunk_size // 4):
                    result += chunk

                output.put((start, result))
            except ChunkedEncodingError:
                chunk_size = max(512 * 4, chunk_size // 2)
                ranges.put((start, end))
            except ConnectionError:
                ranges.put((start, end))

    def session(self) -> Session:
        session = Session()
        max_retries = Retry(total=self.retries, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=max_retries, pool_maxsize=POOL_SIZE)
        session.mount(prefix='https://', adapter=adapter)
        session.mount(prefix='http://', adapter=adapter)
        session.headers.update({'User-Agent': self.useragent})

        return session

    def get_content_length(self, session: Session, url: str, delay: float) -> int:
        try:
            response: Response = self._head(session, delay, url)
        except HTTPError:
            raise

        return int(response.headers.get('Content-Length'))

    def fetch(self, session: Session, url: str, delay: float) -> bytes:
        logger.info('Fetching "%s".', url)

        try:
            response: Response = self._fetch(session, delay, url)
        except HTTPError as err:
            logger.error('Failed fetching "%s": %s', url, err)
            raise

        return response.content if response else b''

    def stream(self, session: Session, url: str, content_length: int, delay: float) -> bytes:
        logger.info('Downloading "%s".', url)

        try:
            chunk_size = self._get_chunk_size(content_length)
            count, ranges = self._get_content_ranges(content_length, chunk_size)
            thread_count: int = POOL_SIZE
            results = Queue()
            threads = []

            stop_streaming.clear()

            for i in range(thread_count):
                t = Thread(target=self._download_worker, args=(session, results, ranges, chunk_size, url, delay))
                threads.append(t)
                t.start()

            for _ in range(count):
                yield results.get()

            for t in threads:
                t.join()
        except GrabpyException as err:
            logger.error('Failed downloading "%s": %s', url, err)
            raise

        logger.info(f'Downloaded "%s".', url)
