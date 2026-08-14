import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1513004124344680448
MESSAGE_ID = 1537607625166823564
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
    if payload.user_id == bot.user.id:
        return

    if payload.guild_id != GUILD_ID:
        return

    if payload.message_id != MESSAGE_ID:
        return

    if str(payload.emoji) != VERIFY_EMOJI:
        return

    guild = bot.get_guild(GUILD_ID)
    if guild is None:
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
        print(f"✅ {member} foi verificado!")

    except discord.Forbidden:
        print("❌ Sem permissão para adicionar o cargo Member.")

    except discord.HTTPException as erro:
        print(f"❌ Erro: {erro}")

bot.run(TOKEN)
