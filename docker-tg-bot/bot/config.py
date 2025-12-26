import os
from dataclasses import dataclass

@dataclass
class Config:
    telegram_token: str
    allowed_chat_ids: list[int]

    autoscale_interval: int = 30  # seconds
    cpu_threshold: float = 0.7    # 70% CPU
    max_replicas: int = 5
    min_replicas: int = 1

    compose_project: str = "tg-scale-lab"
    compose_service: str = "web"
    compose_project_dir: str = "/tg-scale-lab"

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("TELEGRAM_TOKEN", "")
        if not token:
            raise RuntimeError("TELEGRAM_TOKEN is required")

        chat_ids_raw = os.environ.get("TELEGRAM_ALLOWED_CHATS", "")
        allowed_ids = [int(x) for x in chat_ids_raw.split(",") if x.strip()]
        if not allowed_ids:
            raise RuntimeError("TELEGRAM_ALLOWED_CHATS is required")

        return cls(
            telegram_token=token,
            allowed_chat_ids=allowed_ids,
            autoscale_interval=int(os.environ.get("AUTOSCALE_INTERVAL", "30")),
            cpu_threshold=float(os.environ.get("CPU_THRESHOLD", "0.7")),
            max_replicas=int(os.environ.get("MAX_REPLICAS", "5")),
            min_replicas=int(os.environ.get("MIN_REPLICAS", "1")),
            compose_project=os.environ.get("COMPOSE_PROJECT", "tg-scale-lab"),
            compose_service=os.environ.get("COMPOSE_SERVICE", "web"),
            compose_project_dir=os.environ.get("COMPOSE_PROJECT_DIR", "/tg-scale-lab"),
        )

