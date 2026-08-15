import os
import random
import string
import asyncio
import time
import discord
from discord.ext import commands, tasks
from discord import app_commands


TOKEN = os.getenv("DISCORD_TOKEN")

# =========================================================
# CONFIGURAÇÕES GERAIS
# =========================================================

GUILD_ID = 1513004124344680448

# Verificação
VERIFY_MESSAGE_ID = 1537619604031930459
MEMBER_ROLE_ID = 1522512158372401152
VERIFY_EMOJI = "🙏"

# Suporte
SUPPORT_CHANNEL_ID = 1537248179643359366
STAFF_ROLE_ID = 1522511412549783612

# Checker 4C
CHECKER_CHANNEL_ID = 1537261678071382056
POMELO_URL = "https://api.pomelo.lixqa.cc/v1/lookups"

# 6 segundos = abaixo do limite gratuito do Pomelo
CHECK_INTERVAL = 6

SUPPORT_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1537248179643359366/1537253420543639552/banner.jpg"
    "?ex=6a7fafd0&is=6a7e5e50&hm="
    "19f7828ddfa5908b95a06cccef462dedb4696c2fe6c502cb8a72dad511b7009f&"
)


# =========================================================
# BOT
# =========================================================

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

checked_names = set()
posted_names = set()


# =========================================================
# GERADOR 4C
# =========================================================

def generate_4c():
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(4))
# ==============================
# LOOP AUTOMÁTICO 4C
# ==============================

@tasks.loop(seconds=60)
async def four_character_checker():
    channel = bot.get_channel(CHECKER_CHANNEL_ID)

    if channel is None:
        print("❌ Canal do checker não encontrado")
        return

    username = generate_4c()

    if username in posted_names:
        return

    posted_names.add(username)

    if len(posted_names) > 10000:
        posted_names.clear()

    timestamp = int(time.time())

    message = (
        f"☁️ **²³ • 4C**\n"
        f"🔎 - **{username}** | 4C gerado para verificação\n"
        f"<t:{timestamp}:F> (<t:{timestamp}:R>)"
    )

    try:
        await channel.send(message)
        print(f"🔎 4C GERADO: {username}")

    except discord.HTTPException as error:
        print(f"⚠️ Falha temporária ao enviar 4C: {error}")

    except Exception as error:
        print(f"❌ Erro ao enviar 4C: {error}")


@four_character_checker.before_loop
async def before_checker():
    await bot.wait_until_ready()
# =========================================================
# FECHAR TICKET
# =========================================================

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_23"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        staff_role = interaction.guild.get_role(
            STAFF_ROLE_ID
        )

        is_staff = (
            staff_role in interaction.user.roles
            or interaction.user.guild_permissions.administrator
        )

        is_owner = (
            interaction.channel.topic
            == str(interaction.user.id)
        )

        if not is_staff and not is_owner:

            await interaction.response.send_message(
                "❌ Você não pode fechar este ticket.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🔒 Fechando atendimento...",
            ephemeral=True
        )

        await interaction.channel.delete(
            reason=f"Ticket fechado por {interaction.user}"
        )


# =========================================================
# MENU SUPORTE
# =========================================================

class SupportSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="Suporte",
                description="Precisa de ajuda com algo no servidor.",
                emoji="🎫",
                value="suporte"
            ),

            discord.SelectOption(
                label="Dúvida",
                description="Tire uma dúvida com nossa equipe.",
                emoji="❓",
                value="duvida"
            ),

            discord.SelectOption(
                label="Denúncia",
                description="Envie uma denúncia de forma privada.",
                emoji="🚨",
                value="denuncia"
            )

        ]

        super().__init__(
            placeholder="➡️ Clique aqui para ver as opções",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="support_select_23"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        staff_role = guild.get_role(
            STAFF_ROLE_ID
        )

        if staff_role is None:

            await interaction.response.send_message(
                "❌ Cargo da Staff não encontrado.",
                ephemeral=True
            )

            return

        # Evita mais de um ticket
        for channel in guild.text_channels:

            if channel.topic == str(
                interaction.user.id
            ):

                await interaction.response.send_message(
                    f"❌ Você já possui um atendimento aberto: "
                    f"{channel.mention}",
                    ephemeral=True
                )

                return

        support_channel = guild.get_channel(
            SUPPORT_CHANNEL_ID
        )

        category = (
            support_channel.category
            if support_channel
            else None
        )

        ticket_type = self.values[0]

        names = {
            "suporte": "suporte",
            "duvida": "duvida",
            "denuncia": "denuncia"
        }

        emojis = {
            "suporte": "🎫",
            "duvida": "❓",
            "denuncia": "🚨"
        }

        titles = {
            "suporte": "Suporte",
            "duvida": "Dúvida",
            "denuncia": "Denúncia"
        }

        safe_name = (
            interaction.user.name
            .lower()
            .replace(" ", "-")
        )

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                ),

            staff_role:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                ),

            guild.me:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )
        }

        ticket = await guild.create_text_channel(
            name=f"{names[ticket_type]}-{safe_name}",
            category=category,
            overwrites=overwrites,
            topic=str(interaction.user.id)
        )

        await interaction.response.send_message(
            f"✅ Atendimento criado: {ticket.mention}",
            ephemeral=True
        )

        embed = discord.Embed(
            title=(
                f"{emojis[ticket_type]} "
                f"{titles[ticket_type]} | 23"
            ),
            description=(
                f"Olá {interaction.user.mention}.\n\n"
                "Explique abaixo o motivo do seu atendimento.\n"
                f"A equipe {staff_role.mention} responderá "
                "assim que possível."
            ),
            color=0x5865F2
        )

        embed.set_footer(
            text="23 • Central de Atendimento"
        )

        await ticket.send(
            content=(
                f"{interaction.user.mention} "
                f"{staff_role.mention}"
            ),
            embed=embed,
            view=CloseTicketView()
        )


class SupportView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportSelect())


# =========================================================
# VERIFICAÇÃO
# =========================================================

@bot.event
async def on_raw_reaction_add(payload):

    if payload.user_id == bot.user.id:
        return

    if payload.guild_id != GUILD_ID:
        return

    if payload.message_id != VERIFY_MESSAGE_ID:
        return

    if str(payload.emoji) != VERIFY_EMOJI:
        return

    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        return

    role = guild.get_role(
        MEMBER_ROLE_ID
    )

    if role is None:
        return

    member = payload.member

    if member is None:

        try:

            member = await guild.fetch_member(
                payload.user_id
            )

        except discord.HTTPException:
            return

    try:

        await member.add_roles(
            role,
            reason="Verificação por reação 🙏"
        )

        print(
            f"✅ {member} foi verificado."
        )

    except Exception as error:

        print(
            f"❌ Erro verificação: {error}"
        )


# =========================================================
# SETUP SUPORTE
# =========================================================

@bot.tree.command(
    name="setup_suporte",
    description="Cria a Central de Atendimento",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def setup_suporte(
    interaction: discord.Interaction
):

    channel = interaction.guild.get_channel(
        SUPPORT_CHANNEL_ID
    )

    if channel is None:

        await interaction.response.send_message(
            "❌ Canal não encontrado.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="Central de Atendimento | 23",
        description=(
            "Após solicitar atendimento, por favor, aguarde "
            "que um membro da nossa equipe lhe responda.\n\n"

            "⚠️ O atendimento é realizado de forma privada, "
            "com acesso exclusivo da equipe.\n\n"

            "**Horários de Atendimento:**\n"
            "⏰ Segunda a Sexta: **13:00 às 22:00**\n"
            "⏰ Finais de Semana: **Horário indefinido**\n\n"

            "Clique no menu abaixo para continuar:"
        ),
        color=0x5865F2
    )

    embed.set_image(
        url=SUPPORT_IMAGE_URL
    )

    await channel.send(
        embed=embed,
        view=SupportView()
    )

    await interaction.response.send_message(
        "✅ Central criada.",
        ephemeral=True
    )


# =========================================================
# READY
# =========================================================
# =========================================================
# ☁️ CENTRAL ²³
# =========================================================

CENTRAL_CHANNEL_ID = 1538024768580620409
SQUAD_CHANNEL_ID = 1538185588430086244
EMOJI_VAGAS = "<:emoji_37:1538191545407381615>"
EMOJI_PROCURAR = "<:emoji_38:1538191582249877514>"
EMOJI_CRIAR = "<:emoji_39:1538191603624190144>"
EMOJI_SQUAD = "<:emoji_40:1538191651837837343>"
EMOJI_ENTRAR = "<:emoji_41:1538191684238577734>"
CENTRAL_BANNER_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1534219426591670456/1538027510778957934/IMG_4973.jpg"
    "?ex=6a812f3d&is=6a7fddbd&hm=07d3f65f2852679a61ce776874b8b06bcb3bf67db44e64f29286cff79766c884&"
)


