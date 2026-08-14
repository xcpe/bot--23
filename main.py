import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# VERIFICAÇÃO
# =========================

GUILD_ID = 1513004124344680448
VERIFY_MESSAGE_ID = 1537619604031930459
MEMBER_ROLE_ID = 1522512158372401152
VERIFY_EMOJI = "🙏"

# =========================
# SUPORTE
# =========================

SUPPORT_CHANNEL_ID = 1537248179643359366
STAFF_ROLE_ID = 1522511412549783612


intents = discord.Intents.default()
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# BOTÃO DE FECHAR TICKET
# =========================

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
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

        if (
            staff_role not in interaction.user.roles
            and not interaction.user.guild_permissions.administrator
        ):
            # Também permite que o dono do ticket feche
            if interaction.channel.topic != str(interaction.user.id):
                await interaction.response.send_message(
                    "❌ Você não pode fechar este ticket.",
                    ephemeral=True
                )
                return

        await interaction.response.send_message(
            "🔒 Ticket sendo fechado...",
            ephemeral=True
        )

        await interaction.channel.delete(
            reason=f"Ticket fechado por {interaction.user}"
        )


# =========================
# BOTÃO DE ABRIR TICKET
# =========================

class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir suporte",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="open_ticket_23"
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ROLE_ID)

        if staff_role is None:
            await interaction.response.send_message(
                "❌ Cargo da Staff não encontrado.",
                ephemeral=True
            )
            return

        # Impede a pessoa de abrir vários tickets
        for channel in guild.text_channels:
            if channel.topic == str(interaction.user.id):
                await interaction.response.send_message(
                    f"❌ Você já possui um ticket aberto: {channel.mention}",
                    ephemeral=True
                )
                return

        support_channel = guild.get_channel(SUPPORT_CHANNEL_ID)

        # Cria o ticket na mesma categoria do canal de suporte
        category = support_channel.category if support_channel else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),

            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),

            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )
        }

        safe_name = interaction.user.name.lower().replace(" ", "-")

        ticket = await guild.create_text_channel(
            name=f"ticket-{safe_name}",
            category=category,
            overwrites=overwrites,
            topic=str(interaction.user.id),
            reason=f"Ticket aberto por {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ Seu ticket foi criado: {ticket.mention}",
            ephemeral=True
        )

        embed = discord.Embed(
            title="🎫 Suporte ²³",
            description=(
                f"Olá {interaction.user.mention}!\n\n"
                "Explique abaixo como podemos ajudar.\n"
                f"A equipe {staff_role.mention} responderá assim que possível."
            )
        )

        await ticket.send(
            content=f"{interaction.user.mention} {staff_role.mention}",
            embed=embed,
            view=CloseTicketView()
        )


# =========================
# QUANDO O BOT LIGAR
# =========================

@bot.event
async def on_ready():
    # Mantém os botões funcionando mesmo após reiniciar
    bot.add_view(SupportView())
    bot.add_view(CloseTicketView())

    try:
        guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild)
    except Exception as erro:
        print(f"Erro ao sincronizar comandos: {erro}")

    print(f"✅ /23 online como {bot.user}")


# =========================
# VERIFICAÇÃO 🙏
# =========================

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
    role = guild.get_role(MEMBER_ROLE_ID)

    if role is None:
        print("❌ Cargo Member não encontrado.")
        return

    member = payload.member

    if member is None:
        member = await guild.fetch_member(payload.user_id)

    try:
        await member.add_roles(
            role,
            reason="Verificação por reação 🙏"
        )

        print(f"✅ {member} foi verificado.")

    except discord.Forbidden:
        print("❌ Sem permissão para adicionar Member.")


# =========================
# COMANDO /setup-suporte
# =========================

@bot.tree.command(
    name="setup-suporte",
    description="Cria o painel para abertura de tickets",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_permissions(administrator=True)
async def setup_suporte(interaction: discord.Interaction):

    channel = interaction.guild.get_channel(SUPPORT_CHANNEL_ID)

    if channel is None:
        await interaction.response.send_message(
            "❌ Canal de suporte não encontrado.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🎫 Suporte ²³",
        description=(
            "Precisa de ajuda?\n\n"
            "Clique no botão abaixo para abrir um atendimento privado com nossa equipe."
        )
    )

    await channel.send(
        embed=embed,
        view=SupportView()
    )

    await interaction.response.send_message(
        f"✅ Painel de suporte criado em {channel.mention}.",
        ephemeral=True
    )


bot.run(TOKEN)
