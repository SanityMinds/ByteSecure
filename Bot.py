import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
from discord.ui import Button, View
import time
import os
import sys
from colorama import init, Fore

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

init(autoreset=True)

API_KEY = 'YOUR_API_KEY_HERE'
TOKEN = 'YOUR_TOKEN_HERE'

def clear_console():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

@bot.event
async def on_ready():
    clear_console()
    print("ByteSecure is loading", end="")
    for _ in range(3):
        print(".", end="", flush=True)
        time.sleep(1)
    print("\n")

    print(Fore.BLUE + "developed by")
    print(Fore.BLUE + """
      ____        _       _       _         
     |  _ \      | |     | |     | |        
     | |_) |_   _| |_ ___| | __ _| |__  ___ 
     |  _ <| | | | __/ _ \ |/ _` | '_ \/ __|
     | |_) | |_| | ||  __/ | (_| | |_) \__ \
     |____/ \__, |\__\___|_|\__,_|_.__/|___/
             __/ |                          
            |___/                           
    """)
    print(Fore.BLUE + f'Logged in as {bot.user.name}')
    await bot.tree.sync()

class PaginationView(View):
    def __init__(self, data, search_type, query, api_key, token):
        super().__init__()
        self.data = data
        self.search_type = search_type
        self.query = query
        self.page = 1
        self.api_key = api_key
        self.token = token

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: Button):
        if self.page > 1:
            self.page -= 1
            await self.send_new_page(interaction)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: Button):
        self.page += 1
        await self.send_new_page(interaction)

    async def send_new_page(self, interaction: discord.Interaction):
        embed, content_available = self.get_embed_for_page(self.page)
        if content_available:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.page -= 1
            await interaction.response.send_message('No more data available.', ephemeral=True)

    def get_embed_for_page(self, page):
        start_index = (page - 1) * 5
        end_index = start_index + 5
        content = self.data['content'][start_index:end_index]

        if not content:
            return None, False

        embed_color = discord.Color.blue() if self.search_type == 'email' else discord.Color.green()
        embed = discord.Embed(title=f"Search Results: {self.search_type.capitalize()} Query",
                              description=f"**Query**: `{self.query}`\n**Page**: {self.page}",
                              color=embed_color)

        for item in content:
            username = item.get('username', 'N/A')
            email = item.get('email', 'N/A')
            password = item.get('password', 'N/A')
            origin = item.get('origin', 'N/A')
            ip = item.get('ip', None)
            phone = item.get('phone', None)
            name = item.get('name', None)

            value_text = f"**Email**: `{email}`\n**Password**: `{password}`\n**Origin**: `{origin}`"
            if ip:
                value_text += f"\n**IP**: `{ip}`"
            if phone:
                value_text += f"\n**Phone**: `{phone}`"
            if name:
                value_text += f"\n**Name**: `{name}`"

            embed.add_field(name=f"Username: `{username}`", value=value_text, inline=False)
        
        embed.set_footer(text="Data fetched from Breachbase API")
        embed.timestamp = discord.utils.utcnow()
        
        return embed, True

@bot.tree.command(name='search', description='Search for breaches by email, username, IP, phone, name, or password')
@app_commands.describe(
    search_type='The type of search you want to perform',
    query='Your search query, e.g., bob@mail.com'
)
@app_commands.choices(search_type=[
    app_commands.Choice(name="Email", value="email"),
    app_commands.Choice(name="Username", value="username"),
    app_commands.Choice(name="IP", value="ip"),
    app_commands.Choice(name="Phone", value="phone"),
    app_commands.Choice(name="Name", value="name"),
    app_commands.Choice(name="Password", value="password"),
])
async def search(interaction: discord.Interaction, search_type: str, query: str):
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'token={TOKEN}'
    }
    payload = {
        'api_key': API_KEY,
        'type': search_type,
        'input': [query]
    }
    response = requests.post('https://breachbase.com/api/frontend-search/', json=payload, headers=headers)
    response_data = response.json()

    if response_data['status'] == 'success':
        view = PaginationView(response_data, search_type, query, API_KEY, TOKEN)
        embed, _ = view.get_embed_for_page(1)
        await interaction.response.send_message(embed=embed, view=view)
    else:
        error_message = response_data.get('error', 'Unknown error occurred.')
        await interaction.response.send_message(f"Error: {error_message}")

@bot.tree.command(name='info', description='Displays information about the bot')
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ByteSecure Bot Information",
        description="ByteSecure is a dedicated bot designed to help users check for data breaches.",
        color=discord.Color.dark_blue()
    )
    embed.add_field(name="Contact", value="admin@bytelabs.site", inline=False)
    embed.add_field(name="Version", value="1.0.0", inline=False)
    embed.add_field(name="Developer", value="ByteLabs Development Team", inline=False)
    embed.add_field(name="Commands", value="/search - Search for breaches\n/info - Get bot info", inline=False)
    embed.add_field(name="Encrypted Data", value="Some data may be encrypted such as Passwords. This is because some databreaches contain encrypted passwords not stored in plain text.", inline=False)
    embed.set_footer(text="Thank you for using ByteSecure!")

    await interaction.response.send_message(embed=embed)

bot.run('YOUR_DISCORD_BOT_TOKEN_HERE')
