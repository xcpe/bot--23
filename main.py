import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1513004124344680448
MESSAGE_ID = 1537619604031930459
MEMBER_ROLE_ID = 1522512158372401152
VERIFY_EMOJI = "🙏"

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ /23 online como {bot.user}")


@bot.event
async def on_raw_reaction_add(payload):
    # Ignora reações do próprio bot
    if payload.user_id == bot.user.id:
        return

    # Só funciona no servidor correto
    if payload.guild_id != GUILD_ID:
        return

    # Só funciona na mensagem de verificação
    if payload.message_id != MESSAGE_ID:
        return

    # Só aceita o emoji 🙏
    if str(payload.emoji) != VERIFY_EMOJI:
        return

    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("❌ Servidor não encontrado.")
        return

    role = guild.get_role(MEMBER_ROLE_ID)
    if role is None:
        print("❌ Cargo Member não encontrado.")
        return

    member = payload.member

    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except discord.HTTPException:
            return

    try:
        await member.add_roles(
            role,
            reason="Verificação por reação 🙏"
        )
        print(f"✅ {member} foi verificado e recebeu Member.")

    except discord.Forbidden:
        print("❌ O bot não tem permissão para dar o cargo Member.")

    except discord.HTTPException as erro:
        print(f"❌ Erro ao adicionar cargo: {erro}")


bot.run(TOKEN)
