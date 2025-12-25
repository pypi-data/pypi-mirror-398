from aiohttp.test_utils import TestServer, TestClient, AioHTTPTestCase
from aiohttp.web import Application
from typing import Any, Union
from heaobject import root
from freezegun.api import FakeDatetime
# We need to override heaobject.root.json_encode because orjson only encodes datetimes not subclasses of datetime, and
# freezegun results in use of FakeDatetime objects.
def testing_json_encode(o: Any) -> Union[str, root.HEAObjectDict]:
    """
    Function to pass into the orjson.dumps default parameter that supports encoding HEAObjects and Fakedatetime objects.

    :param o: the object to encode.
    :return: the object after encoding.
    :raise TypeError: if the object is not a HEAObject.
    """
    match o:
        case root.HEAObject():
            return o.to_dict()
        case FakeDatetime():
            return o.isoformat()
        case _:
            raise TypeError(f'values {o} must be HEAObject, Fakedatetime, or a value type supported by orjson.dumps by default')
root.json_encode = testing_json_encode
from heaserver.service import appproperty
import pytest
import abc
import asyncio
import logging


class HEAAioHTTPTestCase(AioHTTPTestCase, abc.ABC):
    """
    Base class for testing HEA microservices.
    """

    def __init__(self, methodName=None, port=None):
        """
        Creates a test case object. The optional method name argument is passed into the superclass' constructor. If no
        port is specified in the constructor, a random port is selected. Test cases ignore the microservice's
        default port.

        :param methodName: the test method to execute.
        :param port: the port on which to run the service being tested.
        :raises ValueError: if the provided methodName does not exist.
        """
        super().__init__(methodName=methodName)
        self._port = port

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @abc.abstractmethod
    async def get_application(self) -> Application:
        pass

    async def get_server(self, app: Application) -> TestServer:
        """
        Overrides this method to allow setting a fixed port for running aiohttp. If no port was specified in the
        constructor, a random port will be selected.

        :param app: the aiohttp application.
        :return: a new aiohttp TestServer instance.
        """
        if self._port:
            return TestServer(app, port=self._port)
        else:
            return TestServer(app)

    async def get_client(self, server: TestServer) -> TestClient:
        """Return a TestClient instance."""
        return TestClient(server, loop=self.loop, json_serialize=root.json_dumps)

    async def setUpAsync(self) -> None:
        logger = logging.getLogger(__name__)
        await super().setUpAsync()
        loop = asyncio.get_running_loop()
        try:
            try:
                loop.set_task_factory(asyncio.eager_task_factory)  # type: ignore[attr-defined]
                logger.debug('Eager task factory is turned on')
            except AttributeError:
                pass
        except AttributeError:
            logger.debug('Using default task factory because eager task factory is not supported by this version of python')
        self.app[appproperty.HEA_CLIENT_SESSION] = self.client.session
