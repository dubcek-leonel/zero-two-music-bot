"""
Cog de comandos de música
"""

import logging
import discord
from discord.ext import commands
import asyncio
from config import Config
from utils.music_queue import MusicQueue, Song
from utils.youtube import YTDLSource

log = logging.getLogger("music")


class Music(commands.Cog):
    """Comandos de música del bot"""

    def __init__(self, bot):
        self.bot = bot
        self.queues: dict[int, MusicQueue] = {}
        self.connecting: set[int] = set()

    # ──────────────────────────────────────────
    # MÉTODOS INTERNOS
    # ──────────────────────────────────────────

    def get_queue(self, ctx) -> MusicQueue:
        """Obtiene (o crea) la cola del servidor"""
        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = MusicQueue()
        return self.queues[ctx.guild.id]

    async def _connect(self, ctx) -> bool:
        """Conecta el bot al canal de voz del autor."""
        if not ctx.author.voice:
            await ctx.send(f"{Config.EMOJI_ERROR} Debes estar en un canal de voz")
            return False

        channel = ctx.author.voice.channel
        guild_id = ctx.guild.id

        log.info(
            f"_connect: intentando conectar a {channel.name}, voice_client={ctx.voice_client}"
        )

        try:
            if ctx.voice_client and ctx.voice_client.is_connected():
                if ctx.voice_client.channel == channel:
                    log.info("_connect: ya en el mismo canal, retornando True")
                    return True
                await ctx.voice_client.move_to(channel)
            else:
                # Si hay un voice_client zombie, desconectarlo primero
                if ctx.voice_client:
                    try:
                        await ctx.voice_client.disconnect(force=True)
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)

                self.connecting.add(guild_id)
                await channel.connect(timeout=Config.CONNECT_TIMEOUT, reconnect=True)
                self.connecting.discard(guild_id)
                await asyncio.sleep(Config.CONNECT_SLEEP)

            return True
        except Exception as e:
            self.connecting.discard(guild_id)
            log.error(f"Error al conectar en {ctx.guild.name}: {e!r}")
            await ctx.send(f"{Config.EMOJI_ERROR} No pude conectarme al canal")
            return False

    async def play_next(self, ctx):
        """Reproduce la siguiente canción de la cola"""
        queue = self.get_queue(ctx)

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            log.info("play_next: bot no conectado, abortando")
            queue.current = None
            return

        # Cola vacía → esperar y desconectar por inactividad
        if queue.is_empty() and not queue.current:
            await asyncio.sleep(Config.INACTIVITY_TIMEOUT)
            if (
                queue.is_empty()
                and ctx.voice_client
                and ctx.voice_client.is_connected()
                and not ctx.voice_client.is_playing()
            ):
                await ctx.send(
                    f"{Config.EMOJI_INFO} Cola vacía. Desconectando por inactividad..."
                )
                await ctx.voice_client.disconnect()
            return

        next_song = queue.next()
        if not next_song:
            return

        try:
            source = await YTDLSource.from_url(
                next_song.url, loop=self.bot.loop, stream=True
            )

            def after_playing(error):
                if error:
                    log.error(f"after_playing: {error}")
                # Limpiar current para que el siguiente play_next funcione bien
                queue.current = next_song  # mantener hasta que inicie el siguiente
                if ctx.voice_client and ctx.voice_client.is_connected():
                    fut = asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx), self.bot.loop
                    )
                    try:
                        fut.result(timeout=15)
                    except Exception as e:
                        log.error(f"after_playing fut.result: {e}")

            if not ctx.voice_client or not ctx.voice_client.is_connected():
                log.info("Conexión perdida antes de reproducir")
                return

            ctx.voice_client.play(source, after=after_playing)

            embed = discord.Embed(
                title=f"{Config.EMOJI_PLAY} Reproduciendo",
                description=f"**[{next_song.title}]({next_song.webpage_url})**",
                color=Config.COLOR_MUSIC,
            )
            embed.add_field(
                name="Duración", value=next_song.format_duration(), inline=True
            )
            embed.add_field(
                name="Solicitado por", value=next_song.requester.mention, inline=True
            )
            if next_song.thumbnail:
                embed.set_thumbnail(url=next_song.thumbnail)
            await ctx.send(embed=embed)

        except discord.errors.ClientException as e:
            if "Not connected to voice" in str(e):
                await ctx.send(
                    f"{Config.EMOJI_ERROR} Me desconectaron del canal. Usa `!join`."
                )
            else:
                log.error(f"ClientException en play_next: {e}")
            queue.current = None
        except Exception as e:
            log.error(f"play_next error: {e}")
            await ctx.send(f"{Config.EMOJI_ERROR} Error al reproducir, saltando...")
            queue.current = None
            await asyncio.sleep(1)
            await self.play_next(ctx)

    # ──────────────────────────────────────────
    # COMANDOS DE CONEXIÓN
    # ──────────────────────────────────────────

    @commands.command(name="join", aliases=["connect"])
    async def join(self, ctx):
        """Conecta el bot a tu canal de voz"""
        if not ctx.author.voice:
            await ctx.send(f"{Config.EMOJI_ERROR} Debes estar en un canal de voz")
            return

        if await self._connect(ctx):
            await ctx.send(
                f"{Config.EMOJI_SUCCESS} Conectado a **{ctx.author.voice.channel.name}**"
            )

    @commands.command(name="leave", aliases=["disconnect", "dc"])
    async def leave(self, ctx):
        """Desconecta el bot del canal de voz"""
        if not ctx.voice_client:
            await ctx.send(f"{Config.EMOJI_ERROR} No estoy en un canal de voz")
            return

        self.get_queue(ctx).clear()
        await ctx.voice_client.disconnect()
        await ctx.send(f"{Config.EMOJI_SUCCESS} Desconectado del canal de voz")

    # ──────────────────────────────────────────
    # COMANDOS DE REPRODUCCIÓN
    # ──────────────────────────────────────────

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str):
        """Busca y reproduce una canción de YouTube"""
        if not ctx.author.voice:
            await ctx.send(f"{Config.EMOJI_ERROR} Debes estar en un canal de voz")
            return

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            if not await self._connect(ctx):
                return

        search_msg = await ctx.send(f"{Config.EMOJI_LOADING} Buscando: **{search}**...")

        data = await YTDLSource.search(search, loop=self.bot.loop)

        if not data:
            await search_msg.edit(
                content=f"{Config.EMOJI_ERROR} No se encontró: **{search}**"
            )
            return

        song = Song(
            {
                "url": data.get("url") or data.get("webpage_url"),
                "title": data.get("title", "Sin título"),
                "duration": data.get("duration", 0),
                "thumbnail": data.get("thumbnail"),
                "webpage_url": data.get("webpage_url"),
                "requester": ctx.author,
            }
        )

        queue = self.get_queue(ctx)
        position = queue.add(song)

        # Si no hay nada reproduciéndose Y no hay canción actual → reproducir
        if (
            not ctx.voice_client.is_playing()
            and not ctx.voice_client.is_paused()
            and not queue.current
        ):
            await search_msg.delete()
            await self.play_next(ctx)
        else:
            embed = discord.Embed(
                title=f"{Config.EMOJI_QUEUE} Agregado a la cola",
                description=f"**[{song.title}]({song.webpage_url})**",
                color=Config.COLOR_INFO,
            )
            embed.add_field(name="Posición", value=f"#{position}", inline=True)
            embed.add_field(name="Duración", value=song.format_duration(), inline=True)
            if song.thumbnail:
                embed.set_thumbnail(url=song.thumbnail)
            await search_msg.edit(content=None, embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pausa la reproducción"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(f"{Config.EMOJI_PAUSE} Música pausada")
        else:
            await ctx.send(f"{Config.EMOJI_ERROR} No hay nada reproduciéndose")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Reanuda la reproducción"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(f"{Config.EMOJI_PLAY} Música reanudada")
        else:
            await ctx.send(f"{Config.EMOJI_ERROR} La música no está pausada")

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        """Salta la canción actual (ignora el modo loop)"""
        if not ctx.voice_client or (
            not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused()
        ):
            await ctx.send(f"{Config.EMOJI_ERROR} No hay nada reproduciéndose")
            return

        queue = self.get_queue(ctx)
        queue.loop = False  # ignorar loop al saltar
        ctx.voice_client.stop()
        await ctx.send(f"{Config.EMOJI_SKIP} Canción saltada")

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Detiene la reproducción, limpia la cola y desconecta"""
        self.get_queue(ctx).clear()
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send(f"{Config.EMOJI_STOP} Reproducción detenida y cola limpiada")

    # ──────────────────────────────────────────
    # COMANDOS DE COLA
    # ──────────────────────────────────────────

    @commands.command(name="queue", aliases=["q"])
    async def queue_command(self, ctx):
        """Muestra la cola de reproducción"""
        queue = self.get_queue(ctx)

        if not queue.current and queue.is_empty():
            await ctx.send(f"{Config.EMOJI_ERROR} La cola está vacía")
            return

        embed = discord.Embed(
            title=f"{Config.EMOJI_QUEUE} Cola de Reproducción", color=Config.COLOR_MUSIC
        )

        if queue.current:
            embed.add_field(
                name="🎵 Reproduciendo Ahora",
                value=(
                    f"**[{queue.current.title}]({queue.current.webpage_url})**\n"
                    f"Duración: {queue.current.format_duration()} | "
                    f"Solicitado por: {queue.current.requester.mention}"
                ),
                inline=False,
            )

        if not queue.is_empty():
            songs_list = queue.get_queue()
            lines = [
                f"`{i+1}.` **{s.title}** ({s.format_duration()})"
                for i, s in enumerate(songs_list[:10])
            ]
            embed.add_field(
                name=f"📜 Próximas {min(len(songs_list), 10)} canciones",
                value="\n".join(lines),
                inline=False,
            )
            if len(songs_list) > 10:
                embed.set_footer(text=f"Y {len(songs_list) - 10} canciones más...")

        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx):
        """Muestra la canción que se está reproduciendo"""
        queue = self.get_queue(ctx)
        if not queue.current:
            await ctx.send(f"{Config.EMOJI_ERROR} No hay nada reproduciéndose")
            return

        s = queue.current
        embed = discord.Embed(
            title=f"{Config.EMOJI_MUSIC} Reproduciendo Ahora",
            description=f"**[{s.title}]({s.webpage_url})**",
            color=Config.COLOR_MUSIC,
        )
        embed.add_field(name="Duración", value=s.format_duration(), inline=True)
        embed.add_field(name="Solicitado por", value=s.requester.mention, inline=True)
        if s.thumbnail:
            embed.set_thumbnail(url=s.thumbnail)
        await ctx.send(embed=embed)

    # ──────────────────────────────────────────
    # COMANDOS AVANZADOS
    # ──────────────────────────────────────────

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx, vol: int = None):
        """Ajusta el volumen (0-100). Sin argumento muestra el actual."""
        if not ctx.voice_client:
            await ctx.send(f"{Config.EMOJI_ERROR} No estoy en un canal de voz")
            return

        if vol is None:
            current = (
                int(ctx.voice_client.source.volume * 100)
                if ctx.voice_client.source
                else int(Config.DEFAULT_VOLUME * 100)
            )
            await ctx.send(f"🔊 Volumen actual: **{current}%**")
            return

        if not 0 <= vol <= 100:
            await ctx.send(f"{Config.EMOJI_ERROR} El volumen debe estar entre 0 y 100")
            return

        if ctx.voice_client.source:
            ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"🔊 Volumen ajustado a **{vol}%**")

    @commands.command(name="loop", aliases=["repeat"])
    async def loop_cmd(self, ctx):
        """Activa/desactiva el loop de la canción actual"""
        queue = self.get_queue(ctx)
        queue.loop = not queue.loop
        estado = "activado 🔁" if queue.loop else "desactivado"
        await ctx.send(f"Loop {estado}")

    @commands.command(name="loopqueue", aliases=["lq"])
    async def loopqueue(self, ctx):
        """Activa/desactiva el loop de toda la cola"""
        queue = self.get_queue(ctx)
        queue.loop_queue = not queue.loop_queue
        estado = "activado 🔁" if queue.loop_queue else "desactivado"
        await ctx.send(f"Loop de cola {estado}")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        """Mezcla aleatoriamente la cola"""
        queue = self.get_queue(ctx)
        if queue.is_empty():
            await ctx.send(f"{Config.EMOJI_ERROR} La cola está vacía")
            return
        count = queue.shuffle()
        await ctx.send(f"🔀 Cola mezclada — **{count}** canciones")

    @commands.command(name="remove", aliases=["rm"])
    async def remove(self, ctx, index: int):
        """Elimina una canción de la cola por su posición"""
        queue = self.get_queue(ctx)
        if queue.is_empty():
            await ctx.send(f"{Config.EMOJI_ERROR} La cola está vacía")
            return
        if index < 1 or index > len(queue):
            await ctx.send(
                f"{Config.EMOJI_ERROR} Posición inválida. La cola tiene {len(queue)} canciones"
            )
            return
        removed = queue.get_queue()[index - 1]
        queue.remove(index - 1)
        await ctx.send(f"{Config.EMOJI_SUCCESS} Removido: **{removed.title}**")

    @commands.command(name="clear", aliases=["clean"])
    async def clear(self, ctx):
        """Limpia las canciones pendientes sin detener la reproducción actual"""
        queue = self.get_queue(ctx)
        if queue.is_empty():
            await ctx.send(f"{Config.EMOJI_ERROR} La cola ya está vacía")
            return
        count = queue.clear_queue_only()
        await ctx.send(
            f"{Config.EMOJI_SUCCESS} Cola limpiada — **{count}** canciones removidas"
        )

    # ──────────────────────────────────────────
    # EVENTOS
    # ──────────────────────────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Limpia la cola cuando el bot se desconecta del canal de voz"""
        if member.id != self.bot.user.id:
            return

        guild_id = member.guild.id

        if after.channel is not None:
            self.connecting.discard(guild_id)
            return

        if before.channel and not after.channel:
            if guild_id in self.connecting:
                log.info(f"Reconexión en curso en {member.guild.name}, ignorando")
                self.connecting.discard(guild_id)
                return
            queue = self.queues.get(guild_id)
            if queue:
                queue.clear()
            log.info(f"Bot desconectado de {member.guild.name}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Libera la cola al ser expulsado de un servidor"""
        self.queues.pop(guild.id, None)
        self.connecting.discard(guild.id)
        log.info(f"Cola liberada para servidor eliminado: {guild.name}")


async def setup(bot):
    await bot.add_cog(Music(bot))
