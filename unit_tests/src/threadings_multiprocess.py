import re
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import hashlib
import random
import string

def generate_pii_text():
    emails = [f"user{random.randint(1,100)}@example.com" for _ in range(5)]
    phones = [f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}" for _ in range(5)]
    ssns = [f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}" for _ in range(5)]
    text = " ".join(emails + phones + ssns) + " " + "".join(random.choices(string.ascii_letters + string.digits, k=1000))
    return text

def generate_test_data(num_files=40, lines_per_file=500):
    data = []
    for i in range(num_files):
        content = "\n".join([generate_pii_text() for _ in range(lines_per_file)])
        data.append((f"file_{i}", content))
    return data

email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
phone_pattern = re.compile(r"\+\d{1}-\d{3}-\d{3}-\d{4}")
ssn_pattern = re.compile(r"\d{3}-\d{2}-\d{4}")

patterns = [email_pattern, phone_pattern, ssn_pattern]


def find_pii_in_content(filename, content, result_queue, lock):
    pii_found = []
    for pattern in patterns:
        pii_found.extend(pattern.findall(content))
    with lock:
        result_queue.put((filename, len(pii_found)))

def threading_version(data):
    result_queue = Queue()
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=4) as executor:
        for filename, content in data:
            executor.submit(find_pii_in_content, filename, content, result_queue, lock)
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    return results

def hash_mask(pii):
    return hashlib.sha256(pii.encode()).hexdigest()[:10]  #short hash for masking

def replacer(match):
    return hash_mask(match.group(0))

# Multiprocessing worker
def mp_worker(start_idx, end_idx, result_queue):
    for i in range(start_idx, end_idx):
        filename, content = test_data[i]
        for pattern in patterns:
            content = pattern.sub(replacer, content)
        result_queue.put((filename, len(content)))

#multiprocessing version
def multiprocessing_version(data):
    result_queue = multiprocessing.Queue()
    num_processes = 4
    chunk_size = len(data) // num_processes
    processes = []
    for i in range(num_processes):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_processes - 1 else len(data)
        p = multiprocessing.Process(target=mp_worker, args=(start, end, result_queue))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    return results

#test driver
test_data = generate_test_data()

#threading (search PII)
start = time.perf_counter()
threading_results = threading_version(test_data)
threading_time = time.perf_counter() - start

#multiprocessing (mask PII)
start = time.perf_counter()
mp_results = multiprocessing_version(test_data)
mp_time = time.perf_counter() - start

print(f"Threading time: {threading_time:.3f} seconds")
print(f"Multiprocessing time: {mp_time:.3f} seconds")
print("Threading results sample:", threading_results[:2])
print("Multiprocessing results sample:", mp_results[:2])
