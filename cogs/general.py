"""
Cog de comandos generales
"""

import discord
from discord.ext import commands
import time
from config import Config


class General(commands.Cog):
    """Comandos generales del bot"""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Muestra la latencia del bot"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latencia: **{latency}ms**",
            color=Config.COLOR_INFO,
        )
        await ctx.send(embed=embed)

    @commands.command(name="info", aliases=["about", "botinfo"])
    async def info(self, ctx):
        """Información sobre el bot"""
        uptime = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title=f"{Config.EMOJI_MUSIC} ZERO_Two - Bot de Música",
            description="Bot de música profesional para Discord",
            color=Config.COLOR_MUSIC,
        )
        embed.add_field(
            name="📊 Estadísticas",
            value=f"```\nServidores: {len(self.bot.guilds)}\nUsuarios: {len(self.bot.users)}\nComandos: {len(self.bot.commands)}\n```",
            inline=True,
        )
        embed.add_field(
            name="⏰ Uptime",
            value=f"```\n{hours}h {minutes}m {seconds}s\n```",
            inline=True,
        )
        embed.add_field(
            name="🔧 Versión",
            value=f"```\ndiscord.py {discord.__version__}\n```",
            inline=True,
        )
        embed.set_footer(text=f"Prefix: {Config.PREFIX}")
        await ctx.send(embed=embed)

    @commands.command(name="help", aliases=["ayuda", "comandos"])
    async def help_command(self, ctx):
        """Muestra todos los comandos disponibles"""
        embed = discord.Embed(
            title=f"{Config.EMOJI_MUSIC} Comandos de Zero Two",
            description=f"Usa `{Config.PREFIX}` antes de cada comando",
            color=Config.COLOR_INFO,
        )
        embed.add_field(
            name="📌 General",
            value=f"```\n{Config.PREFIX}ping\n{Config.PREFIX}info\n{Config.PREFIX}help\n```",
            inline=False,
        )
        embed.add_field(
            name="🎵 Reproducción",
            value=f"```\n{Config.PREFIX}play <canción>\n{Config.PREFIX}pause\n{Config.PREFIX}resume\n{Config.PREFIX}skip\n{Config.PREFIX}stop\n```",
            inline=False,
        )
        embed.add_field(
            name="📜 Cola",
            value=f"```\n{Config.PREFIX}queue\n{Config.PREFIX}nowplaying\n{Config.PREFIX}shuffle\n{Config.PREFIX}remove <pos>\n{Config.PREFIX}clear\n```",
            inline=False,
        )
        embed.add_field(
            name="⚙️ Configuración",
            value=f"```\n{Config.PREFIX}volume <0-100>\n{Config.PREFIX}loop\n{Config.PREFIX}loopqueue\n{Config.PREFIX}join\n{Config.PREFIX}leave\n```",
            inline=False,
        )
        embed.set_footer(text="Zero Two v1.0")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
