# protocol.py - shared message helpers for the tic-tac-toe client and server.
# Messages are JSON with a newline at the end (see protocol_blueprint.md).

import argparse
import json

ENCODING = "utf-8"
RECV_SIZE = 4096
MIN_PORT = 1024
MAX_PORT = 65535


def send_msg(sock, msg):
    # dict -> JSON + "\n"
    data = (json.dumps(msg) + "\n").encode(ENCODING)
    sock.sendall(data)


class MessageReader:
    # TCP can split or combine messages, so keep a buffer and only
    # return a message once we've seen its "\n".

    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""

    def read(self):
        while True:
            while b"\n" not in self.buffer:
                chunk = self.sock.recv(RECV_SIZE)
                if not chunk:
                    return None  # 0 bytes = other side closed the connection
                self.buffer += chunk

            line, self.buffer = self.buffer.split(b"\n", 1)
            if not line.strip():
                continue

            try:
                msg = json.loads(line.decode(ENCODING))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {"msg_type": "MALFORMED"}
            if not isinstance(msg, dict):
                return {"msg_type": "MALFORMED"}
            return msg


def port_type(value):
    # used by argparse to check the -p argument
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a valid port number")
    if not MIN_PORT <= port <= MAX_PORT:
        raise argparse.ArgumentTypeError(
            f"port must be between {MIN_PORT} and {MAX_PORT} (got {port})")
    return port