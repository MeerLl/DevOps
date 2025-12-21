import asyncio
import time
import logging
from statistics import mean
from typing import Dict, Any

from clients import (
    UrllibUserClient,
    RequestsUserClient,
    HttpxUserClient,
    AiohttpUserClient,
)
from otel_config import configure_opentelemetry, get_tracer, get_meter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("benchmark_otel")


TEST_USERS = [
    {"username": "ivan", "email": "ivan@example.com"},
    {"username": "maria", "email": "maria@example.com"},
    {"username": "petr", "email": "petr@example.com"},
]


def bench_sync_client(
    name: str,
    client,
    tracer,
    duration_hist,
    errors_counter,
    num_requests: int = 10,
) -> Dict[str, Any]:
    logger.info(f"=== {name} (sync) ===")
    times = []
    errors = 0

    with tracer.start_as_current_span(f"benchmark.{name}") as span_client:
        span_client.set_attribute("client.name", name)
        span_client.set_attribute("client.type", "sync")

        for i in range(num_requests):
            with tracer.start_as_current_span(f"{name}.iteration") as span_iter:
                span_iter.set_attribute("iteration", i)
                start = time.perf_counter()

                user_payload = TEST_USERS[i % len(TEST_USERS)].copy()
                user_payload["email"] = f"user{i}_{user_payload['email']}"

                try:
                    created = client.create_user(user_payload)
                    if not created or "id" not in created:
                        errors += 1
                        errors_counter.add(
                            1,
                            attributes={"client.name": name, "client.type": "sync"},
                        )
                        span_iter.set_attribute("status", "error")
                        span_iter.set_attribute("error.reason", "no id on create")
                        logger.warning("[%s] create_user returned no id: %r", name, created)
                        continue

                    user_id = created["id"]
                    span_iter.set_attribute("user.id", user_id)

                    _ = client.get_user(user_id)

                    updated = {**user_payload, "username": user_payload["username"] + "_updated"}
                    _ = client.update_user(user_id, updated)

                    _ = client.delete_user(user_id)

                    duration_ms = (time.perf_counter() - start) * 1000
                    times.append(duration_ms)

                    attributes = {
                        "client.name": name,
                        "client.type": "sync",
                    }
                    duration_hist.record(duration_ms, attributes=attributes)

                    span_iter.set_attribute("status", "success")
                    span_iter.set_attribute("duration_ms", round(duration_ms, 2))
                    span_iter.set_attribute("crud_ops", 4)

                    logger.info("[%s] iteration %d: %.2f ms", name, i, duration_ms)
                except Exception as e:
                    errors += 1
                    errors_counter.add(
                        1,
                        attributes={"client.name": name, "client.type": "sync"},
                    )
                    span_iter.set_attribute("status", "error")
                    span_iter.set_attribute("error.msg", str(e))
                    logger.exception("[%s] error on iteration %d", name, i)

    if hasattr(client, "close"):
        try:
            client.close()
        except Exception:
            pass

    return {"times": times, "errors": errors}


async def bench_httpx_client(
    tracer,
    duration_hist,
    errors_counter,
    num_requests: int = 10,
) -> Dict[str, Any]:
    name = "httpx"
    logger.info(f"=== {name} (async) ===")
    times = []
    errors = 0

    with tracer.start_as_current_span("benchmark.httpx") as span_client:
        span_client.set_attribute("client.name", name)
        span_client.set_attribute("client.type", "async")

        async with HttpxUserClient() as client:
            for i in range(num_requests):
                with tracer.start_as_current_span(f"{name}.iteration") as span_iter:
                    span_iter.set_attribute("iteration", i)
                    start = time.perf_counter()

                    user_payload = TEST_USERS[i % len(TEST_USERS)].copy()
                    user_payload["email"] = f"user{i}_{user_payload['email']}"

                    try:
                        created = await client.create_user(user_payload)
                        if not created or "id" not in created:
                            errors += 1
                            errors_counter.add(
                                1,
                                attributes={"client.name": name, "client.type": "async"},
                            )
                            span_iter.set_attribute("status", "error")
                            span_iter.set_attribute("error.reason", "no id on create")
                            logger.warning("[%s] create_user returned no id: %r", name, created)
                            continue

                        user_id = created["id"]
                        span_iter.set_attribute("user.id", user_id)

                        _ = await client.get_user(user_id)

                        updated = {**user_payload, "username": user_payload["username"] + "_updated"}
                        _ = await client.update_user(user_id, updated)

                        _ = await client.delete_user(user_id)

                        duration_ms = (time.perf_counter() - start) * 1000
                        times.append(duration_ms)

                        attributes = {
                            "client.name": name,
                            "client.type": "async",
                        }
                        duration_hist.record(duration_ms, attributes=attributes)

                        span_iter.set_attribute("status", "success")
                        span_iter.set_attribute("duration_ms", round(duration_ms, 2))
                        span_iter.set_attribute("crud_ops", 4)

                        logger.info("[%s] iteration %d: %.2f ms", name, i, duration_ms)
                    except Exception as e:
                        errors += 1
                        errors_counter.add(
                            1,
                            attributes={"client.name": name, "client.type": "async"},
                        )
                        span_iter.set_attribute("status", "error")
                        span_iter.set_attribute("error.msg", str(e))
                        logger.exception("[%s] error on iteration %d", name, i)

    return {"times": times, "errors": errors}


