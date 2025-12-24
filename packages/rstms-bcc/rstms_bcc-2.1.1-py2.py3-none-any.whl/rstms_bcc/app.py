import asyncio
import logging
import os
import signal
from contextlib import asynccontextmanager

import arrow
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from typing_extensions import Annotated

from . import settings
from .browser import BrowserException, Session
from .models import (
    Account,
    AddBookRequest,
    AddBookResponse,
    AddUserRequest,
    AddUserResponse,
    BooksResponse,
    DeleteBookRequest,
    DeleteBookResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    InitializeResponse,
    PasswordResponse,
    ResetResponse,
    ShutdownResponse,
    StatusResponse,
    UptimeResponse,
    UserAccountsResetRequest,
    UserAccountsResponse,
    UsersResponse,
)
from .passwd import AccountException, Accounts
from .version import __version__


async def require_client_cert_header(
    x_client_cert_dn: Annotated[str, Header()],
):
    if x_client_cert_dn != "CN=mabctl":
        raise HTTPException(status_code=401, detail="client certificate CN mismatch")


async def require_api_key_header(
    x_api_key: Annotated[str, Header()],
):
    if x_api_key != app.state.api_key:
        raise HTTPException(status_code=401, detail="invalid API key")


async def require_admin_credential_headers(
    x_admin_username: Annotated[str, Header()],
    x_admin_password: Annotated[str, Header()],
):
    if not x_admin_username:
        raise HTTPException(status_code=401, detail="missing username")
    if not x_admin_password:
        raise HTTPException(status_code=401, detail="missing password")
    app.state.account = Account(username=x_admin_username, password=x_admin_password)


async def null_header_dependency():
    pass


def shutdown_browser_session():
    clear_logout_timer()
    clear_shutdown_timer()
    if app.state.session:
        app.state.session.shutdown()
    app.state.session = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.logger = logging.getLogger(settings.LOGGER_NAME)
    app.state.logger.setLevel(settings.LOG_LEVEL)
    app.state.logger.info(f"bcc v{__version__} startup")
    app.state.api_key = settings.get(None, "API_KEY", settings.Get.DECODE_SECRET, settings.Get.OPTIONAL_READ_FILE)
    app.state.startup_time = arrow.now()
    app.state.logout_timer_task = None
    app.state.shutdown_timer_task = None
    app.state.account = None
    app.state.session = Session()
    if settings.INSECURE_NO_CLIENT_CERT:
        app.state.logger.warning("INSECURE_NO_CLIENT_CERT: client certificate header validation disabled")
        app.dependency_overrides[require_client_cert_header] = null_header_dependency
    if settings.INSECURE_NO_API_KEY:
        app.state.logger.warning("INSECURE_NO_API_KEY: api key header validation disabled")
        app.dependency_overrides[require_api_key_header] = null_header_dependency
    yield
    app.state.logger.info("shutdown")
    shutdown_browser_session()


app = FastAPI(
    dependencies=[
        Depends(require_client_cert_header),
        Depends(require_api_key_header),
        Depends(require_admin_credential_headers),
    ],
    lifespan=lifespan,
)


def handle_exception(request, exc):
    path = str(request.url)[len(str(request.base_url)) :]
    error = dict(success=False, request=request.method + " /" + path, message=exc.__class__.__name__, detail=exc.args)
    app.state.logger.error(repr(error))
    return JSONResponse(status_code=500, content=error)


@app.exception_handler(BrowserException)
async def browser_exception_handler(request: Request, exc: BrowserException):
    return handle_exception(request, exc)


@app.exception_handler(AccountException)
async def account_exception_handler(request: Request, exc: BrowserException):
    return handle_exception(request, exc)


def clear_shutdown_timer():
    if app.state.shutdown_timer_task:
        app.state.shutdown_timer_task.cancel()
    app.state.shutdown_timer = None


def restart_shutdown_timer(restart=True):
    clear_shutdown_timer()
    if settings.AUTO_SHUTDOWN_TIMER:
        app.state.shutdown_timer_task = asyncio.create_task(auto_shutdown_timer())


