import os
from typing import List, Optional

import aiodocker


class DockerClient:
    def __init__(self):
        self._base_url = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")

    async def _get(self) -> aiodocker.Docker:
        # каждый вызов создаёт новый клиент; его нужно закрыть после использования
        return aiodocker.Docker(url=self._base_url)

    async def list_containers(self, all_: bool = True):
        docker = await self._get()
        try:
            return await docker.containers.list(all=all_)
        finally:
            await docker.close()

    async def get_container(self, name: str):
        docker = await self._get()
        try:
            try:
                return await docker.containers.get(name)
            except aiodocker.exceptions.DockerError:
                return None
        finally:
            await docker.close()

    async def container_logs(self, name: str, tail: int = 100) -> str:
        docker = await self._get()
        try:
            try:
                container = await docker.containers.get(name)
            except aiodocker.exceptions.DockerError:
                raise ValueError(f"Container {name} not found")
            logs = await container.log(stdout=True, stderr=True, tail=tail)
            return "".join(logs)
        finally:
            await docker.close()

    async def container_logs_to_file(
        self, name: str, path: str, tail: int = 100
    ) -> str:
        logs = await self.container_logs(name, tail=tail)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(logs)
        return path

    async def start_container(self, name: str) -> bool:
        docker = await self._get()
        try:
            container = await docker.containers.get(name)
            await container.start()
            return True
        except aiodocker.exceptions.DockerError:
            return False
        finally:
            await docker.close()

    async def stop_container(self, name: str) -> bool:
        docker = await self._get()
        try:
            container = await docker.containers.get(name)
            await container.stop()
            return True
        except aiodocker.exceptions.DockerError:
            return False
        finally:
            await docker.close()

    async def restart_container(self, name: str) -> bool:
        docker = await self._get()
        try:
            container = await docker.containers.get(name)
            await container.restart()
            return True
        except aiodocker.exceptions.DockerError:
            return False
        finally:
            await docker.close()

    async def remove_container(self, name: str, force: bool = False) -> bool:
        docker = await self._get()
        try:
            container = await docker.containers.get(name)
            await container.delete(force=force)
            return True
        except aiodocker.exceptions.DockerError:
            return False
        finally:
            await docker.close()

    async def create_container(
        self,
        image: str,
        name: Optional[str] = None,
        cmd: Optional[List[str]] = None,
    ):
        docker = await self._get()
        try:
            config = {"Image": image}
            if cmd:
                config["Cmd"] = cmd
            container = await docker.containers.create_or_replace(
                name=name, config=config
            )
            return container
        finally:
            await docker.close()

    async def get_container_stats_cpu(self, name: str) -> float:
        docker = await self._get()
        try:
            try:
                container = await docker.containers.get(name)
            except aiodocker.exceptions.DockerError:
                raise ValueError(f"Container {name} not found")

            async for stat in container.stats(stream=False):
                cpu_delta = (
                    stat["cpu_stats"]["cpu_usage"]["total_usage"]
                    - stat["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_delta = (
                    stat["cpu_stats"]["system_cpu_usage"]
                    - stat["precpu_stats"]["system_cpu_usage"]
                )
                if system_delta <= 0:
                    return 0.0
                cpu_percent = (cpu_delta / system_delta) * len(
                    stat["cpu_stats"]["cpu_usage"].get("percpu_usage", [1])
                )
                return cpu_percent
            return 0.0
        finally:
            await docker.close()

    async def compose_scale(
        self, project: str, service: str, replicas: int, project_dir: str
    ) -> int:
        import asyncio
        import shlex

        cmd = (
            f"cd {shlex.quote(project_dir)} && "
            f"docker compose -p {shlex.quote(project)} "
            f"up -d --scale {shlex.quote(service)}={replicas}"
        )
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Compose scale failed: {stderr.decode()}")
        return proc.returncode

