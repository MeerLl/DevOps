import asyncio

import pytest

from bot.config import Config
from bot.monitor import Autoscaler


class DummyDocker:
    def __init__(self, cpus, containers=None, scale_ok=True):
        self.cpus = cpus
        self.compose_calls = []
        self._scale_ok = scale_ok
        self._containers = containers

    async def list_containers(self, all_=True):
        if self._containers is not None:
            return self._containers

        class C:
            def __init__(self):
                self._id = "id1"
                self._container = {"Names": ["/my_stack_web-1"], "Status": "Up"}

        return [C()]

    async def get_container_stats_cpu(self, cid):
        return self.cpus[0]

    async def compose_scale(self, project, service, replicas, project_dir):
        if not self._scale_ok:
            raise RuntimeError("compose error")
        self.compose_calls.append((project, service, replicas, project_dir))


def _base_cfg():
    return Config(
        telegram_token="x",
        allowed_chat_ids=[1],
        autoscale_interval=0,
        cpu_threshold=0.7,
        max_replicas=3,
        min_replicas=1,
        compose_project="my_stack",
        compose_service="web",
    )


@pytest.mark.asyncio
async def test_autoscaler_scales_up(monkeypatch):
    cfg = _base_cfg()
    docker = DummyDocker(cpus=[0.9])
    notifications = []

    async def notify(msg: str):
        notifications.append(msg)

    autoscaler = Autoscaler(cfg, docker, notify)

    async def fake_sleep(_):
        autoscaler._running = False

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    autoscaler._replicas = 1
    await autoscaler._loop()

    assert docker.compose_calls
    project, service, replicas, project_dir = docker.compose_calls[0]
    assert project == "my_stack"
    assert service == "web"
    assert replicas == 2
    assert any("Autoscale" in m for m in notifications)


@pytest.mark.asyncio
async def test_autoscaler_scales_down(monkeypatch):
    cfg = _base_cfg()
    docker = DummyDocker(cpus=[0.1])
    notifications = []

    async def notify(msg: str):
        notifications.append(msg)

    autoscaler = Autoscaler(cfg, docker, notify)

    async def fake_sleep(_):
        autoscaler._running = False

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    autoscaler._replicas = 3
    await autoscaler._loop()

    assert docker.compose_calls
    _, _, replicas, _ = docker.compose_calls[0]
    assert replicas == 2
    assert any("Autoscale" in m for m in notifications)


@pytest.mark.asyncio
async def test_autoscaler_no_matching_containers(monkeypatch):
    cfg = _base_cfg()

    class C:
        def __init__(self):
            self._id = "id1"
            self._container = {"Names": ["/other_stack_web-1"], "Status": "Up"}

    docker = DummyDocker(cpus=[0.9], containers=[C()])
    notifications = []

    async def notify(msg: str):
        notifications.append(msg)

    autoscaler = Autoscaler(cfg, docker, notify)

    async def fake_sleep(_):
        autoscaler._running = False

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    autoscaler._replicas = 2
    await autoscaler._loop()

    assert docker.compose_calls
    _, _, replicas, _ = docker.compose_calls[0]
    assert replicas == cfg.min_replicas


@pytest.mark.asyncio
async def test_autoscaler_handles_errors(monkeypatch):
    cfg = _base_cfg()

    class FailingDocker(DummyDocker):
        async def list_containers(self, all_=True):
            raise RuntimeError("boom")

    docker = FailingDocker(cpus=[0.9])
    notifications = []

    async def notify(msg: str):
        notifications.append(msg)

    autoscaler = Autoscaler(cfg, docker, notify)

    async def fake_sleep(_):
        autoscaler._running = False

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await autoscaler._loop()

    assert any("Autoscaler error" in m for m in notifications)


@pytest.mark.asyncio
async def test_autoscaler_start_and_stop(monkeypatch):
    cfg = _base_cfg()
    docker = DummyDocker(cpus=[0.9])
    notifications = []

    async def notify(msg: str):
        notifications.append(msg)

    autoscaler = Autoscaler(cfg, docker, notify)

    async def fake_loop(self):
        self._running = False

    monkeypatch.setattr(Autoscaler, "_loop", fake_loop)

    autoscaler.start()
    assert autoscaler._task is not None

    await autoscaler.stop()
    assert autoscaler._running is False

