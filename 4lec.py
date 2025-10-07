#-CPU bond -I/O bound _threading -GIL multiprocessing

# import threading
# import time

# value = 0
# lock = threading.RLock()

# def worker(n) -> None:
#     global value
#     print(f"[{threading.current_thread().name}] start {n}")
#     time.sleep(0.5)
#     with lock:
#         value: int = value + 1
#     print(f"[{threading.current_thread().name}] done {n}")

# threads: list[Thread] = [threading.Thread(target=worker, args=(i,), name=f"t{i}") for i in range(3)]
# for t in threads: t.start()
# for t in threads: t.join()
# print("All done")
# print(value)

import threading, time

event = threading.Event()

def waiter() -> None:
    print("waiting..")
    event.wait()
    print("go!")
threading.Thread(target=waiter).start()
time.sleep(1)
event.set()

from concurrent.futures import ThreadPoolExecutor, as_completed
import time, random

def fetch(url) -> str:
    time.sleep(random.uniform(0.1, 0.4)) #имитация I/O
    return f"{url} -> OK"

urls: list[str] = [f"https://api.example.com/{i}" for i in range(8)]

with ThreadPoolExecutor(max_