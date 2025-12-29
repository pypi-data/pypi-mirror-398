import urllib.parse
from .users import USERS, hash_password

def register(handler):
    if handler.command != "POST":
        handler.send_response(405)
        handler.end_headers()
        return b"Method Not Allowed"

    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length).decode("utf-8")

    data = urllib.parse.parse_qs(body)
    username = data.get("username", [None])[0]
    password = data.get("password", [None])[0]

    if not username or not password:
        handler.send_response(400)
        handler.end_headers()
        return b"Missing username or password"

    if username in USERS:
        handler.send_response(409)
        handler.end_headers()
        return b"User already exists"

    USERS[username] = hash_password(password)

    handler.send_response(201)
    handler.end_headers()
    return b"User registered"
