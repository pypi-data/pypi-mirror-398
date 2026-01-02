"""Zoozl server.

Meant to be run in main python thread.

>>> with open("conf.toml", "rb") as file:
...     conf = tomllib.load(file)
>>> # Run server until interrupted
>>> start(conf)
"""

from abc import abstractmethod
import asyncio
import email
import functools
import hmac
import json
import logging
import signal
import time
import traceback
import uuid

from aiosmtpd.lmtp import LMTP
from aiosmtpd.handlers import AsyncMessage

from zoozl import websocket, chatbot, slack, emailer


log = logging.getLogger(__name__)


class Interrupt(Exception):
    """Exception to interrupt server."""


# Standard HTTP/1.1 constants
DEFAULT_HTTP_BODY_ENCODING = "iso-8859-1"
HTTP_STATUS_CODES = (
    (200, "OK"),
    (400, "Bad Request"),
    (403, "Forbidden"),
    (405, "Method Not Allowed"),
    (408, "Request Timeout"),
    (411, "Length Required"),
    (414, "URI Too Long"),
    (500, "Internal Server Error"),
    (501, "Not Implemented"),
)


def write_http_response(
    writer: asyncio.StreamWriter, status: int, headers: dict = None, body: bytes = b""
):
    """Write HTTP response to writer."""
    headers = headers if headers is not None else {}
    # Capitalize all fields in headers
    # Although HTTP headers are case-insensitive, it is common to have them in title case
    # and thus it might be that some clients (users) expect them to be so
    response_headers = {}
    for key, value in headers.items():
        response_headers[key.title()] = value
    if "Connection" not in response_headers:
        headers["Connection"] = "close"
    if body:
        headers["Content-Length"] = str(len(body))
    try:
        reason = next(msg for code, msg in HTTP_STATUS_CODES if code == status)
    except StopIteration:
        raise NotImplementedError(f"Invalid status code: {status}")
    writer.write(f"HTTP/1.1 {status} {reason}\r\n".encode("ascii"))
    for key, value in headers.items():
        writer.write(f"{key}: {value}\r\n".encode("ascii"))
    writer.write(b"\r\n")
    if body:
        writer.write(body)


class CaseInsensitiveFrozenDict(dict):
    """Case-insensitive dictionary.

    This class is used to store headers in HTTP message.
    """

    def __init__(self, iterable):
        """Initialise dictionary with case-insensitive keys."""
        super().__init__((key.lower(), value.strip()) for key, value in iterable)

    def __setitem__(self, key, value):
        """Set item in dictionary."""
        raise TypeError("Cannot modify frozen dictionary")

    def get(self, key, default=None):
        """Get item from dictionary."""
        return super().get(key.lower(), default)

    def __getitem__(self, key):
        """Get item from dictionary."""
        return super().__getitem__(key.lower())

    def __delitem__(self, key):
        """Delete item from dictionary."""
        raise TypeError("Cannot modify frozen dictionary")

    def __contains__(self, key):
        """Check if key is in dictionary."""
        return super().__contains__(key.lower())


