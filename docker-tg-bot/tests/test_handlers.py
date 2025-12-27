import types

import pytest

from bot.config import Config
from bot.docker_client import DockerClient
from bot.handlers import create_handlers


class DummyUpdate:
    def __init__(self, chat_id=1, text=""):
        self.effective_chat = types.SimpleNamespace(id=chat_id)
        self._texts: list[str] = []
        self._docs: list[object] = []

        async def _reply_text(text, **kwargs):
            self._texts.append(text)

        async def _reply_doc(document, **kwargs):
            self._docs.append(document)

        self.message = types.SimpleNamespace(
            text=text,
            reply_text=_reply_text,
            reply_document=_reply_doc,
        )


class DummyContext:
    def __init__(self, args=None):
        self.args = args or []


def _cfg():
    return Config(
        telegram_token="x",
        allowed_chat_ids=[1],
        autoscale_interval=10,
        cpu_threshold=0.7,
        max_replicas=5,
        min_replicas=1,
        compose_project="my_stack",
        compose_service="web",
        compose_project_dir="/tmp",
    )


@pytest.mark.asyncio
async def test_list_cmd_auth(monkeypatch, tmp_path):
    cfg = _cfg()

    class DummyDocker(DockerClient):
        async def list_containers(self, all_=True):
            class C:
                def __init__(self):
                    self._id = "abc123456789"
                    self._container = {
                        "Names": ["/foo"],
                        "Status": "Up 1 second",
                    }

            return [C()]

    docker = DummyDocker()
    handlers = create_handlers(cfg, docker)
    list_cmd = handlers["list"]


    upd = DummyUpdate(chat_id=1)
    ctx = DummyContext()
    await list_cmd(upd, ctx)
    assert any("foo" in t for t in upd._texts)


    upd2 = DummyUpdate(chat_id=999)
    await list_cmd(upd2, ctx)
    assert not upd2._texts


@pytest.mark.asyncio
async def test_start_cmd_and_auth(monkeypatch):
    cfg = _cfg()

    class DummyDocker(DockerClient):
        pass

    docker = DummyDocker()
    handlers = create_handlers(cfg, docker)
    start_cmd = handlers["start"]

    upd = DummyUpdate(chat_id=1)
    ctx = DummyContext()
    await start_cmd(upd, ctx)


    assert upd._texts
    assert "Docker bot ready" in upd._texts[0]


@pytest.mark.asyncio
async def test_logs_cmd_success_and_missing(monkeypatch, tmp_path):
    cfg = _cfg()

    class DummyDocker(DockerClient):
        async def container_logs_to_file(self, name, path, tail=200):

            with open(path, "w", encoding="utf-8") as f:
                f.write("log1\nlog2\n")
            return path

    docker = DummyDocker()
    handlers = create_handlers(cfg, docker)
    logs_cmd = handlers["logs"]


    upd_no_args = DummyUpdate(chat_id=1)
    ctx_no_args = DummyContext(args=[])
    await logs_cmd(upd_no_args, ctx_no_args)
    assert any("Usage: /logs" in t for t in upd_no_args._texts)


    upd_ok = DummyUpdate(chat_id=1)
    ctx_ok = DummyContext(args=["foo"])
    await logs_cmd(upd_ok, ctx_ok)

    assert upd_ok._docs


    class FailingDocker(DockerClient):
        async def container_logs_to_file(self, name, path, tail=200):
            raise ValueError("Container foo not found")

    docker2 = FailingDocker()
    handlers2 = create_handlers(cfg, docker2)
    logs_cmd2 = handlers2["logs"]

    upd_fail = DummyUpdate(chat_id=1)
    ctx_fail = DummyContext(args=["foo"])
    await logs_cmd2(upd_fail, ctx_fail)
    assert any("Container foo not found" in t for t in upd_fail._texts)


