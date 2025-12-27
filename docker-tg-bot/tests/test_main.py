import asyncio
import types

import pytest

from bot import main as main_mod


class DummyApp:
    def __init__(self):
        self.handlers = []
        self.bot = types.SimpleNamespace(send_message=self._send_message)
        self.run_polling_called = False
        self.sent_messages = []

    async def _send_message(self, chat_id, text):
        self.sent_messages.append((chat_id, text))

    def add_handler(self, handler):
        self.handlers.append(handler)

    def run_polling(self):
        self.run_polling_called = True


class DummyApplicationBuilder:
    def __init__(self):
        self._token = None

    def token(self, token):
        self._token = token
        return self

    def build(self):
        return DummyApp()


class DummyDocker:
    def __init__(self):
        self.closed = False


class DummyAutoscaler:
    def __init__(self, cfg, docker, notify):
        self.cfg = cfg
        self.docker = docker
        self.notify = notify
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    async def stop(self):
        self.stopped = True


def _setup_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHATS", "1,2")


def fake_asyncio_run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_main_runs_setup_and_polling(monkeypatch):
    _setup_env(monkeypatch)

    monkeypatch.setattr(main_mod, "ApplicationBuilder", DummyApplicationBuilder)
    monkeypatch.setattr(main_mod, "DockerClient", DummyDocker)
    monkeypatch.setattr(main_mod, "Autoscaler", DummyAutoscaler)
    monkeypatch.setattr(asyncio, "run", fake_asyncio_run)

    app_holder = {}

    def fake_run_polling(self):
        app_holder["app"] = self

    monkeypatch.setattr(DummyApp, "run_polling", fake_run_polling)

    main_mod.main()

    app = app_holder["app"]
    assert isinstance(app, DummyApp)

