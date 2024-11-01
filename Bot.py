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
import shodan
from discord import Embed
from json import JSONDecodeError
import ftplib


intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

init(autoreset=True)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


API_KEY = 'BREACHBASE_API_KEY'
TOKEN = 'BREACHBASE_TOKEN'
SHODAN_API_KEY = 'SHODAN_API_KEY'  
api = shodan.Shodan(SHODAN_API_KEY)
def clear_console():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

SHODAN_WEBCAM_QUERIES = [
    'http.title:"WV-SC385" has_screenshot:true',
    'http.favicon.hash:-1616143106 has_screenshot:true',
    'screenshot.label:webcam port:443',
    'title:"Camera" has_screenshot:true -ip:"122.128.4.106" -ip:"110.4.178.160"',
    'title:"axis" has_screenshot:true',
    'http.favicon.hash:999357577 has_screenshot:true',
    'title:"Live" has_screenshot:true',
    'title:"security" has_screenshot:true',
    '"google" has_screenshot:true',
    'title:"blue iris remote view" has_screenshot:true',
    'title:"ui3 -" has_screenshot:true',
    'title:"Network Camera VB-M600" has_screenshot:true',
    'product:"Yawcam webcam viewer httpd" has_screenshot:true',
    'title:"+tm01+" has_screenshot:true',
    'WVC80N has_screenshot:true'
]

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


async def make_request_with_retries(url, payload, headers, retries=3):
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    await asyncio.sleep(2)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed with error: {e}")
    return None

@bot.tree.command(name='search', description='Search for breaches by email, username, IP, phone, name, or password')
@commands.cooldown(1, 30, commands.BucketType.user)
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
    url = 'https://breachbase.com/api/frontend-search/'
    headers = {
        'Content-Type': 'application/json',
        'Cookie': f'token={TOKEN}'
    }
    payload = {
        'api_key': API_KEY,
        'type': search_type,
        'input': [query]
    }

    logging.debug(f"Making request to {url} with payload: {payload}")

    response_data = await make_request_with_retries(url, payload, headers)
    if not response_data:
        await interaction.followup.send("Error: Failed to retrieve data after multiple attempts.")
        return


    try:
        response_data = response.json()
        logging.debug(f"API Response Data: {response_data}")
    except ValueError as e:
        logging.error(f"Failed to parse JSON response: {e}")
        await interaction.response.send_message("Error: Failed to parse API response.")
        return

    if response_data.get('status') == 'success':
        view = PaginationView(response_data, search_type, query, API_KEY, TOKEN)
        embed, _ = view.get_embed_for_page(1)
        await interaction.followup.send(embed=embed, view=view)
    else:
        await interaction.followup.send(f"Error: {response_data.get('error', 'Unknown error occurred.')}")

