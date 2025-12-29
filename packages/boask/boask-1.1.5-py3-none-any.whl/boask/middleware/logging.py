import time

def logging_middleware(handler):
    if not hasattr(handler, "_start_time"):
        handler._start_time = time.time()
        return

    duration = (time.time() - handler._start_time) * 1000
    status = getattr(handler, "_last_status", 200)

    print(
        f"[BOASK] {handler.command} {handler.path} "
        f"-> {status} ({duration:.2f}ms)"
    )
