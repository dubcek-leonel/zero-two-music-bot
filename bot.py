import os
import sys
import asyncio
import logging
import warnings

# CRÍTICO: Configurar asyncio ANTES de cualquier otro import en Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")

# ── Logging ──────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)
log = logging.getLogger("bot")
# ─────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from config import Config


def load_opus():
    if discord.opus.is_loaded():
        return True

    candidates = [
        os.path.join(os.getcwd(), "opus.dll"),
        "opus.dll",
        "opus",
        "libopus-0.dll",
        "libopus.dll",
    ]

    for name in candidates:
        try:
            discord.opus.load_opus(name)
            if discord.opus.is_loaded():
                log.info(f"Opus cargado: {name}")
                return True
        except Exception:
            continue

    log.warning("Opus no cargado — el audio de voz puede no funcionar")
    return False


load_opus()


class FlaviBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True

        super().__init__(
            command_prefix=Config.PREFIX, intents=intents, help_command=None
        )

    async def setup_hook(self):
        log.info("Configurando bot...")
        await self.load_cogs()

    async def load_cogs(self):
        cogs_loaded = 0
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    log.info(f"  Cog cargado: {filename[:-3]}")
                    cogs_loaded += 1
                except Exception as e:
                    log.error(f"  Error cargando {filename}: {e}")
        log.info(f"Cogs cargados: {cogs_loaded}")

    async def on_ready(self):
        log.info(
            f"Bot listo: {self.user} | Prefix: {Config.PREFIX} | Opus: {discord.opus.is_loaded()}"
        )
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=f"{Config.PREFIX}help"
            )
        )

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"{Config.EMOJI_ERROR} Te falta: `{error.param.name}`")
            return
        log.error(f"Error en comando '{ctx.command}': {error}")


async def main():
    bot = FlaviBot()
    try:
        await bot.start(Config.TOKEN)
    except KeyboardInterrupt:
        pass
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
