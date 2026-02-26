"""
Cog de comandos de administración
"""
import discord
from discord.ext import commands
from config import Config

class Admin(commands.Cog):
    """Comandos de administración del bot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='reload')
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        """Recargar un cog (solo owner)"""
        try:
            await self.bot.reload_extension(f'cogs.{cog}')
            embed = discord.Embed(
                description=f"{Config.EMOJI_SUCCESS} Cog `{cog}` recargado",
                color=Config.COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                description=f"{Config.EMOJI_ERROR} Error: `{e}`",
                color=Config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='shutdown')
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Apagar el bot (solo owner)"""
        embed = discord.Embed(
            description=f"{Config.EMOJI_SUCCESS} Apagando bot...",
            color=Config.COLOR_INFO
        )
        await ctx.send(embed=embed)
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))