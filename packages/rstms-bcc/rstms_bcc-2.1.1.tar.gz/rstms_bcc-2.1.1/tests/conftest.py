# test config

import asyncio
import logging
import os
import time
from threading import Thread

import psutil
import pytest

from rstms_bcc import settings
from rstms_bcc.app import app
from rstms_bcc.client import API
from rstms_bcc.models import Book, User

logger = logging.getLogger(__name__)

LISTEN_TIMEOUT = 5

# configure the test environment
TEST_ADDRESS = "127.0.0.1"
TEST_PORT = 8001
TEST_API_KEY = os.environ.get("TEST_API_KEY", "test_api_key")
TEST_API_URL = f"http://{TEST_ADDRESS}:{TEST_PORT}/bcc"
TEST_CALDAV_URL = os.environ["TEST_CALDAV_URL"]
TEST_SERVER_LOG_LEVEL = "INFO"
TEST_USER_PREFIX = "bcc__test__user__"
TEST_BOOK_PREFIX = "bcc__test__book__"

# test control flags
USE_EXISTING_SERVER = "USE_EXISTING_SERVER" in os.environ
PRUNE_TEST_DATA = True  # "NO_PRUNE_TEST_DATA" not in os.environ


@pytest.fixture(scope="session")
def test_env():
    env = os.environ
    try:
        settings.ADDRESS = TEST_ADDRESS
        settings.PORT = TEST_PORT
        settings.API_KEY = TEST_API_KEY
        settings.API_URL = TEST_API_URL
        settings.CALDAV_URL = TEST_CALDAV_URL
        settings.LOG_LEVEL = "INFO"
        settings.DEBUG = False
        # settings.INSECURE_NO_CLIENT_CERT = True
        yield env
    finally:
        for k, v in env.items():
            os.environ[k] = v


"""
@pytest.fixture(scope="session")
def test_api_key():
    return TEST_API_KEY


@pytest.fixture(scope="session")
def test_api_url():
    return TEST_API_URL


@pytest.fixture
def headers():
    return {"X-API-Key": TEST_API_KEY}
"""


class TestServer:
    def __init__(self):
        self.host = settings.ADDRESS
        self.port = settings.PORT
        self.app = app
        self._server = None
        self.running = False

    def run(self):
        import uvicorn

        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level=TEST_SERVER_LOG_LEVEL.lower(),
            loop="asyncio",
            lifespan="on",
        )
        self._server = uvicorn.Server(config)
        self.running = True
        self._server.run()
        self.running = False

    def stop(self):
        if self._server:
            self._server.should_exit = True


def listening_tcp_ports():
    return [conn.laddr.port for conn in psutil.net_connections(kind="tcp") if conn.status == "LISTEN"]


async def not_listening(host, port):
    return await listening(host, port, False)


async def listening(host, port, desired_state=True):
    timeout = time.time() + LISTEN_TIMEOUT
    while True:
        assert time.time() < timeout, f"Timed out waiting for {host}:{port} LISTEN"
        if port in listening_tcp_ports():
            if desired_state is True:
                return
        else:
            if desired_state is False:
                return
        await asyncio.sleep(1)


def prune_test_data(client):
    users = client.users()
    for user in users:
        if user.username.startswith(TEST_USER_PREFIX):
            logger.info(f"PRUNING: {user}")
            client.delete_user(user.username)


@pytest.fixture(scope="session")
async def test_server(test_env):

    if int(TEST_PORT) in listening_tcp_ports():
        assert USE_EXISTING_SERVER, f"server running on port {TEST_PORT}; set USE_EXISTING_SERVER to use"
        yield True
        return
    server = TestServer()
    thread = Thread(target=server.run)
    thread.start()
    try:
        await listening(server.host, server.port)
        yield server
    finally:
        server.stop()
        await not_listening(server.host, server.port)
        thread.join()


@pytest.fixture(scope="session")
def client(test_server):
    client = API()
    yield client
    if PRUNE_TEST_DATA:
        prune_test_data(client)


@pytest.fixture(scope="session")
def testid(client):
    yield str(time.time()).replace(".", "")


@pytest.fixture(scope="function")
def username(testid):
    return f"{TEST_USER_PREFIX}{testid}@domain.ext"


@pytest.fixture(scope="function")
def displayname(testid):
    return f"testuser {testid}"


@pytest.fixture(scope="function")
def password(testid):
    return testid


@pytest.fixture(scope="function")
def bookname(testid):
    return f"{TEST_BOOK_PREFIX}book_{testid}"


@pytest.fixture(scope="function")
def description(testid):
    return f"test book {testid}"


@pytest.fixture(scope="function")
def testuser(client, username, displayname, password):
    """ensure testuser exists"""
    users = client.users()
    for user in users:
        if user.username == username:
            assert user.displayname == displayname
            return user
    user = client.add_user(username, displayname, password)
    assert isinstance(user, User)
    assert user.username == username
    assert user.displayname == displayname
    return user


@pytest.fixture(scope="function")
def testbook(client, testuser, bookname, description):
    """ensure testuser and testbook exist"""
    books = client.books(testuser.username)
    for book in books:
        if book.username == testuser.username and book.bookname == bookname:
            assert book.description == description
            return book
    book = client.add_book(testuser.username, bookname, description)
    assert isinstance(book, Book)
    assert book.username == testuser.username
    assert book.bookname == bookname
    assert book.description == description
    return book
