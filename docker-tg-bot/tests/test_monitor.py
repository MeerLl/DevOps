import asyncio

import pytest

from bot.config import Config
from bot.monitor import Autoscaler


class DummyDocker:
    def __init__(self, cpus):
        self.cpus = cpus
        self.compose_calls = []

    async def list_containers(self, all_=True):
        class C:
            def __init__(self):
                self._id = "id1"
                self._container = {"Names": ["/my_stack_web-1"], "Status": "Up"}

        return [C()]

    async def get_container_stats_cpu(self, cid):
        return self.cpus[0]

    async def compose_scale(self, project, service, replicas, project_dir):
        self.compose_calls.append((project, service, replicas, project_dir))


@pytest.mark.asyncio
async def test_autoscaler_scales_up(monkeypatch):
    cfg = Config(
        telegram_token="x",
        allowed_chat_ids=[1],
        autoscale_interval=0,
        cpu_threshold=0.7,
        max_replicas=3,
        min_replicas=1,
        compose_project="my_stack",
        compose_service="web",
    )

    docker = DummyDocker(cpus=[0.9])
    notifications = []

    async def notify(msg: str):
        notifications.append(msg)

    autoscaler = Autoscaler(cfg, docker, notify)

    async def one_loop():
        autoscaler._replicas = 1
        await autoscaler._loop()

    async def fake_sleep(_):
        autoscaler._running = False

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await one_loop()

    assert docker.compose_calls
    project, service, replicas, project_dir = docker.compose_calls[0]
    assert project == "my_stack"
    assert service == "web"
    assert replicas == 2

