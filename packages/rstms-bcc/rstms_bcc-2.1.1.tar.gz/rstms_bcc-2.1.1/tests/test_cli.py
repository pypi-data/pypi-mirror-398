# cli tests

import json
import os
import shlex

import pytest
from click.testing import CliRunner

import rstms_bcc as bcc_module
from rstms_bcc import __version__, bcc
from rstms_bcc.models import Book, User


@pytest.fixture(scope="module")
def run(client):
    runner = CliRunner()

    env = os.environ.copy()
    env["TESTING"] = "1"

    def _run(cmd, **kwargs):
        assert_exit = kwargs.pop("assert_exit", 0)
        assert_exception = kwargs.pop("assert_exception", None)
        parse_json = kwargs.pop("parse_json", True)
        env.update(kwargs.pop("env", {}))
        kwargs["env"] = env
        result = runner.invoke(bcc, cmd, **kwargs)
        if assert_exception is not None:
            assert isinstance(result.exception, assert_exception)
        elif result.exception is not None:
            raise result.exception from result.exception
        elif assert_exit is not None:
            assert result.exit_code == assert_exit, (
                f"Unexpected {result.exit_code=} (expected {assert_exit})\n"
                f"cmd: '{shlex.join(cmd)}'\n"
                f"output: {str(result.output)}"
            )
        if parse_json:
            return json.loads(result.output)
        return result

    yield _run


def test_cli_version():
    assert bcc_module.__name__ == "rstms_bcc"
    assert __version__
    assert isinstance(__version__, str)


def test_cli_status(run):
    result = run(["status"])
    assert isinstance(result, dict)
    print(result)


def test_cli_mkuser(run, testuser, password, client):
    delete_result = client.delete_user(testuser.username)
    assert delete_result == dict(request="delete user", success=True, message=f"deleted: {testuser.username}")
    result = run(["mkuser", testuser.username, testuser.displayname, password])
    assert isinstance(result, dict)
    user = User(**result)
    assert isinstance(user, User)
    assert user.username == testuser.username
    assert user.displayname == testuser.displayname
    users = client.users()
    assert testuser in users


def test_cli_users(run, testuser):
    result = run(["users"])
    assert len(result)
    assert isinstance(result, list)
    for r in result:
        assert isinstance(r, dict)
    users = [User(**r) for r in result]
    assert testuser in users


def test_cli_rmuser(run, testuser, client):
    result = run(["rmuser", testuser.username])
    assert result == dict(request="delete user", success=True, message=f"deleted: {testuser.username}")
    users = client.users()
    assert testuser not in users


def test_cli_mkbook(run, testuser, testbook, client):
    assert testuser.username == testbook.username
    delete_result = client.delete_book(testbook.username, testbook.token)
    assert delete_result == dict(request="delete address book", success=True, message=f"deleted: {testbook.token}")
    result = run(["mkbook", testuser.username, testbook.bookname, testbook.description])
    assert isinstance(result, dict)
    book = Book(**result)
    assert isinstance(book, Book)
    assert book.username == testbook.username
    assert book.bookname == testbook.bookname
    assert book.description == testbook.description
    assert book.token


def test_cli_books(run, testbook):
    results = run(["books"])
    assert isinstance(results, list)
    for result in results:
        assert isinstance(result, dict)
    books = [Book(**result) for result in results]
    assert testbook in books


def test_cli_rmbook(run, testuser, testbook, client):
    assert testuser.username == testbook.username
    result = run(["rmbook", testuser.username, testbook.token])
    assert result == dict(request="delete address book", success=True, message=f"deleted: {testbook.token}")
    books = client.books(testuser.username)
    assert testbook not in books
