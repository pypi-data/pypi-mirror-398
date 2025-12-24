#
# baikal api client tests
#

import pytest

from rstms_bcc import settings
from rstms_bcc.browser import Session
from rstms_bcc.models import (
    Account,
    AddBookRequest,
    AddUserRequest,
    Book,
    DeleteBookRequest,
    DeleteUserRequest,
    User,
)
from rstms_bcc.version import __version__


@pytest.fixture
def test_username():
    return "testo@example.org"


@pytest.fixture
def account(test_env):
    account = Account(username=settings.ADMIN_USERNAME, password=str(settings.ADMIN_PASSWORD))
    return account


@pytest.fixture
def session(account):
    session = Session()
    assert session
    yield session
    session.shutdown()


@pytest.fixture
def test_user(account, session, test_username):
    users = session.users(account)
    for user in users:
        if user.username == test_username:
            return user
    added = session.add_user(
        account, AddUserRequest(username=test_username, displayname="test user", password="testpassword")
    )
    assert isinstance(added, User)
    assert added.username == test_username
    return added


def test_session_status(session):
    status = session.status()
    assert isinstance(status, dict)


def test_session_login(session, account):
    session.login(account)
    assert session.logged_in


def test_session_logout(session, account):
    session.login(account)
    assert session.logged_in
    session.logout()
    assert not session.logged_in


def test_session_users(session, account):
    users = session.users(account)
    assert users
    assert isinstance(users, list)
    for user in users:
        assert isinstance(user, User)


def test_session_add_delete_user(session, account, test_username):
    def delete_testuser():
        users = session.users(account)
        for user in users:
            if user.username == test_username:
                deleted = session.delete_user(account, DeleteUserRequest(username=test_username))
                assert deleted == {"message": f"deleted: {test_username}"}

    delete_testuser()
    added = session.add_user(
        account, AddUserRequest(username=test_username, displayname="test user", password="testpassword")
    )
    assert isinstance(added, User)
    assert added.username == test_username
    delete_testuser()


def test_session_books(session, account, test_user):
    books = session.books(account, test_user.username)
    assert books
    assert isinstance(books, list)
    for book in books:
        assert isinstance(book, Book)


def test_session_add_delete_book(session, account, test_user):

    def delete_testbook():
        books = session.books(account, test_user.username)
        assert books
        assert isinstance(books, list)
        for book in books:
            if book.bookname == "testbook":
                deleted = session.delete_book(account, DeleteBookRequest(username=test_user.username, token=book.token))
                assert deleted == {"message": f"deleted: {book.token}"}

    delete_testbook()
    request = AddBookRequest(username=test_user.username, bookname="testbook", description="test address book")
    added = session.add_book(account, request)
    assert added
    assert isinstance(added, Book)
    assert added.username == test_user.username
    assert added.bookname == "testbook"
    book_names = [b.bookname for b in session.books(account, test_user.username)]
    assert "testbook" in book_names
    delete_testbook()
    book_names = [b.bookname for b in session.books(account, test_user.username)]
    assert "testbook" not in book_names


def test_session_reset(session):
    status = session.status()
    assert isinstance(status, dict)
    assert status["uptime"] is not None
    assert status["version"] == __version__
    ret = session.reset()
    assert ret == dict(message="session reset")
    status = session.status()
    assert isinstance(status, dict)
    assert status["uptime"] is not None
    assert status["reset_time"] is not None
    assert status["version"] == __version__


def test_session_initialized(session, account):
    ret = session.initialize(account)
    assert isinstance(ret, dict)
    assert list(ret.keys()) == ["message"]
    assert ret["message"] in ["already initialized", "configured successfully"]