@pytest.mark.asyncio
async def test_start_stop_restart_rmc_cmds(monkeypatch):
    cfg = _cfg()

    class DummyDocker(DockerClient):
        def __init__(self, ok=True):
            self._ok = ok

        async def start_container(self, name: str) -> bool:
            return self._ok

        async def stop_container(self, name: str) -> bool:
            return self._ok

        async def restart_container(self, name: str) -> bool:
            return self._ok

        async def remove_container(self, name: str, force: bool = False) -> bool:
            return self._ok

    docker = DummyDocker(ok=True)
    handlers = create_handlers(cfg, docker)

    for cmd_name, usage, ok_text in [
        ("startc", "Usage: /startc", "Started"),
        ("stopc", "Usage: /stopc", "Stopped"),
        ("restartc", "Usage: /restartc", "Restarted"),
        ("rmc", "Usage: /rmc", "Removed"),
    ]:
        cmd = handlers[cmd_name]


        upd_no_args = DummyUpdate(chat_id=1)
        ctx_no_args = DummyContext(args=[])
        await cmd(upd_no_args, ctx_no_args)
        assert any(usage in t for t in upd_no_args._texts)


        upd_ok = DummyUpdate(chat_id=1)
        ctx_ok = DummyContext(args=["foo"])
        await cmd(upd_ok, ctx_ok)
        assert any(ok_text in t for t in upd_ok._texts)


    docker_fail = DummyDocker(ok=False)
    handlers_fail = create_handlers(cfg, docker_fail)
    startc_cmd = handlers_fail["startc"]

    upd_fail = DummyUpdate(chat_id=1)
    ctx_fail = DummyContext(args=["foo"])
    await startc_cmd(upd_fail, ctx_fail)
    assert any("Container not found" in t for t in upd_fail._texts)


@pytest.mark.asyncio
async def test_new_and_scale_cmds(monkeypatch, tmp_path):
    cfg = _cfg()

    class DummyContainer:
        def __init__(self):
            self._id = "abc123456789"

    class DummyDocker(DockerClient):
        async def create_container(self, image: str, name=None):
            self.last_image = image
            self.last_name = name
            return DummyContainer()

        async def compose_scale(self, project, service, replicas, project_dir):
            self.last_scale = (project, service, replicas, project_dir)

    docker = DummyDocker()
    handlers = create_handlers(cfg, docker)
    new_cmd = handlers["new"]
    scale_cmd = handlers["scale"]


    upd_new_no_args = DummyUpdate(chat_id=1)
    ctx_new_no_args = DummyContext(args=[])
    await new_cmd(upd_new_no_args, ctx_new_no_args)
    assert any("Usage: /new" in t for t in upd_new_no_args._texts)


    upd_new_ok = DummyUpdate(chat_id=1)
    ctx_new_ok = DummyContext(args=["nginx:latest", "my-nginx"])
    await new_cmd(upd_new_ok, ctx_new_ok)
    assert docker.last_image == "nginx:latest"
    assert docker.last_name == "my-nginx"
    assert any("Created:" in t for t in upd_new_ok._texts)


    upd_scale_no_args = DummyUpdate(chat_id=1)
    ctx_scale_no_args = DummyContext(args=[])
    await scale_cmd(upd_scale_no_args, ctx_scale_no_args)
    assert any("Usage: /scale" in t for t in upd_scale_no_args._texts)


    upd_scale_ok = DummyUpdate(chat_id=1)
    ctx_scale_ok = DummyContext(args=["3"])
    await scale_cmd(upd_scale_ok, ctx_scale_ok)

    assert docker.last_scale == (
        "my_stack",
        "web",
        3,
        "/tmp",
    )
    assert any("Scaled my_stack/web to 3" in t for t in upd_scale_ok._texts)


@pytest.mark.asyncio
async def test_handlers_auth_block(monkeypatch):
    cfg = _cfg()

    class DummyDocker(DockerClient):
        async def list_containers(self, all_=True):
            return []

    docker = DummyDocker()
    handlers = create_handlers(cfg, docker)
    list_cmd = handlers["list"]


    upd = DummyUpdate(chat_id=999)
    ctx = DummyContext()
    await list_cmd(upd, ctx)
    assert upd._texts == []