@bot.tree.command(name='info', description='Displays information about the bot')
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔐 **ByteSecure Bot Information**",
        description=(
            "ByteSecure is a multifunctional bot designed to help users verify data breaches, "
            "retrieve random webcam feeds, and find FTP servers using Shodan. "
            "It's a powerful tool for security-focused individuals and researchers."
        ),
        color=discord.Color.dark_blue()
    )

    embed.add_field(
        name="📞 **Contact**",
        value="For support or inquiries, please reach out to **admin@bytelabs.site**",
        inline=False
    )
    embed.add_field(
        name="⚙️ **Version**",
        value="4.5.0",
        inline=False
    )
    embed.add_field(
        name="👨‍💻 **Developer**",
        value="ByteLabs Development Team",
        inline=False
    )

    embed.add_field(
        name="💻 **Available Commands**",
        value=(
            "Here are the core commands you can use with ByteSecure:\n"
            "• **`/search`** - 🔎 Search for breaches by email, username, IP, phone, name, or password.\n"
            "• **`/random_webcam`** - 🎥 Get a random webcam feed from Insecam or Shodan.\n"
            "• **`/random_ftp`** - 🖥️ Retrieve a random FTP server from Shodan.\n"
            "• **`/info`** - ℹ️ Display this bot information.\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🔒 **Breachbase API Integration**",
        value=(
            "The **`/search`** command allows you to check for data breaches across multiple platforms. "
            "You can search using:\n"
            "• Email 📧\n"
            "• Username 👤\n"
            "• IP Address 🌐\n"
            "• Phone Number 📱\n"
            "• Name 📝\n"
            "• Password 🔑"
        ),
        inline=False
    )

    embed.add_field(
        name="🌍 **Shodan Integration**",
        value=(
            "**`/random_webcam`**: Find random webcam feeds indexed by Shodan and Insecam, including live screenshots when available.\n\n"
            "**`/random_ftp`**: Retrieve random FTP server details from Shodan, including:\n"
            "• IP Address 🌐\n"
            "• Banner Information 💻\n"
            "• Port 🔌 (Port 21 by default)\n"
            "• Country 🏳️ (with country flag)"
        ),
        inline=False
    )

    embed.set_footer(text="Thank you for using ByteSecure! 🔐")

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
@commands.cooldown(1, 30, commands.BucketType.user)
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
            webcam_query = random.choice(SHODAN_WEBCAM_QUERIES)
            max_pages = 20

            async with aiohttp.ClientSession() as session:
                shodan_url = f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query={webcam_query}&page=1"
                try:
                    async with session.get(shodan_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                            except JSONDecodeError as json_err:
                                logging.error(f"Failed to parse JSON: {json_err}")
                                raw_response = await response.text()
                                logging.error(f"Raw Response: {raw_response}")
                                await interaction.followup.send(f"Failed to fetch webcam data due to a JSON parsing error.", ephemeral=True)
                                return

                            if 'matches' not in data or not data['matches']:
                                await interaction.followup.send("No webcams found matching the query.", ephemeral=True)
                                return

                            random_result = random.choice(data['matches'])

                            ip_address = random_result.get("ip_str", "Unknown")
                            banner_info = random_result.get("data", "Unknown")
                            country = random_result.get("location", {}).get("country_name", "Unknown")
                            country_code = random_result.get("location", {}).get("country_code", "Unknown")
                            latitude = random_result.get("location", {}).get("latitude", "Unknown")
                            longitude = random_result.get("location", {}).get("longitude", "Unknown")
                            port = random_result.get("port", 80)

                            embed = Embed(title="🎥 Random Webcam Found (Shodan)!", color=discord.Color.green())
                            embed.add_field(name="🔗 IP Address", value=ip_address, inline=False)
                            embed.add_field(name="💻 Banner Info", value=f"```{banner_info}```", inline=False)
                            embed.add_field(name="🔌 Port", value=str(port), inline=False)
                            embed.add_field(name="🌍 Country", value=f":flag_{country_code.lower()}: {country}", inline=False)
                            embed.add_field(name="📌 Latitude/Longitude", value=f"{latitude}, {longitude}", inline=False)

                            webcam_url = f"http://{ip_address}:{port}"
                            embed.add_field(name="🌐 Live Webcam", value=f"[Click here to view live feed]({webcam_url})", inline=False)

                            if 'screenshot' in random_result:
                                screenshot_data = random_result['screenshot'].get('data', None)
                                if screenshot_data:
                                    screenshot_bytes = base64.b64decode(screenshot_data)
                                    screenshot_file = BytesIO(screenshot_bytes)
                                    discord_file = File(screenshot_file, filename="webcam_screenshot.jpg")

                                    embed.set_image(url="attachment://webcam_screenshot.jpg")
                                    await interaction.followup.send(embed=embed, file=discord_file)
                                else:
                                    await interaction.followup.send(embed=embed)
                            else:
                                await interaction.followup.send(embed=embed)
                        else:
                            await interaction.followup.send(f"Shodan API Error: {response.status}", ephemeral=True)
                            return
                except aiohttp.ClientError as e:
                    logging.error(f"Shodan API request failed: {e}")
                    await interaction.followup.send(f"Failed to fetch webcam data due to a network error: {e}", ephemeral=True)

    except Exception as e:
        logging.error(f"Error in random_webcam: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

class FTPLoginView(View):
    def __init__(self, ip_address, port):
        super().__init__()
        self.ip_address = ip_address
        self.port = port

    @discord.ui.button(label="🔐 Login as Anonymous", style=discord.ButtonStyle.success, emoji="🔑")
    async def login_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()  
        attempt_limit = 3
        for attempt in range(attempt_limit):
            try:
                with ftplib.FTP() as ftp:
                    ftp.connect(self.ip_address, self.port, timeout=10)
                    ftp.login()  

                    try:
                        directory_listing = ftp.nlst()
                        if not directory_listing:
                            directory_message = "No files or directories found."
                        else:
                            directory_message = "\n".join(directory_listing[:10])
                            if len(directory_listing) > 10:
                                directory_message += f"\n...and {len(directory_listing) - 10} more items."

                        embed = discord.Embed(
                            title=f"📂 Directory Structure of `{self.ip_address}:{self.port}`",
                            description=f"Here are the files and directories at the root level:\n```{directory_message}```",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="💡 Info", value="Listing limited to the first 10 items.", inline=False)
                        embed.set_footer(text="FTP Directory Structure - Logged in as anonymous")

                        await interaction.followup.send(embed=embed)  
                        return  

                    except ftplib.error_perm as e:
                        logging.warning(f"FTP Permission error: {e}")
                        await interaction.followup.send(f"❌ Permission denied on `{self.ip_address}:{self.port}`.", ephemeral=True)
                        return  

            except ftplib.all_errors as e:
                error_message = f"Attempt {attempt + 1}/{attempt_limit} failed to access FTP server at `{self.ip_address}:{self.port}`. Error: {e}"
                logging.error(error_message)
                if attempt < attempt_limit - 1:
                    await asyncio.sleep(2)  
                else:

                    if not interaction.response.is_done():
                        await interaction.followup.send(f"❌ Failed to log into FTP server after {attempt_limit} attempts.", ephemeral=True)
                    return

@bot.tree.command(name='random_ftp', description='Get a random FTP server from Shodan!')
@commands.cooldown(1, 30, commands.BucketType.user)
async def random_ftp(interaction: discord.Interaction):
    await interaction.response.defer()
    FTP_QUERY = '"logged in" "220" port:21'
    retries = 3
    max_pages = 20

    async def fetch_ftp_results(session, query, page):
        shodan_url = f"https://api.shodan.io/shodan/host/search?key={SHODAN_API_KEY}&query={query}&page={page}"
        try:
            async with session.get(shodan_url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 500:
                    logging.error(f"Shodan API returned a 500 error for page {page}.")
                    return None
                else:
                    logging.error(f"Shodan API Error: {response.status} for page {page}")
                    return None
        except aiohttp.ClientError as e:
            logging.error(f"Request failed: {e}")
            return None

    async with aiohttp.ClientSession() as session:
        for attempt in range(retries):
            data = await fetch_ftp_results(session, FTP_QUERY, page=1)
            if data and 'total' in data:
                total_results = data['total']
                total_pages = min((total_results // 100) + 1, max_pages)
                random_page = random.randint(1, total_pages)
                data = await fetch_ftp_results(session, FTP_QUERY, random_page)
                if data and 'matches' in data and data['matches']:
                    random_result = random.choice(data['matches'])
                    ip_address = random_result.get("ip_str", "Unknown")
                    banner_info = random_result.get("data", "Unknown")
                    country = random_result.get("location", {}).get("country_name", "Unknown")
                    country_code = random_result.get("location", {}).get("country_code", "Unknown")
                    port = 21

                    embed = Embed(title="🖥️ Random FTP Server Found", color=discord.Color.blue())
                    embed.add_field(name="🔗 IP Address", value=ip_address, inline=False)
                    embed.add_field(name="💻 Banner Info", value=f"```{banner_info}```", inline=False)
                    embed.add_field(name="🔌 Port", value=str(port), inline=False)
                    embed.add_field(name="🌍 Country", value=f":flag_{country_code.lower()}: {country}", inline=False)

                    view = FTPLoginView(ip_address, port)
                    embed.set_footer(text="Powered by Shodan")
                    await interaction.followup.send(embed=embed, view=view)
                    return
                elif data is None:
                    logging.warning(f"Failed to fetch FTP results on attempt {attempt + 1}/{retries}. Retrying...")
                    continue 

        await interaction.followup.send("No FTP servers found or an error occurred while fetching data. Please try again later.", ephemeral=True)

class CVEPaginationView(View):
    def __init__(self, cves, title, query, items_per_page=3):
        super().__init__(timeout=180)
        self.cves = cves
        self.title = title
        self.query = query
        self.page = 0
        self.items_per_page = items_per_page

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        self.page -= 1
        await self.update_embed(interaction)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.page += 1
        await self.update_embed(interaction)

    async def update_embed(self, interaction):
        embed = self.get_embed_for_page()
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= (len(self.cves) - 1) // self.items_per_page
        await interaction.response.edit_message(embed=embed, view=self)

    def get_embed_for_page(self):
        start_index = self.page * self.items_per_page
        end_index = start_index + self.items_per_page
        page_items = self.cves[start_index:end_index]

        embed = discord.Embed(
            title=f"{self.title}",
            description=f"Results for `{self.query}` (Page {self.page + 1}/{(len(self.cves) - 1) // self.items_per_page + 1})",
            color=discord.Color.blue()
        )

        for cve in page_items:
            cve_id = cve.get("cve_id", "N/A")
            summary = cve.get("summary", "No summary available.")
            cvss_score = cve.get("cvss", "N/A")
            kev_status = "Yes" if cve.get("kev", False) else "No"
            propose_action = cve.get("propose_action", "None provided.")
            ransomware_campaign = cve.get("ransomware_campaign", "None reported.")
            published_time = cve.get("published_time", "N/A")
            references = cve.get("references", [])
            reference_links = "\n".join(references[:2])  

            embed.add_field(
                name=f"CVE ID: {cve_id}",
                value=(
                    f"**Summary**: {summary[:250]}...\n"  
                    f"**CVSS Score**: {cvss_score}\n"
                    f"**KEV Status**: {kev_status}\n"
                    f"**Proposed Action**: {propose_action}\n"
                    f"**Ransomware Campaign**: {ransomware_campaign}\n"
                    f"**Published**: {published_time}\n"
                    f"**References**: {reference_links or 'None'}"
                ),
                inline=False
            )

        embed.set_footer(text="Data sourced from CVE API")
        embed.timestamp = discord.utils.utcnow()
        return embed


@bot.tree.command(name='cve_lookup', description='Look up CVE information based on a product query')
@app_commands.describe(
    query='The product name to search for CVEs (e.g., "wordpress")',
    is_kev='Filter for Known Exploited Vulnerabilities (optional)',
    sort_by_epss='Sort results by EPSS score (optional)'
)
async def cve_lookup(
    interaction: discord.Interaction,
    query: str,
    is_kev: bool = False,
    sort_by_epss: bool = False
):
    await interaction.response.defer()

    url = "https://cvedb.shodan.io/cves"
    params = {
        'product': query,
        'count': 'false',
        'is_kev': 'true' if is_kev else 'false',
        'sort_by_epss': 'true' if sort_by_epss else 'false',
        'skip': 0,
        'limit': 1000  
    }
    headers = {
        'accept': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                cves = data.get('cves', [])

                if not cves:
                    await interaction.followup.send(f"No CVEs found for the specified query: `{query}`.")
                    return

                view = CVEPaginationView(cves, "CVE Lookup Results", query)
                embed = view.get_embed_for_page()
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send("Error: Failed to retrieve CVE data from the API.")

bot.run('DISCORD_TOKEN')
