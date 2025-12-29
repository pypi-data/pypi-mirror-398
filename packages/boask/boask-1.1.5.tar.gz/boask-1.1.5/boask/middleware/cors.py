def cors(
    allow_origin="*",
    allow_methods="GET,POST,PUT,DELETE,OPTIONS",
    allow_headers="Content-Type, Authorization"
):
    def middleware(handler):
        handler.send_header("Access-Control-Allow-Origin", allow_origin)
        handler.send_header("Access-Control-Allow-Methods", allow_methods)
        handler.send_header("Access-Control-Allow-Headers", allow_headers)

        if handler.command == "OPTIONS":
            handler.send_response(204)
            handler.end_headers()
            raise StopIteration

    return middleware
