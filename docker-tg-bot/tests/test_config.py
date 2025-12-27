import os

import pytest

from bot.config import Config


def test_from_env_ok(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "token123")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHATS", "1, 2,3")
    monkeypatch.setenv("AUTOSCALE_INTERVAL", "15")
    monkeypatch.setenv("CPU_THRESHOLD", "0.8")
    monkeypatch.setenv("MAX_REPLICAS", "10")
    monkeypatch.setenv("MIN_REPLICAS", "2")
    monkeypatch.setenv("COMPOSE_PROJECT", "proj")
    monkeypatch.setenv("COMPOSE_SERVICE", "svc")
    monkeypatch.setenv("COMPOSE_PROJECT_DIR", "/proj-dir")

    cfg = Config.from_env()

    assert cfg.telegram_token == "token123"
    assert cfg.allowed_chat_ids == [1, 2, 3]
    assert cfg.autoscale_interval == 15
    assert cfg.cpu_threshold == 0.8
    assert cfg.max_replicas == 10
    assert cfg.min_replicas == 2
    assert cfg.compose_project == "proj"
    assert cfg.compose_service == "svc"
    assert cfg.compose_project_dir == "/proj-dir"


def test_from_env_missing_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHATS", "1")

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_missing_chats(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "token123")
    monkeypatch.delenv("TELEGRAM_ALLOWED_CHATS", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()