async def auto_shutdown_timer():
    await asyncio.sleep(settings.AUTO_SHUTDOWN_TIMER)
    app.state.logger.info("auto browser shutdown")
    app.state.session.shutdown()


def clear_logout_timer():
    """called after each request to logout after timeout"""
    if app.state.logout_timer_task:
        app.state.logout_timer_task.cancel()
    app.state.logout_timer_task = None


def restart_logout_timer():
    clear_logout_timer()
    if settings.AUTO_LOGOUT_TIMER:
        app.state.logout_timer_task = asyncio.create_task(auto_logout_timer())


async def auto_logout_timer():
    await asyncio.sleep(settings.AUTO_LOGOUT_TIMER)
    app.state.logger.info("auto logout")
    app.state.session.logout()


@app.middleware("http")
async def logout_after_request(request: Request, call_next):
    response = await call_next(request)
    restart_logout_timer()
    restart_shutdown_timer()
    return response


@app.get("/bcc/status/")
async def get_status() -> StatusResponse:
    return StatusResponse(request="status", status=app.state.session.status())


@app.post("/bcc/reset/")
async def post_reset() -> ResetResponse:
    return app.state.session.reset()


@app.post("/bcc/initialize/")
async def post_initialize() -> InitializeResponse:
    return app.state.session.initialize(app.state.account)


@app.get("/bcc/users/")
async def get_users() -> UsersResponse:
    return UsersResponse(users=app.state.session.users(app.state.account))


@app.post("/bcc/user/")
async def post_user(request: AddUserRequest) -> AddUserResponse:
    return AddUserResponse(user=app.state.session.add_user(app.state.account, request))


@app.delete("/bcc/user/")
async def delete_user(request: DeleteUserRequest) -> DeleteUserResponse:
    result = app.state.session.delete_user(app.state.account, request)
    Accounts().remove(request.username)
    return result


@app.get("/bcc/books/")
async def get_addressbooks_all() -> BooksResponse:
    users = app.state.session.users(app.state.account)
    books = []
    for user in users:
        books.extend(app.state.session.books(app.state.account, user.username))
    return BooksResponse(books=books)


@app.get("/bcc/books/{username}/")
async def get_addressbooks_user(username: str) -> BooksResponse:
    return BooksResponse(books=app.state.session.books(app.state.account, username))


@app.post("/bcc/book/")
async def post_address_book(request: AddBookRequest) -> AddBookResponse:
    return AddBookResponse(book=app.state.session.add_book(app.state.account, request))


@app.delete("/bcc/book/")
async def delete_book(request: DeleteBookRequest) -> DeleteBookResponse:
    return app.state.session.delete_book(app.state.account, request)


@app.post("/bcc/shutdown/")
async def shutdown(background_tasks: BackgroundTasks) -> ShutdownResponse:
    app.state.logger.warning("received shutdown request")
    shutdown_browser_session()
    background_tasks.add_task(shutdown_app)
    return dict(message="shutdown requested")


@app.get("/bcc/password/{username}/")
async def get_password(username: str) -> PasswordResponse:
    password = Accounts().get(username)
    return PasswordResponse(username=username, password=password)


@app.get("/bcc/accounts/")
async def get_accounts() -> UserAccountsResponse:
    accounts = Accounts()
    response = UserAccountsResponse(message="user accounts", accounts=accounts.read())
    return response


@app.post("/bcc/accounts/")
async def post_accounts(request: UserAccountsResetRequest) -> UserAccountsResponse:
    accounts = Accounts()
    response = UserAccountsResponse(message="user accounts reset", accounts=accounts.write(request.accounts))
    return response


def shutdown_app():
    app.state.logger.warning("shutdown_task: exiting")
    os.kill(os.getpid(), signal.SIGINT)


@app.get("/bcc/uptime/")
async def uptime() -> UptimeResponse:
    return dict(message="started " + app.state.startup_time.humanize(arrow.now()))
