import pytest

from bot.docker_client import DockerClient


@pytest.mark.asyncio
async def test_logs_to_file(tmp_path, monkeypatch):
    async def fake_container_logs(self, name, tail=100):
        return "line1\nline2\n"

    client = DockerClient()
    monkeypatch.setattr(
        client, "container_logs", fake_container_logs.__get__(client)
    )

    path = tmp_path / "logs.txt"
    res = await client.container_logs_to_file("foo", str(path), tail=2)

    assert res == str(path)
    assert path.read_text() == "line1\nline2\n"

