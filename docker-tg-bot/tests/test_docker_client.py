import asyncio

import pytest

from bot.docker_client import DockerClient
import aiodocker


@pytest.mark.asyncio
async def test_logs_to_file(tmp_path, monkeypatch):
    async def fake_container_logs(self, name, tail=100):
        assert name == "foo"
        assert tail == 200
        return "line1\nline2\n"

    client = DockerClient()
    monkeypatch.setattr(
        client, "container_logs", fake_container_logs.__get__(client)
    )

    path = tmp_path / "logs.txt"
    res = await client.container_logs_to_file("foo", str(path), tail=200)
    assert res == str(path)
    assert path.read_text(encoding="utf-8") == "line1\nline2\n"


@pytest.mark.asyncio
async def test_container_logs_not_found(monkeypatch):
    class DummyDocker:
        class Containers:
            async def get(self, name):
                # эмулируем DockerError, как в реальном aiodocker
                raise aiodocker.exceptions.DockerError(
                    status=404, message="not found"
                )

        def __init__(self):
            self.containers = self.Containers()

        async def close(self):
            pass

    client = DockerClient()

    async def fake_get(self):
        return DummyDocker()

    monkeypatch.setattr(client, "_get", fake_get.__get__(client))

    with pytest.raises(ValueError):
        await client.container_logs("missing")


@pytest.mark.asyncio
async def test_start_stop_restart_remove_success(monkeypatch):
    class DummyContainer:
        def __init__(self):
            self.started = False
            self.stopped = False
            self.restarted = False
            self.deleted = False

        async def start(self):
            self.started = True

        async def stop(self):
            self.stopped = True

        async def restart(self):
            self.restarted = True

        async def delete(self, force=False):
            self.deleted = True
            self.force = force

    class DummyDocker:
        def __init__(self):
            self.container = DummyContainer()
            self.containers = self

        async def get(self, name):
            assert name == "foo"
            return self.container

        async def close(self):
            pass

    client = DockerClient()

    async def fake_get(self):
        return DummyDocker()

    monkeypatch.setattr(client, "_get", fake_get.__get__(client))

    assert await client.start_container("foo") is True
    assert await client.stop_container("foo") is True
    assert await client.restart_container("foo") is True
    assert await client.remove_container("foo", force=True) is True


@pytest.mark.asyncio
async def test_start_container_not_found(monkeypatch):
    class DummyDocker:
        def __init__(self):
            self.containers = self

        async def get(self, name):
            # код ловит именно DockerError
            raise aiodocker.exceptions.DockerError(
                status=404, message="not found"
            )

        async def close(self):
            pass

    client = DockerClient()

    async def fake_get(self):
        return DummyDocker()

    monkeypatch.setattr(client, "_get", fake_get.__get__(client))

    assert await client.start_container("foo") is False


@pytest.mark.asyncio
async def test_get_container_stats_cpu_ok(monkeypatch):
    class DummyContainer:
        async def stats(self, stream=False):
            # Сделаем простые числа, чтобы доля была 1.0
            yield {
                "cpu_stats": {
                    "cpu_usage": {
                        "total_usage": 200,
                        "percpu_usage": [1, 2],
                    },
                    "system_cpu_usage": 1200,
                },
                "precpu_stats": {
                    "cpu_usage": {"total_usage": 100},
                    "system_cpu_usage": 1100,
                },
            }

    class DummyDocker:
        def __init__(self):
            self.containers = self

        async def get(self, name):
            assert name == "foo"
            return DummyContainer()

        async def close(self):
            pass

    client = DockerClient()

    async def fake_get(self):
        return DummyDocker()

    monkeypatch.setattr(client, "_get", fake_get.__get__(client))

    cpu = await client.get_container_stats_cpu("foo")
    # просто проверяем, что вернулось положительное значение
    assert cpu > 0


@pytest.mark.asyncio
async def test_get_container_stats_cpu_not_found(monkeypatch):
    class DummyDocker:
        def __init__(self):
            self.containers = self

        async def get(self, name):
            # как и в других местах, эмулируем DockerError
            raise aiodocker.exceptions.DockerError(
                status=404, message="not found"
            )

        async def close(self):
            pass

    client = DockerClient()

    async def fake_get(self):
        return DummyDocker()

    monkeypatch.setattr(client, "_get", fake_get.__get__(client))

    with pytest.raises(ValueError):
        await client.get_container_stats_cpu("foo")


@pytest.mark.asyncio
async def test_compose_scale_success(monkeypatch, tmp_path):
    client = DockerClient()

    class DummyProc:
        def __init__(self, rc=0):
            self.returncode = rc

        async def communicate(self):
            return b"ok", b""

    async def fake_create_subprocess_shell(cmd, stdout=None, stderr=None):
        assert "docker compose -p my_stack" in cmd
        assert "--scale web=3" in cmd
        return DummyProc(rc=0)

    # в модуле docker_client asyncio импортируется внутри функции,
    # поэтому патчим сам объект asyncio.subprocess.create_subprocess_shell
    monkeypatch.setattr(
        asyncio, "create_subprocess_shell", fake_create_subprocess_shell
    )

    rc = await client.compose_scale(
        project="my_stack",
        service="web",
        replicas=3,
        project_dir=str(tmp_path),
    )
    assert rc == 0


@pytest.mark.asyncio
async def test_compose_scale_fail(monkeypatch, tmp_path):
    client = DockerClient()

    class DummyProc:
        def __init__(self, rc=1):
            self.returncode = rc

        async def communicate(self):
            return b"", b"error!"

    async def fake_create_subprocess_shell(cmd, stdout=None, stderr=None):
        return DummyProc(rc=1)

    monkeypatch.setattr(
        asyncio, "create_subprocess_shell", fake_create_subprocess_shell
    )

    with pytest.raises(RuntimeError):
        await client.compose_scale(
            project="my_stack",
            service="web",
            replicas=3,
            project_dir=str(tmp_path),
        )

