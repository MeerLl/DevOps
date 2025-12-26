import types

import pytest

from bot.config import Config
from bot.docker_client import DockerClient
from bot.handlers import create_handlers


class DummyUpdate:
    def __init__(self, chat_id=1):
        self.effective_chat = types.SimpleNamespace(id=chat_id)
        self._texts = []
        self._docs = []

        async def _reply_text(text):
            self._texts.append(text)

        async def _reply_doc(document):
            self._docs.append(document)

        self.message = types.SimpleNamespace(
            text="", reply_text=_reply_text, reply_document=_reply_doc
        )


class DummyContext:
    def __init__(self, args=None):
        self.args = args or []


@pytest.mark.asyncio
async def test_list_cmd_auth(monkeypatch, tmp_path):
    cfg = Config(
        telegram_token="x",
        allowed_chat_ids=[1],
        autoscale_interval=10,
        cpu_threshold=0.7,
        max_replicas=5,
        min_replicas=1,
        compose_project="my_stack",
        compose_service="web",
    )

    class DummyDocker(DockerClient):
        async def list_containers(self, all_=True):
            class C:
                def __init__(self):
                    self._id = "abc123"
                    self._container = {"Names": ["/foo"], "Status": "Up 1 second"}

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