class Central23View(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Suporte",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="central23_support"
    )
    async def suporte(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "🎫 Para receber atendimento, acesse o canal de **suporte** da ²³.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Squad",
        emoji="🎮",
        style=discord.ButtonStyle.secondary,
        custom_id="central23_squad"
    )
    async def squad(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "🎮 O sistema de **Procurar Squad** está chegando em breve.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Ranking",
        emoji="🏆",
        style=discord.ButtonStyle.secondary,
        custom_id="central23_ranking"
    )
    async def ranking(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "🏆 O **Ranking ²³** está chegando em breve.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Sugestão",
        emoji="💡",
        style=discord.ButtonStyle.secondary,
        custom_id="central23_suggestion"
    )
    async def sugestao(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "💡 O sistema de **sugestões** está chegando em breve.",
            ephemeral=True
        )


def create_central_embed(guild):

    total_members = guild.member_count or 0

    online_members = sum(
        1
        for member in guild.members
        if not member.bot
        and member.status != discord.Status.offline
    )

    boost_count = guild.premium_subscription_count or 0

    created_timestamp = int(guild.created_at.timestamp())

    embed = discord.Embed(
        title="☁️  ²³ • CENTRAL",
        description=(
            "Bem-vindo à central da **²³**.\n"
            "Tudo que você precisa, reunido em um só lugar.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 📊 Estatísticas da comunidade"
        ),
        color=0x74C0FC
    )

    embed.add_field(
        name="👥  MEMBROS",
        value=f"**{total_members:,}**".replace(",", "."),
        inline=True
    )

    embed.add_field(
        name="🟢  ONLINE",
        value=f"**{online_members:,}**".replace(",", "."),
        inline=True
    )

    embed.add_field(
        name="🚀  BOOSTS",
        value=f"**{boost_count}**",
        inline=True
    )

    embed.add_field(
        name="📅  NOSSA HISTÓRIA",
        value=f"Servidor criado <t:{created_timestamp}:R>",
        inline=False
    )

    embed.add_field(
        name="✨  ACESSO RÁPIDO",
        value=(
            "Use os botões abaixo para navegar pelos "
            "principais recursos da comunidade."
        ),
        inline=False
    )

    embed.set_image(url=CENTRAL_BANNER_URL)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.set_footer(
        text="²³ • nossa comunidade, nossa história."
    )

    return embed


async def send_central_panel():

    channel = bot.get_channel(CENTRAL_CHANNEL_ID)

    if channel is None:
        print("❌ Central ²³: canal não encontrado.")
        return

    guild = channel.guild

    try:
        embed = create_central_embed(guild)

        await channel.send(
            embed=embed,
            view=Central23View()
        )

        print("☁️ Central ²³ criada com sucesso.")

    except discord.HTTPException as error:
        print(f"⚠️ Erro do Discord ao criar Central ²³: {error}")

    except Exception as error:
        print(f"❌ Erro na Central ²³: {error}")

@bot.event
async def on_ready():
    bot.add_view(SupportView())
    bot.add_view(CloseTicketView())
    bot.add_view(Central23View())

    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    except Exception as error:
        print(f"❌ Sync: {error}")

    if not four_character_checker.is_running():
        four_character_checker.start()

    if not getattr(bot, "central_23_loaded", False):
        await send_central_panel()
        bot.central_23_loaded = True

    print(f"✅ /23 online como {bot.user}")

bot.run(TOKEN)
