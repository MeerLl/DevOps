import logging

from telegram.ext import ApplicationBuilder, CommandHandler

from .config import Config
from .docker_client import DockerClient
from .handlers import create_handlers
from .monitor import Autoscaler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def main() -> None:
    cfg = Config.from_env()
    docker = DockerClient()

    async def _async_setup() -> tuple:
        app = ApplicationBuilder().token(cfg.telegram_token).build()

        handlers = create_handlers(cfg, docker)
        app.add_handler(CommandHandler("start", handlers["start"]))
        app.add_handler(CommandHandler("list", handlers["list"]))
        app.add_handler(CommandHandler("logs", handlers["logs"]))
        app.add_handler(CommandHandler("startc", handlers["startc"]))
        app.add_handler(CommandHandler("stopc", handlers["stopc"]))
        app.add_handler(CommandHandler("restartc", handlers["restartc"]))
        app.add_handler(CommandHandler("rmc", handlers["rmc"]))
        app.add_handler(CommandHandler("new", handlers["new"]))
        app.add_handler(CommandHandler("scale", handlers["scale"]))

        async def notify(msg: str):
            for chat_id in cfg.allowed_chat_ids:
                await app.bot.send_message(chat_id=chat_id, text=msg)

        autoscaler = Autoscaler(cfg, docker, notify)
        autoscaler.start()
        return app, autoscaler

    import asyncio
    app, autoscaler = asyncio.run(_async_setup())

    log.info("Starting bot with run_polling")
    try:
        app.run_polling()
    finally:
        log.info("Stopping autoscaler")
        asyncio.run(autoscaler.stop())


if __name__ == "__main__":
    main()

