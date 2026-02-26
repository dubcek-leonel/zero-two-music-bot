import asyncio
import discord


async def test():
    intents = discord.Intents.default()
    intents.voice_states = True
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        print(f"Conectado como {bot.user}")
        # Pon aquí el ID de tu canal de voz
        channel = bot.get_channel(TU_CHANNEL_ID_AQUI)
        if channel:
            try:
                vc = await channel.connect(timeout=30)
                print("✅ Conexión de voz exitosa!")
                await vc.disconnect()
            except Exception as e:
                print(f"❌ Error: {e!r}")
        await bot.close()

    await bot.start("TU_TOKEN_AQUI")


asyncio.run(test())
