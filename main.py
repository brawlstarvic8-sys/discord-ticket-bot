# main.py
import discord
from discord import app_commands
from discord.ui import Button, Select, View
import os
from dotenv import load_dotenv
from datetime import timedelta
import discord.utils

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


TICKET_CATEGORY_ID = None  # Put the categorie id here or let none
SUPPORT_ROLE_ID = 123456789012345678  # put the staff id here

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", description="Need help?", emoji="❓", value="general"),
            discord.SelectOption(label="Report a Player", description="Report a member", emoji="⚠️", value="report"),
            discord.SelectOption(label="Payment Issue", description="Store or purchase problem", emoji="💰", value="payment"),
            discord.SelectOption(label="Other", description="Something else", emoji="📩", value="other"),
        ]
        super().__init__(
            placeholder="Select a ticket type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select"  
        )

    async def callback(self, interaction: discord.Interaction):
        category = bot.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None

        everyone = interaction.guild.default_role
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        if SUPPORT_ROLE_ID:
            support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}-{interaction.user.discriminator}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket by {interaction.user} | Type: {self.values[0]}"
        )

        embed = discord.Embed(
            title="Ticket Created!",
            description=f"Thank you {interaction.user.mention}! The staff will assist you shortly.",
            color=discord.Color.green()
        )
        view = CloseView()
        mention = f"<@&{SUPPORT_ROLE_ID}>" if SUPPORT_ROLE_ID else None
        await channel.send(embed=embed, content=mention, view=view)

        await interaction.response.send_message(f"Your ticket has been created: {channel.mention}", ephemeral=True)

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="Ticket Closed",
            description=f"Closed by {interaction.user.mention}",
            color=discord.Color.orange()
        )
        await interaction.channel.send(embed=embed)

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        # Supprime le salon après 10 secondes
        await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=10))
        await interaction.channel.delete()

class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎟️", custom_id="create_ticket_button")
    async def open_ticket_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Please select a ticket type from the menu below.", ephemeral=True)

@tree.command(name="setup", description="Set up the ticket panel (admin only)")
@app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎟️ Ticket System",
        description="Click the button or select a category to open a ticket.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Support Team")

    view = TicketPanelView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("Ticket panel successfully set up!", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"{bot.user} is online and ready!")
    print(f"Synced {len(tree.get_commands())} slash commands")

# Rendre les vues persistantes (boutons fonctionnent même après redémarrage)
async def setup_hook():
    bot.add_view(TicketPanelView())
    bot.add_view(CloseView())

bot.setup_hook = setup_hook

# Lancement du bot
if __name__ == "__main__":
    token = os.getenv("TOKEN") or "YOUR_BOT_TOKEN_HERE"  # Remplace ou utilise .env
    bot.run(token)