def auth_middleware(
    token: str,
    header: str = "Authorization",
    prefix: str = "Bearer "
):
    def middleware(handler):
        value = handler.headers.get(header)

        if not value or not value.startswith(prefix):
            handler.send_response(401)
            handler.send_header("Content-Type", "text/plain")
            handler.end_headers()
            handler.wfile.write(b"Unauthorized")
            raise StopIteration

        received = value[len(prefix):].strip()
        if received != token:
            handler.send_response(403)
            handler.send_header("Content-Type", "text/plain")
            handler.end_headers()
            handler.wfile.write(b"Forbidden")
            raise StopIteration

    return middleware
