import signal
import platform
import warnings
from contextlib import contextmanager
from pydantic import BaseModel, PositiveInt, ValidationError

class TimeoutConfig(BaseModel):
    seconds: PositiveInt

@contextmanager
def soft_timeout(seconds: int):
    try:
        config = TimeoutConfig(seconds=seconds)
    except ValidationError as e:
        # Правильно передаем ошибку дальше
        raise e

    is_unix = platform.system() != "Windows"
    old_handler = None

    def handle_timeout(signum, frame):
        raise TimeoutError("Operation timed out")

    if is_unix:
        old_handler = signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(config.seconds)
    else:
        warnings.warn("Soft-timeout is not supported on Windows, running as no-op", RuntimeWarning)

    try:
        yield
    finally:
        if is_unix and old_handler is not None:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

if __name__ == "__main__":
    import time

    try:
        with soft_timeout(2):
            print("Starting operation...")
            time.sleep(3)
            print("Operation completed.")
    except (TimeoutError, ValidationError) as e:
        print(f"Caught error: {e}")
