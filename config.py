"""
Configuración centralizada del bot
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración principal del bot"""

    # Discord
    TOKEN = os.getenv("DISCORD_TOKEN")
    PREFIX = os.getenv("PREFIX", "!")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))

    # FFmpeg — usa el binario local en Windows, el del sistema en Linux/Mac
    FFMPEG_PATH = os.getenv(
        "FFMPEG_PATH",
        "./ffmpeg.exe" if sys.platform == "win32" else "ffmpeg",
    )

    # Archivos externos
    COOKIES_PATH = os.getenv("COOKIES_PATH", "./cookies.txt")

    # Música
    MAX_QUEUE_SIZE = 100
    DEFAULT_VOLUME = 0.5
    INACTIVITY_TIMEOUT = 300  # segundos antes de desconectar por inactividad

    # Conexión de voz
    CONNECT_TIMEOUT = 60.0  # bajar de 60
    CONNECT_SLEEP = 2.0  # subir un poco

    # YouTube / yt-dlp
    YDL_OPTIONS = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "source_address": "0.0.0.0",
        "cookiefile": COOKIES_PATH,
        "geo_bypass": True,
        "age_limit": None,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }

    # FFmpeg — opciones estables para streaming de voz
    FFMPEG_OPTIONS = {
        "before_options": (
            "-reconnect 1 "
            "-reconnect_streamed 1 "
            "-reconnect_delay_max 5 "
            "-nostdin"
        ),
        "options": "-vn -bufsize 64k",
    }

    # Colores para embeds
    COLOR_SUCCESS = 0x2ECC71
    COLOR_ERROR = 0xE74C3C
    COLOR_INFO = 0x3498DB
    COLOR_WARNING = 0xF39C12
    COLOR_MUSIC = 0x9B59B6

    # Emojis
    EMOJI_PLAY = "▶️"
    EMOJI_PAUSE = "⏸️"
    EMOJI_STOP = "⏹️"
    EMOJI_SKIP = "⏭️"
    EMOJI_QUEUE = "📜"
    EMOJI_MUSIC = "🎵"
    EMOJI_SUCCESS = "✅"
    EMOJI_ERROR = "❌"
    EMOJI_LOADING = "⏳"
    EMOJI_INFO = "ℹ️"


# ── Validaciones al iniciar ──────────────────────────────────
if not Config.TOKEN:
    raise ValueError("❌ DISCORD_TOKEN no encontrado en .env")

if Config.OWNER_ID == 0:
    print("⚠️ OWNER_ID no configurado.")

if not os.path.exists(Config.FFMPEG_PATH):
    print(f"⚠️ FFmpeg no encontrado en: {Config.FFMPEG_PATH}")

if not os.path.exists(Config.COOKIES_PATH):
    print(f"⚠️ cookies.txt no encontrado en: {Config.COOKIES_PATH}")