class HTTPRequest:
    """Message container for receiving HTTP/1.1 compliant messages.

    Example usage:

        >>> msg = HTTPRequest(reader, writer)
        >>> if await msg.read(timeout=1):
        ...     print(msg.method)
        ...     print(msg.request_uri)
        ...     print(msg.headers)
        ...     # reader still contains message body
        ...     # writer is still open and has not written anything
        ...     if await msg.read_body(timeout=100):
        ...         print(msg.body)
        ...         print(msg.media_type)
        ...         print(msg.encoding)
        ...     else:
        ...         # reader might still be able to read some data
        ...         # writer has written error message as per HTTP/1.1
        ...         # writer must be closed as `connection: close` header was written
        ...         print(msg.error_code)
        ...         print(msg.error_message)
        ... else:
        ...     # reader might still be able to read some data
        ...     # writer has written error message as per HTTP/1.1
        ...     # writer must be closed as `connection: close` header was written
        ...     print(msg.error_code)
        ...     print(msg.error_message)
        >>> # Responsibility of flushing and closing writer is on the caller
        >>> await writer.drain()
        >>> writer.close()
        >>> await writer.wait_closed()

    The `read()` method reads from the reader and parses the message up to the message
    body, consuming the following:

        - Start-line: [CONSUMED]
        - *( header-field CRLF ): [CONSUMED]
        - CRLF: [CONSUMED]
        - Message body: [NOT CONSUMED]

    method (str): HTTP method used in the request, not guaranteed to be valid HTTP method
    request_uri (str): URI requested
    headers (dict): headers in the request

    The `read_body` method reads the body of the message, it consumes fully the received
    message. The body is parsed as per `content-type` header.

    The `error_code` and `error_message` are set if an error occurs while reading the
    message.
    """

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Initialise HTTP message with empty attributes."""
        self.method = None
        self.request_uri = None
        self.headers = None
        self.error_code = None
        self.error_message = None
        self.reader = reader
        self.writer = writer
        self.body = None
        self.media_type = None
        self.encoding = None

    async def read(self, timeout: int = 500):
        """Read from reader and parse HTTP message."""
        try:
            if not await asyncio.wait_for(self._read_request_line(), timeout):
                return False
            if not await asyncio.wait_for(self._read_headers(), timeout):
                return False
        except asyncio.TimeoutError:
            self.error_code = 408
            self.error_message = "While reading, request timed out"
            write_http_response(self.writer, self.error_code)
            return False
        return True

    async def read_body(self, timeout: int = 500):
        """Read body of the message."""
        if self.headers is None:
            raise RuntimeError("Message must be `read` first before reading body")
        if self.error_code is not None or self.error_message is not None:
            raise RuntimeError("Message had error reading, cannot read body")
        content_type = self.headers.get("content-type", "application/octet-stream")
        content_type = content_type.split(";")
        self.media_type = content_type[0]
        self.encoding = None
        for part in content_type[1:]:
            part = part.strip()
            part = part.split("=", maxsplit=1)
            if len(part) == 2:
                key, value = part
                if key == "charset":
                    self.encoding = value
        length = self.headers.get("content-length")
        if length is None:
            self.error_code = 411
            self.error_message = "While reading body, missing content-length"
            write_http_response(self.writer, self.error_code)
            return False
        try:
            self.body = await asyncio.wait_for(
                self.reader.readexactly(int(length)), timeout
            )
            return True
        except asyncio.IncompleteReadError:
            write_http_response(self.writer, 400)
            log.warning("Incomplete body")
            return False
        except asyncio.TimeoutError:
            write_http_response(self.writer, 408)
            log.warning("Timeout while reading body")
            return False

    async def _read_method(self):
        """Read method from reader."""
        error_code = None
        try:
            method = await self.reader.readuntil(b" ")
            method = method[:-1]
        except asyncio.LimitOverrunError:
            error_code = 501
            self.error_message = "While reading method, buffer limit exceeded"
        except asyncio.IncompleteReadError:
            error_code = 400
            self.error_message = "While reading method, incomplete read"
        else:
            try:
                self.method = method.decode("ascii")
            except UnicodeError:
                error_code = 400
                self.error_message = "While decoding method, invalid ascii"
            else:
                return True
        write_http_response(self.writer, error_code)
        self.error_code = error_code
        return False

    async def _read_request_uri(self):
        """Read request-uri from reader."""
        error_code = None
        try:
            request_uri = await self.reader.readuntil(b" ")
            request_uri = request_uri[:-1]
        except asyncio.LimitOverrunError:
            error_code = 414
            self.error_message = "While reading request-uri, buffer limit exceeded"
        except asyncio.IncompleteReadError:
            error_code = 400
            self.error_message = "While reading request-uri, incomplete read"
        else:
            try:
                self.request_uri = request_uri.decode("ascii")
            except UnicodeError:
                error_code = 400
                self.error_message = "While decoding request-uri, invalid ascii"
            else:
                return True
        write_http_response(self.writer, error_code)
        self.error_code = error_code
        return False

    async def _read_version(self):
        """Read version from reader."""
        error_code = None
        try:
            await self.reader.readuntil(b"\r\n")
        except (asyncio.LimitOverrunError, asyncio.IncompleteReadError):
            error_code = 400
            self.error_message = (
                "While reading version, buffer limit exceeded or incomplete read"
            )
        else:
            return True
        write_http_response(self.writer, error_code)
        self.error_code = error_code
        return False

    async def _read_request_line(self):
        """Read first line from reader."""
        for block in [self._read_method, self._read_request_uri, self._read_version]:
            if not await block():
                return False
        return True

    async def _read_headers(self):
        """Read headers from reader."""
        error_code = None
        try:
            headers = await self.reader.readuntil(b"\r\n\r\n")
            headers = headers[:-4]
        except (asyncio.LimitOverrunError, asyncio.IncompleteReadError):
            error_code = 400
            self.error_message = (
                "While reading headers, buffer limit exceeded or incomplete read"
            )
        else:
            try:
                headers = headers.decode("ascii")
            except UnicodeError:
                error_code = 400
                self.error_message = "While decoding headers, invalid ascii"
            try:
                headers = headers.split("\r\n")
                self.headers = CaseInsensitiveFrozenDict(
                    map(lambda x: x.split(":", maxsplit=1), headers)
                )
            except ValueError as e:
                error_code = 400
                self.error_message = f"While decoding headers, invalid format: {e}"
            else:
                return True
        write_http_response(self.writer, error_code)
        self.error_code = error_code
        return False


async def wait_for_response(
    coro,
    writer: asyncio.StreamWriter,
    timeout: int = 3,
    error_code: int = 408,
    error_message: str = "Server timed out while waiting on sender",
):
    """Wait for coroutine to finish and handle exceptions.

    :param coro: coroutine to wait for
    :param writer: writer to send error response to
    :param timeout: time to wait for coroutine to finish
    :param error_code: error code to send if coroutine times out
    :param error_message: error message to send if coroutine times out
        Return coroutine result if it finishes within timeout, otherwise
        return None.
    """
    try:
        return await asyncio.wait_for(coro, timeout)
    except asyncio.TimeoutError:
        log.warning(error_message)
        try:
            write_http_response(writer, error_code)
        except ConnectionError:
            pass


def http_request(coroutine):
    """Handle HTTP request message and pass it to coroutine."""

    @functools.wraps(coroutine)
    async def wrapper(self, reader, writer):
        msg = HTTPRequest(reader, writer)
        try:
            if await msg.read(timeout=3):
                await coroutine(self, reader, writer, msg)
            else:
                log.warning("Rejected HTTP message: %s", msg.error_message)
                return
        except ConnectionError:
            pass
        except Exception as e:
            log.error("".join(traceback.format_exception(e)))
        finally:
            try:
                await writer.drain()
            except ConnectionError:
                pass
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    return wrapper


def allowed_methods(*methods):
    """Decorate to allow only certain http methods."""

    def decorator(coroutine):
        @functools.wraps(coroutine)
        async def wrapper(self, reader, writer, msg):
            if msg.method not in methods:
                write_http_response(writer, 405, {"allow": ", ".join(methods)})
                log.warning("Invalid method %s", msg.method)
                return
            await coroutine(self, reader, writer, msg)

        return wrapper

    return decorator


class RequestHandler:
    """Allows to handle requests from different sources."""

    def __init__(self, root: chatbot.InterfaceRoot):
        """Initialise with interface root.

        :param root: must be already loaded
        """
        self.root = root

    @abstractmethod
    async def handle(self, reader, writer):
        """Handle request."""


class WebSocketHandler(RequestHandler):
    """Handle websocket connections."""

    @http_request
    @allowed_methods("GET")
    async def handle(self, reader, writer, msg):
        """Handle new websocket connection."""
        if "sec-websocket-key" not in msg.headers:
            write_http_response(writer, 400)
            log.warning("Missing Sec-WebSocket-Key header")
            return
        writer.write(websocket.handshake(msg.headers["sec-websocket-key"]))
        await writer.drain()
        bot = chatbot.Chat(
            str(uuid.uuid4()),
            lambda x: self.send_message(writer, x),
            self.root,
        )
        await bot.greet()
        await writer.drain()
        while True:
            frame = await wait_for_response(
                websocket.read_frame(reader),
                writer,
                timeout=300,
            )
            if frame.op_code == "TEXT":
                log.info("Asking: %s", frame.data.decode())
                msg = {}
                txt = frame.data.decode()
                try:
                    msg = json.loads(txt)
                except json.decoder.JSONDecodeError:
                    log.warning("User sent message with invalid json format: %s", txt)
                    self.send_error(writer, f"Invalid JSON format '{txt}'")
                if "text" in msg:
                    await bot.ask(chatbot.Message(msg["text"]))
                else:
                    self.send_error(writer, "Missing 'text' key in JSON")
            elif frame.op_code == "CLOSE":
                self.send_close(writer, frame.data)
                break
            elif frame.op_code == "PING":
                self.send_pong(writer, frame.data)
            await writer.drain()

    @staticmethod
    def send_close(writer, text):
        """Send close frame."""
        sendback = 0b1000100000000010
        sendback = sendback.to_bytes(2, "big")
        sendback += text
        writer.write(sendback)

    @staticmethod
    def send_pong(writer, data):
        """Send pong frame."""
        writer.write(websocket.get_frame("PONG", data))

    @staticmethod
    def send_packet(writer, packet):
        """Send packet."""
        packet = json.dumps(packet)
        log.debug("Sending: %s", packet)
        writer.write(websocket.get_frame("TEXT", packet.encode()))

    def send_message(self, writer, message):
        """Send back message."""
        packet = {"author": message.author, "text": message.text}
        self.send_packet(writer, packet)

    def send_error(self, writer, txt):
        """Send error message."""
        self.send_packet(writer, {"error": txt})


class SlackHandler(RequestHandler):
    """Handle slack connections."""

    @http_request
    @allowed_methods("POST")
    async def handle(self, reader, writer, msg):
        """Handle new slack request."""
        if not await msg.read_body():
            return
        if self.valid_slack_request(
            writer, msg.headers, msg.body, self.root.conf["slack_signing_secret"]
        ):
            try:
                body = json.loads(msg.body)
            except json.JSONDecodeError:
                write_http_response(writer, 400)
                log.warning("Invalid Slack JSON format")
                return
            if "type" in body and "url_verification" == body["type"]:
                write_http_response(
                    writer,
                    200,
                    {"Content-Type": "text/plain; charset=utf-8"},
                    body=body["challenge"].encode("utf-8"),
                )
            else:
                write_http_response(writer, 200)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            if "event" in body:
                body = body["event"]
                if body["type"] == "message" and "bot_id" not in body:
                    if "user" in body:
                        slack_token = self.root.conf["slack_app_token"]
                        channel = body["channel"]
                        bot = chatbot.Chat(
                            body["user"],
                            lambda msg: slack.send_slack(slack_token, channel, msg),
                            self.root,
                        )
                        parts = []
                        parts.append(chatbot.MessagePart(body["text"]))
                        for binary, file_type in slack.get_attachments(
                            body, slack_token
                        ):
                            parts.append(chatbot.MessagePart("", binary, file_type))
                        await bot.ask(chatbot.Message(parts=parts, author=body["user"]))

    @staticmethod
    def valid_slack_request(writer, headers: dict, body: bytes, secret: bytes) -> bool:
        """Make sure request comes slack and is not tampered.

        :param writer: writer to send response
        :param headers: headers from request
        :param body: body of request
        :param secret: slack secret to verify signature
        """
        slack_sign = headers.get("X-Slack-Signature")
        slack_stamp = headers.get("X-Slack-Request-Timestamp", "0")
        if slack_sign is None or abs(time.time() - float(slack_stamp)) > 60 * 5:
            write_http_response(writer, 403)
            log.warning(
                "Invalid slack authorization headers",
            )
            return False
        sig = b"v0:" + slack_stamp.encode("ascii") + b":" + body
        hasher = hmac.new(secret.encode("ascii"), sig, digestmod="sha256")
        my_signature = "v0=" + hasher.hexdigest()
        if my_signature != slack_sign:
            write_http_response(writer, 403)
            log.warning("Invalid slack app ignature")
            return False
        return True


class EmailHandler(AsyncMessage):
    """Handle incoming emails as LMTP server."""

    def __init__(self, root: chatbot.InterfaceRoot):
        """Initialise email handler."""
        self.root = root
        super().__init__()

    async def handle_message(self, message: email.message.Message):
        """Handle email message."""
        bot = chatbot.Chat(
            message["to"],
            lambda msg: emailer.send_sync(
                self.root.conf["email_address"],
                message["from"],
                message.get("subject", ""),
                msg,
                self.root.conf["email_smtp_port"],
            ),
            self.root,
        )
        await bot.ask(emailer.serialise_email(message))


async def run_servers_stacked(shutdown_release: asyncio.Lock, *servers):
    """Run servers in stacked manner.

    :param shutdown_release: lock to wait on before shutting down
    """
    if len(servers) < 1:
        log.error("No servers configured to run")
    elif len(servers) < 2:
        async with servers[0]:
            async with shutdown_release:
                log.info("Server shutdown")
    else:
        async with servers[0]:
            await run_servers_stacked(shutdown_release, *servers[1:])


async def run_servers(*servers):
    """Run servers forever until SIGTERM/SIGINT received.

    :param servers: asyncio servers already started
    """
    # Lock to keep server running until interrupted
    shutdown = asyncio.Lock()
    await shutdown.acquire()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, shutdown.release)
    loop.add_signal_handler(signal.SIGINT, shutdown.release)
    await run_servers_stacked(shutdown, *servers)


async def build_slack_server(
    root: chatbot.InterfaceRoot, port: int, force_bind: bool = False
):
    """Build slack server from configuration."""
    return await asyncio.start_server(
        SlackHandler(root).handle,
        host="localhost",
        port=port,
        reuse_port=force_bind,
    )


async def build_servers(root: chatbot.Interface, conf: dict):
    """Build servers from configuration."""
    force_bind = conf.get("force_bind", False)
    servers = []
    if conf.get("websocket_port"):
        servers.append(
            await asyncio.start_server(
                WebSocketHandler(root).handle,
                host="localhost",
                port=conf["websocket_port"],
                reuse_port=force_bind,
            )
        )
    if conf.get("slack_port"):
        if conf.get("slack_signing_secret") is None:
            log.error("Slack secret not set, disabling slack server")
        elif conf.get("slack_app_token") is None:
            log.error("Slack app token not set, disabling slack server")
        else:
            servers.append(
                await build_slack_server(root, conf["slack_port"], force_bind)
            )
    if conf.get("email_port"):
        if conf.get("email_address") is None:
            log.error("No email address of the bot set, disabling email server")
        else:
            loop = asyncio.get_running_loop()
            servers.append(
                await loop.create_server(
                    functools.partial(LMTP, EmailHandler(root), loop=loop),
                    host="localhost",
                    port=conf["email_port"],
                    reuse_port=force_bind,
                )
            )
    return servers


async def run(conf: dict):
    """Start and run servers forever."""
    root = chatbot.InterfaceRoot(conf)
    root.load()
    try:
        servers = await build_servers(root, conf)
        await run_servers(*servers)
    finally:
        root.close()


def start(conf: dict) -> None:
    """Start server listening on given ports provided by conf.

    We serve forever until interrupted or terminated.
    """
    logging.basicConfig(level=conf.get("log_level", logging.WARNING))
    if "email_smtp_port" not in conf:
        conf["email_smtp_port"] = 25
    asyncio.run(run(conf))
