"""
Utilidades para YouTube/yt-dlp
"""

import logging
import yt_dlp
import discord
import asyncio
from typing import Optional, Dict
from config import Config

log = logging.getLogger("youtube")


class YTDLSource(discord.PCMVolumeTransformer):
    """Fuente de audio extraída con yt-dlp"""

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")
        self.duration = data.get("duration")
        self.thumbnail = data.get("thumbnail")
        self.webpage_url = data.get("webpage_url")

    @classmethod
    def _get_audio_url(cls, data: dict) -> str:
        """Extrae la mejor URL de audio del diccionario de datos de yt-dlp"""
        if "url" in data:
            return data["url"]

        if "formats" in data:
            audio_only = [
                f
                for f in data["formats"]
                if f.get("acodec") != "none" and f.get("vcodec") == "none"
            ]
            if audio_only:
                audio_only.sort(key=lambda f: f.get("abr") or 0, reverse=True)
                return audio_only[0]["url"]

            with_audio = [f for f in data["formats"] if f.get("acodec") != "none"]
            if with_audio:
                return with_audio[0]["url"]

            return data["formats"][0]["url"]

        raise ValueError("No se pudo obtener URL de audio del resultado de yt-dlp")

    @classmethod
    async def from_url(cls, url: str, *, loop=None, stream=True):
        """Crea una fuente de audio FFmpeg a partir de una URL directa"""
        loop = loop or asyncio.get_event_loop()
        opts = {**Config.YDL_OPTIONS, "skip_download": True}

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(url, download=False)
                )

                if not data:
                    raise ValueError("yt-dlp no devolvió datos para la URL")

                if "entries" in data:
                    data = data["entries"][0]

                audio_url = cls._get_audio_url(data)

                return cls(
                    discord.FFmpegPCMAudio(
                        audio_url,
                        executable=Config.FFMPEG_PATH,
                        **Config.FFMPEG_OPTIONS,
                    ),
                    data=data,
                )
        except Exception as e:
            log.error(f"from_url falló ({url}): {e}")
            raise

    @classmethod
    async def search(cls, query: str, *, loop=None) -> Optional[Dict]:
        """
        Busca en YouTube y devuelve la información de la primera coincidencia.
        Primero intenta con cookies; si falla, reintenta sin ellas.
        """
        loop = loop or asyncio.get_event_loop()

        # Normalizar URLs de YouTube Music a YouTube estándar
        if "music.youtube.com" in query:
            query = query.replace("music.youtube.com", "www.youtube.com")
            if "&list=" in query:
                query = query.split("&list=")[0]

        opts = {**Config.YDL_OPTIONS, "skip_download": True, "extract_flat": False}

        result = await cls._do_search(query, opts, loop)
        if result:
            return result

        # Segunda oportunidad sin cookies
        log.info("Reintentando búsqueda sin cookies...")
        opts_no_cookies = {k: v for k, v in opts.items() if k != "cookiefile"}
        return await cls._do_search(query, opts_no_cookies, loop)

    @classmethod
    async def _do_search(cls, query: str, opts: dict, loop) -> Optional[Dict]:
        """Ejecuta la búsqueda con las opciones dadas"""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                search_query = (
                    query if query.startswith("http") else f"ytsearch:{query}"
                )

                data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(search_query, download=False)
                )

                if not data:
                    return None

                if "entries" in data:
                    entries = [e for e in data["entries"] if e]
                    return entries[0] if entries else None

                return data

        except Exception as e:
            log.error(f"Búsqueda falló ({query!r}): {e}")
            return None
