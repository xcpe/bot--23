import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# CONFIGURAÇÕES
# =========================

GUILD_ID = 1513004124344680448

# Verificação
VERIFY_MESSAGE_ID = 1537619604031930459
MEMBER_ROLE_ID = 1522512158372401152
VERIFY_EMOJI = "🙏"

# Suporte
SUPPORT_CHANNEL_ID = 1537248179643359366
STAFF_ROLE_ID = 1522511412549783612

# Imagem da embed
SUPPORT_IMAGE_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1537248179643359366/1537253420543639552/banner.jpg"
    "?ex=6a7fafd0&is=6a7e5e50&hm="
    "19f7828ddfa5908b95a06cccef462dedb4696c2fe6c502cb8a72dad511b7009f&"
)

intents = discord.Intents.default()
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# FECHAR TICKET
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

        is_staff = (
            staff_role in interaction.user.roles
            or interaction.user.guild_permissions.administrator
        )

        is_owner = interaction.channel.topic == str(interaction.user.id)

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


# =========================
# MENU DO SUPORTE
# =========================

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

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ROLE_ID)

        if staff_role is None:
            await interaction.response.send_message(
                "❌ Cargo da Staff não encontrado.",
                ephemeral=True
            )
            return

        # Impede múltiplos tickets
        for channel in guild.text_channels:
            if channel.topic == str(interaction.user.id):
                await interaction.response.send_message(
                    f"❌ Você já possui um atendimento aberto: {channel.mention}",
                    ephemeral=True
                )
                return

        support_channel = guild.get_channel(SUPPORT_CHANNEL_ID)
        category = support_channel.category if support_channel else None

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

        safe_name = interaction.user.name.lower().replace(" ", "-")

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

        ticket = await guild.create_text_channel(
            name=f"{names[ticket_type]}-{safe_name}",
            category=category,
            overwrites=overwrites,
            topic=str(interaction.user.id),
            reason=f"{titles[ticket_type]} aberto por {interaction.user}"
        )

        await interaction.response.send_message(
            f"✅ Atendimento criado: {ticket.mention}",
            ephemeral=True
        )

        ticket_embed = discord.Embed(
            title=f"{emojis[ticket_type]} {titles[ticket_type]} | 23",
            description=(
                f"Olá {interaction.user.mention}.\n\n"
                "Explique abaixo o motivo do seu atendimento.\n"
                f"A equipe {staff_role.mention} responderá assim que possível."
            ),
            color=0x5865F2
        )

        ticket_embed.set_footer(
            text="23 • Central de Atendimento"
        )

        await ticket.send(
            content=f"{interaction.user.mention} {staff_role.mention}",
            embed=ticket_embed,
            view=CloseTicketView()
        )


class SupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportSelect())


# =========================
# BOT ONLINE
# =========================

@bot.event
async def on_ready():
    bot.add_view(SupportView())
    bot.add_view(CloseTicketView())

    try:
        guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=guild)
    except Exception as erro:
        print(f"❌ Erro ao sincronizar comandos: {erro}")

    print(f"✅ /23 online como {bot.user}")


# =========================
# VERIFICAÇÃO
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

        print(f"✅ {member} foi verificado.")

    except discord.Forbidden:
        print("❌ Sem permissão para adicionar Member.")

    except discord.HTTPException as erro:
        print(f"❌ Erro: {erro}")


# =========================
# /setup_suporte
# =========================

@bot.tree.command(
    name="setup_suporte",
    description="Cria a Central de Atendimento",
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
        title="Central de Atendimento | 23",
        description=(
            "Após solicitar atendimento, por favor, aguarde que "
            "um membro da nossa equipe lhe responda.\n\n"

            "⚠️ O atendimento é realizado de forma privada, com "
            "acesso exclusivo da equipe.\n\n"

            "**Horários de Atendimento:**\n"
            "⏰ Segunda a Sexta: **13:00 às 22:00**\n"
            "⏰ Finais de Semana: **Horário indefinido**\n\n"

            "Clique no menu abaixo para continuar:"
        ),
        color=0x5865F2
    )

    embed.set_image(url=SUPPORT_IMAGE_URL)

    await channel.send(
        embed=embed,
        view=SupportView()
    )

    await interaction.response.send_message(
        f"✅ Central de Atendimento criada em {channel.mention}.",
        ephemeral=True
    )


bot.run(TOKEN)
