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
import base64
import random
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from collections import deque
import logging
import base64
from io import BytesIO
from discord import File


intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

init(autoreset=True)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = 'BREACHBASE_API_KEY'
TOKEN = 'BREACHBASE_TOKEN'
SHODAN_API_KEY = 'SHODAN_TOKEN'

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
    print(Fore.BLUE + r"""
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

async def get_random_webcam_url():
    random_page = random.randint(1, 585)
    url = f"http://www.insecam.org/en/byrating/?page={random_page}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            logging.debug(f"Response status: {response.status}")
            if response.status != 200:
                logging.error(f"Failed to retrieve the webpage, status code: {response.status}")
                return None
            html = await response.text()
            logging.debug(f"Page HTML content length: {len(html)}")
            soup = BeautifulSoup(html, "html.parser")

            webcam_links = soup.find_all("a", href=True)
            logging.debug(f"Found {len(webcam_links)} links on the page.")
            webcam_urls = [f"http://www.insecam.org{link['href']}" for link in webcam_links if '/view/' in link['href']]
            logging.debug(f"Filtered {len(webcam_urls)} valid webcam URLs.")

            if not webcam_urls:
                logging.warning("No webcam URLs found.")
                return None

            return random.choice(webcam_urls)

async def get_random_webcam_from_shodan():

    queries = [
        'http.title:"WV-SC385" has_screenshot:true',
        'http.favicon.hash:-1616143106 has_screenshot:true'
    ]


    chosen_query = random.choice(queries)


    if chosen_query == 'http.title:"WV-SC385" has_screenshot:true':
        random_page = random.randint(1, 2)
    else:

        random_page = random.randint(1, 25)


    shodan_url = f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query={chosen_query}&page={random_page}"

    try:
        response = requests.get(shodan_url)
        

        if response.status_code == 500:
            logging.error(f"Shodan API returned a 500 error. Query: {chosen_query}, Page: {random_page}")

            if chosen_query == 'http.title:"WV-SC385" has_screenshot:true' and random_page == 2:
                logging.info("Falling back to page 1 for 'WV-SC385' query.")
                fallback_url = f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query={chosen_query}&page=1"
                response = requests.get(fallback_url)
                if response.status_code == 500:
                    logging.error("Fallback to page 1 failed as well.")
                    return None
            else:
                return None

        data = response.json()

        if 'matches' not in data:
            logging.error(f"Shodan API response does not contain 'matches'. Query: {chosen_query}, Page: {random_page}")
            return None

        if data['matches']:
            random_result = random.choice(data['matches'])

            latitude = random_result.get("location", {}).get("latitude", "Unknown")
            longitude = random_result.get("location", {}).get("longitude", "Unknown")
            country = random_result.get("location", {}).get("country_name", "Unknown")
            country_code = random_result.get("location", {}).get("country_code", "Unknown")
            city = random_result.get("location", {}).get("city", "Unknown")
            ip_address = random_result.get("ip_str", "Unknown")
            port = random_result.get("port", 80)
            screenshot_data = random_result.get("screenshot", {}).get("data", None)

            webcam_url = f"http://{ip_address}:{port}"

            return {
                "latitude": latitude,
                "longitude": longitude,
                "country": country,
                "country_code": country_code,
                "city": city,
                "ip_address": ip_address,
                "port": port,
                "webcam_url": webcam_url,
                "screenshot_data": screenshot_data
            }
        else:
            logging.error("No matches found in the response from Shodan.")
            return None
    except Exception as e:
        logging.error(f"Shodan API error: {e}")
        return None

async def get_insecam_image_url(webcam_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(webcam_url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                meta_tag = soup.find("meta", property="og:image")
                if meta_tag:
                    return meta_tag["content"]

                img_tag = soup.find("img", {"id": "image0"})
                if img_tag:
                    return img_tag["src"]

            return None

@bot.tree.command(name='random_webcam', description='Get a random webcam from either Insecam or Shodan!')
@app_commands.choices(source=[
    app_commands.Choice(name="Insecam", value="insecam"),
    app_commands.Choice(name="Shodan", value="shodan")
])
async def random_webcam(interaction: discord.Interaction, source: str):
    await interaction.response.defer()

    try:
        if source == "insecam":
            webcam_url = await get_random_webcam_url()
            if webcam_url:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                }
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(webcam_url) as response:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")

                        camera_details = soup.find_all("div", class_="camera-details__row")

                        def extract_detail(label):
                            for row in camera_details:
                                if label in row.text:
                                    return row.find_all("div")[1].text.strip()
                            return "Unknown"

                        country = extract_detail("Country:")
                        country_code = extract_detail("Country code:")
                        region = extract_detail("Region:")
                        city = extract_detail("City:")
                        latitude = extract_detail("Latitude:")
                        longitude = extract_detail("Longitude:")
                        zip_code = extract_detail("ZIP:")
                        timezone = extract_detail("Timezone:")
                        manufacturer = extract_detail("Manufacturer:")

                        img_url = await get_insecam_image_url(webcam_url)
                        ip_address = img_url 

                        embed = discord.Embed(title="🎥 Random Webcam Found (Insecam)!", color=discord.Color.blue())
                        embed.add_field(name="🔗 IP Address", value=ip_address, inline=False)
                        embed.add_field(name="🌐 Insecam Link", value=webcam_url, inline=False)
                        embed.add_field(name="🌍 Country", value=f":flag_{country_code.lower()}: {country}", inline=False)
                        embed.add_field(name="📍 City", value=city, inline=False)
                        embed.add_field(name="🗺️ Region", value=region, inline=False)
                        embed.add_field(name="📌 Latitude/Longitude", value=f"{latitude}, {longitude}", inline=False)
                        embed.add_field(name="📬 ZIP", value=zip_code, inline=False)
                        embed.add_field(name="🕒 Timezone", value=timezone, inline=False)
                        embed.add_field(name="📷 Manufacturer", value=manufacturer, inline=False)

                        if img_url:
                            embed.set_image(url=img_url)

                        embed.set_footer(text="Powered by Insecam")
                        await interaction.followup.send(embed=embed)
                        return

        elif source == "shodan":
            shodan_webcam = await get_random_webcam_from_shodan()
            if shodan_webcam:
                embed = discord.Embed(title="🎥 Random Webcam Found (Shodan)!", color=discord.Color.green())
                embed.add_field(name="🔗 IP Address", value=shodan_webcam['ip_address'], inline=False)
                embed.add_field(name="🌍 Country", value=f":flag_{shodan_webcam['country_code'].lower()}: {shodan_webcam['country']}", inline=False)
                embed.add_field(name="📍 City", value=shodan_webcam['city'], inline=False)
                embed.add_field(name="📌 Latitude/Longitude", value=f"{shodan_webcam['latitude']}, {shodan_webcam['longitude']}", inline=False)
                
                embed.add_field(name="🌐 Live Webcam", value=f"[Click here to view live feed]({shodan_webcam['webcam_url']})", inline=False)

                if shodan_webcam['screenshot_data']:
                    screenshot_bytes = base64.b64decode(shodan_webcam['screenshot_data'])
                    screenshot_file = BytesIO(screenshot_bytes)
                    discord_file = discord.File(screenshot_file, filename="webcam_screenshot.jpg")

                    embed.set_image(url="attachment://webcam_screenshot.jpg")

                    await interaction.followup.send(embed=embed, file=discord_file)
                else:
                    await interaction.followup.send(embed=embed)

                return

        await interaction.followup.send("Could not fetch a random webcam at this time. Please try again later.", ephemeral=True)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

#replace with your token
bot.run('TOKEN')