async def bench_aiohttp_client(
    tracer,
    duration_hist,
    errors_counter,
    num_requests: int = 10,
) -> Dict[str, Any]:
    name = "aiohttp"
    logger.info(f"=== {name} (async) ===")
    times = []
    errors = 0

    with tracer.start_as_current_span("benchmark.aiohttp") as span_client:
        span_client.set_attribute("client.name", name)
        span_client.set_attribute("client.type", "async")

        async with AiohttpUserClient() as client:
            for i in range(num_requests):
                with tracer.start_as_current_span(f"{name}.iteration") as span_iter:
                    span_iter.set_attribute("iteration", i)
                    start = time.perf_counter()

                    user_payload = TEST_USERS[i % len(TEST_USERS)].copy()
                    user_payload["email"] = f"user{i}_{user_payload['email']}"

                    try:
                        created = await client.create_user(user_payload)
                        if not created or "id" not in created:
                            errors += 1
                            errors_counter.add(
                                1,
                                attributes={"client.name": name, "client.type": "async"},
                            )
                            span_iter.set_attribute("status", "error")
                            span_iter.set_attribute("error.reason", "no id on create")
                            logger.warning("[%s] create_user returned no id: %r", name, created)
                            continue

                        user_id = created["id"]
                        span_iter.set_attribute("user.id", user_id)

                        _ = await client.get_user(user_id)

                        updated = {**user_payload, "username": user_payload["username"] + "_updated"}
                        _ = await client.update_user(user_id, updated)

                        _ = await client.delete_user(user_id)

                        duration_ms = (time.perf_counter() - start) * 1000
                        times.append(duration_ms)

                        attributes = {
                            "client.name": name,
                            "client.type": "async",
                        }
                        duration_hist.record(duration_ms, attributes=attributes)

                        span_iter.set_attribute("status", "success")
                        span_iter.set_attribute("duration_ms", round(duration_ms, 2))
                        span_iter.set_attribute("crud_ops", 4)

                        logger.info("[%s] iteration %d: %.2f ms", name, i, duration_ms)
                    except Exception as e:
                        errors += 1
                        errors_counter.add(
                            1,
                            attributes={"client.name": name, "client.type": "async"},
                        )
                        span_iter.set_attribute("status", "error")
                        span_iter.set_attribute("error.msg", str(e))
                        logger.exception("[%s] error on iteration %d", name, i)

    return {"times": times, "errors": errors}


def summarize(name: str, result: Dict[str, Any]) -> None:
    times = result["times"]
    errors = result["errors"]
    logger.info("--- %s summary ---", name)
    logger.info("  successful: %d", len(times))
    logger.info("  errors:     %d", errors)
    if times:
        logger.info("  min:        %.2f ms", min(times))
        logger.info("  max:        %.2f ms", max(times))
        logger.info("  avg:        %.2f ms", mean(times))


async def main():
    configure_opentelemetry()
    tracer = get_tracer("benchmark_otel")
    meter = get_meter("benchmark_otel")

    duration_hist = meter.create_histogram(
        name="http_client_iteration_ms",
        unit="ms",
        description="Duration of one CRUD iteration per client",
    )
    errors_counter = meter.create_counter(
        name="http_client_errors_total",
        unit="1",
        description="Number of failed CRUD iterations per client",
    )

    num_requests = 10
    logger.info(
        "Running OTEL benchmark against http://localhost:3100/users with %d iterations each",
        num_requests,
    )

    with tracer.start_as_current_span("benchmark.full") as root_span:
        root_span.set_attribute("num_requests", num_requests)
        root_span.set_attribute("clients", "urllib,requests,httpx,aiohttp")

        urllib_res = bench_sync_client(
            "urllib",
            UrllibUserClient(),
            tracer,
            duration_hist,
            errors_counter,
            num_requests,
        )
        requests_res = bench_sync_client(
            "requests",
            RequestsUserClient(),
            tracer,
            duration_hist,
            errors_counter,
            num_requests,
        )

        httpx_res, aiohttp_res = await asyncio.gather(
            bench_httpx_client(tracer, duration_hist, errors_counter, num_requests),
            bench_aiohttp_client(tracer, duration_hist, errors_counter, num_requests),
        )

        summarize("urllib", urllib_res)
        summarize("requests", requests_res)
        summarize("httpx", httpx_res)
        summarize("aiohttp", aiohttp_res)

    await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())

