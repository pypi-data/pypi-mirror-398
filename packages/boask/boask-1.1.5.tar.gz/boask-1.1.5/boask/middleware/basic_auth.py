import base64

def basic_auth(username: str, password: str):
    expected = base64.b64encode(
        f"{username}:{password}".encode()
    ).decode()

    def middleware(handler):
        auth = handler.headers.get("Authorization")

        if not auth or not auth.startswith("Basic "):
            handler.send_response(401)
            handler.send_header("WWW-Authenticate", 'Basic realm="Boask"')
            handler.end_headers()
            raise StopIteration

        received = auth.split(" ", 1)[1]
        if received != expected:
            handler.send_response(403)
            handler.end_headers()
            raise StopIteration

    return middleware
