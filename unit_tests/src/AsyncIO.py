import re
import time
import asyncio
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
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

# Regex patterns for PII
email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
phone_pattern = re.compile(r"\+\d{1}-\d{3}-\d{3}-\d{4}")
ssn_pattern = re.compile(r"\d{3}-\d{2}-\d{4}")

patterns = [email_pattern, phone_pattern, ssn_pattern]

def find_pii_in_content(filename, content):
    pii_found = []
    for pattern in patterns:
        pii_found.extend(pattern.findall(content))
    return (filename, len(pii_found))

# Async threading version using ThreadPoolExecutor
async def async_threading_version(data):
    loop = asyncio.get_running_loop()
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = [loop.run_in_executor(pool, find_pii_in_content, filename, content) for filename, content in data]
        results = await asyncio.gather(*tasks)
    return results

def hash_mask(pii):
    return hashlib.sha256(pii.encode()).hexdigest()[:10]  # Short hash for masking

def replacer(match):
    return hash_mask(match.group(0))

def mask_content(filename, content):
    for pattern in patterns:
        content = pattern.sub(replacer, content)
    return (filename, len(content))

async def async_multiprocessing_version(data):
    loop = asyncio.get_running_loop()
    results = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        tasks = [loop.run_in_executor(pool, mask_content, filename, content) for filename, content in data]
        results = await asyncio.gather(*tasks)
    return results

test_data = generate_test_data()

async def main():
    # Async threading (search PII)
    start = time.perf_counter()
    threading_results = await async_threading_version(test_data)
    threading_time = time.perf_counter() - start

    # Async multiprocessing (mask PII)
    start = time.perf_counter()
    mp_results = await async_multiprocessing_version(test_data)
    mp_time = time.perf_counter() - start


    print(f"Async threading time: {threading_time:.4f} seconds")
    print(f"Async multiprocessing time: {mp_time:.4f} seconds")
    print("Async threading results sample:", threading_results[:2])
    print("Async multiprocessing results sample:", mp_results[:2])

asyncio.run(main())
