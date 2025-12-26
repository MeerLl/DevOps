import asyncio
import logging
from typing import Callable

from .config import Config
from .docker_client import DockerClient

log = logging.getLogger(__name__)


class Autoscaler:
    def __init__(
        self,
        cfg: Config,
        docker: DockerClient,
        notify_func: Callable[[str], "asyncio.Future"],
    ):
        self.cfg = cfg
        self.docker = docker
        self.notify = notify_func

        self._task: asyncio.Task | None = None
        self._running = False
        self._replicas = cfg.min_replicas

    async def _measure_cpu_avg(self) -> float:
        containers = await self.docker.list_containers(all_=False)
        cpu_values: list[float] = []

        for c in containers:
            name = c._container.get("Names", [""])[0].lstrip("/")
            if not name.startswith(
                f"{self.cfg.compose_project}_{self.cfg.compose_service}"
            ):
                continue
            cpu = await self.docker.get_container_stats_cpu(c._id)
            cpu_values.append(cpu)

        if not cpu_values:
            return 0.0

        return sum(cpu_values) / len(cpu_values)

    async def _loop(self):
        self._running = True
        try:
            while self._running:
                try:
                    cpu_avg = await self._measure_cpu_avg()
                    log.info("Autoscaler CPU avg=%.2f", cpu_avg)

                    # простое правило:
                    #  > threshold — +1 реплика
                    #  < threshold / 2 — -1 реплика (но не ниже min)
                    new_replicas = self._replicas
                    if cpu_avg > self.cfg.cpu_threshold:
                        new_replicas = min(
                            self.cfg.max_replicas, self._replicas + 1
                        )
                    elif (
                        cpu_avg < self.cfg.cpu_threshold / 2
                        and self._replicas > self.cfg.min_replicas
                    ):
                        new_replicas = max(
                            self.cfg.min_replicas, self._replicas - 1
                        )

                    if new_replicas != self._replicas:
                        await self.docker.compose_scale(
                            self.cfg.compose_project,
                            self.cfg.compose_service,
                            new_replicas,
                            self.cfg.compose_project_dir,
                        )
                        msg = (
                            f"Autoscale: {self._replicas} -> {new_replicas} "
                            f"replicas (CPU avg={cpu_avg:.2f})"
                        )
                        await self.notify(msg)
                        self._replicas = new_replicas

                except Exception as e:
                    log.exception("Autoscaler error: %s", e)
                    try:
                        await self.notify(f"Autoscaler error: {e}")
                    except Exception:
                        log.exception("Failed to send autoscaler error notification")

                await asyncio.sleep(self.cfg.autoscale_interval)
        except asyncio.CancelledError:
            # тихое завершение при остановке приложения
            pass

    def start(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

