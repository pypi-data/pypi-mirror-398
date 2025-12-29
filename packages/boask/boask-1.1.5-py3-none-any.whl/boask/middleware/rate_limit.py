import time

def rate_limit(max_requests=60, per_seconds=60):
    hits = {}

    def middleware(handler):
        ip = handler.client_address[0]
        now = time.time()

        window = hits.get(ip, [])
        window = [t for t in window if now - t < per_seconds]

        if len(window) >= max_requests:
            handler.send_response(429)
            handler.send_header("Content-Type", "text/plain")
            handler.send_header("Retry-After", str(per_seconds))
            handler.end_headers()
            handler.wfile.write(b"Too Many Requests")
            raise StopIteration

        window.append(now)
        hits[ip] = window

    return middleware
