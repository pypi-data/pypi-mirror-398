import asyncio
from http.server import SimpleHTTPRequestHandler
from aiohttp import StreamReader
from aiohttp.hdrs import CONTENT_DISPOSITION
from aiohttp.test_utils import make_mocked_request
from socketserver import TCPServer, ThreadingMixIn
from threading import Thread
from unittest import IsolatedAsyncioTestCase
from heaserver.service.aiohttp import client_session, StreamReaderWrapper, RequestFileLikeWrapper, \
    ConnectionFileLikeObjectWrapper, extract_sorts, SortOrder
from pathlib import Path
import inspect
import os
from abc import ABC
from unittest import mock
from contextlib import closing


class HTTPServer(ThreadingMixIn, TCPServer):
    pass


class AbstractMyAioHTTPTestCase(IsolatedAsyncioTestCase, ABC):
    def setUp(self) -> None:
        self.old_cwd = os.getcwd()
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path = os.path.dirname(os.path.abspath(filename))
        os.chdir(path)
        self.data = 'aiohttpdata/requirements_dev.txt'

    def tearDown(self) -> None:
        os.chdir(self.old_cwd)


class MyAioHTTPTestCase(AbstractMyAioHTTPTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.server = HTTPServer(('localhost', 0), SimpleHTTPRequestHandler)
        self.port = self.server.server_address[1]
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.start()

    async def test_client_session(self):
        async with client_session() as session:
            async with session.get(f'http://localhost:{self.port}') as response:
                self.assertEqual(200, response.status)

    async def test_stream_reader_wrapper(self):

        async with client_session() as session:
            async with session.get(f'http://localhost:{self.port}/{self.data}') as response:
                wrapper = StreamReaderWrapper(response.content)
                try:
                    self.assertEqual(Path(self.data).read_bytes(), await wrapper.read())
                finally:
                    wrapper.close()
                self.assertEqual(200, response.status)

    def tearDown(self) -> None:
        super().tearDown()
        self.server.shutdown()
        self.server.server_close()


class MyAioHTTPTestCase2(AbstractMyAioHTTPTestCase):

    async def test_request_file_like_wrapper(self):
        loop = asyncio.get_event_loop()
        protocol = mock.Mock(_reading_paused=False)
        filename = Path(self.data).name
        payload = StreamReader(protocol, 2**16, loop=loop)
        payload.feed_data(Path(self.data).read_bytes())
        payload.feed_eof()
        request = make_mocked_request(method='GET', path=f'/{filename}', payload=payload)
        with closing(RequestFileLikeWrapper(request, loop=loop)) as wrapper:
            wrapper.initialize()
            self.assertEqual(Path(self.data).read_bytes(), await loop.run_in_executor(None, wrapper.read))

    async def test_connection_file_like_object_wrapper(self):
        from multiprocessing import Pipe
        a, b = Pipe()
        the_bytes = Path(self.data).read_bytes()
        with closing(ConnectionFileLikeObjectWrapper(a)) as wrapper, closing(b) as b:
            b.send_bytes(the_bytes)
            self.assertEqual(the_bytes, wrapper.read())

class SimpleAioHTTPTestCase(IsolatedAsyncioTestCase):

    async def test_parse_sort_asc(self):
        request = make_mocked_request('GET', '/test?sort=asc')
        self.assertEqual(SortOrder.ASC, next(extract_sorts(request)), None)

    async def test_parse_sort_asc_with_space(self):
        request = make_mocked_request('GET', '/test?sort=asc ')
        self.assertEqual(SortOrder.ASC, next(extract_sorts(request)), None)

    async def test_parse_sort_desc(self):
        request = make_mocked_request('GET', '/test?sort=desc')
        self.assertEqual(SortOrder.DESC, next(extract_sorts(request)), None)

    async def test_parse_sort_ASC(self):
        request = make_mocked_request('GET', '/test?sort=ASC')
        self.assertEqual(SortOrder.ASC, next(extract_sorts(request)), None)

    async def test_parse_sort_DESC(self):
        request = make_mocked_request('GET', '/test?sort=DESC')
        self.assertEqual(SortOrder.DESC, next(extract_sorts(request)))
