from functools import wraps
from typing import Callable, Awaitable

from telegram import Update, InputFile
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from .config import Config
from .docker_client import DockerClient


def require_auth(cfg: Config):
    def decorator(func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable]):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chat_id = update.effective_chat.id if update.effective_chat else None
            if chat_id not in cfg.allowed_chat_ids:
                return
            return await func(update, context)

        return wrapper

    return decorator


def create_handlers(cfg: Config, docker: DockerClient):
    @require_auth(cfg)
    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "🐳 *Docker bot ready*\n\n"
            "Доступные команды:\n"
            "• 📋 `/list` — список контейнеров\n"
            "• 📜 `/logs <name>` — логи в файл\n"
            "• ▶️ `/startc <name>` — старт контейнера\n"
            "• ⏹ `/stopc <name>` — стоп контейнера\n"
            "• 🔁 `/restartc <name>` — рестарт контейнера\n"
            "• 🗑 `/rmc <name>` — удалить контейнер\n"
            "• 🧱 `/new <image> [name]` — создать контейнер\n"
            "• 📈 `/scale <n>` — масштабировать web‑сервис\n"
        )
        await update.message.reply_text(
            text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
        )

    @require_auth(cfg)
    async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        containers = await docker.list_containers(all_=True)
        lines: list[str] = []

        for c in containers:
            c_id = c._id[:12]
            raw_name = c._container.get("Names", [""])[0]
            name = raw_name.lstrip("/")
            status = c._container.get("Status", "")

            lower = status.lower()
            if "up" in lower:
                emoji = "🟢"
            elif "exited" in lower or "dead" in lower:
                emoji = "🔴"
            elif "created" in lower:
                emoji = "🟡"
            else:
                emoji = "⚪️"

            lines.append(f"{emoji} {name} — {status} ({c_id})")

        text = "\n".join(lines) if lines else "Нет контейнеров"

        await update.message.reply_text(f"Containers:\n{text}")

    @require_auth(cfg)
    async def logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /logs <container>")
            return

        name = context.args[0]
        path = f"/tmp/{name}_logs.txt"

        try:
            await docker.container_logs_to_file(name, path, tail=200)
        except ValueError as e:
            await update.message.reply_text(str(e))
            return

        with open(path, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename=f"{name}_logs.txt")
            )

    @require_auth(cfg)
    async def startc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /startc <container>")
            return

        ok = await docker.start_container(context.args[0])
        await update.message.reply_text("Started" if ok else "Container not found")

    @require_auth(cfg)
    async def stopc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /stopc <container>")
            return

        ok = await docker.stop_container(context.args[0])
        await update.message.reply_text("Stopped" if ok else "Container not found")

    @require_auth(cfg)
    async def restartc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /restartc <container>")
            return

        ok = await docker.restart_container(context.args[0])
        await update.message.reply_text("Restarted" if ok else "Container not found")

    @require_auth(cfg)
    async def rmc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /rmc <container>")
            return

        ok = await docker.remove_container(context.args[0], force=True)
        await update.message.reply_text("Removed" if ok else "Container not found")

    @require_auth(cfg)
    async def new_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /new <image> [name]")
            return

        image = context.args[0]
        name = context.args[1] if len(context.args) > 1 else None
        container = await docker.create_container(image=image, name=name)
        await update.message.reply_text(f"Created: {container._id[:12]}")

    @require_auth(cfg)
    async def scale_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /scale <replicas>")
            return

        replicas = int(context.args[0])

        await docker.compose_scale(
            cfg.compose_project,
            cfg.compose_service,
            replicas,
            cfg.compose_project_dir,
        )

        await update.message.reply_text(
            f"Scaled {cfg.compose_project}/{cfg.compose_service} to {replicas}"
        )

    return {
        "start": start_cmd,
        "list": list_cmd,
        "logs": logs_cmd,
        "startc": startc_cmd,
        "stopc": stopc_cmd,
        "restartc": restartc_cmd,
        "rmc": rmc_cmd,
        "new": new_cmd,
        "scale": scale_cmd,
    }


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"echo: {update.message.text}")


def register_handlers(app, cfg: Config, docker: DockerClient):
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

    app.add_handler(MessageHandler(filters.ALL, echo))

    return handlers

