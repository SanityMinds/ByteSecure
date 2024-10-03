# ByteSecure Discord Bot

ByteSecure is a Discord bot designed to utilize the Breachbase API for retrieving data breach information directly within Discord environments. This bot integrates features that allow users to search for breaches by email, username, IP, phone, name, or password.

## Features

- **Search Functionality**: Allows users to search for breach data associated with different identifiers like email, username, IP, and more.
- **Dynamic Embeds**: Presents search results in a dynamic, paginated format using Discord embeds.
- **API Utilization**: Leverages the unofficial Breachbase API endpoint for consistent data retrieval.

## API Usage

The bot utilizes an alternative API endpoint (`frontend-search`) provided by Breachbase as the official API has seen no updates and the main project is no longer maintained actively. The API documentation for the standard endpoints is available [here](https://breachbase.com/apidocs), but these may not function correctly.

### Obtaining API Key and Token

To use the bot, you'll need an API key and a token:

- **API Key**: Obtain this by creating an account on [Breachbase.com](https://breachbase.com). The key is available within your account dashboard.
- **API Token**: Access this through your browser's inspect element tool:
  - Navigate to "Storage"
  - Go to "Cookies"
  - Find the "token" item stored there.

![Breachbase Token Retrieval](https://i.imgur.com/GNT5FZI.png)

### Endpoint Information

Currently, the only working API endpoint is `frontend-search`. This endpoint provides access to the database via the interface that Breachbase uses for its web version.

### Known Glitch for Unlimited Searches

There is a known glitch in the Breachbase system that allows for unlimited API searches:
- Purchase a Lifetime plan.
- Then purchase a VIP plan.
- After 30 days, cancel the VIP subscription to avoid further charges.

This method exploits a glitch where the user benefits from unlimited searches while retaining the Lifetime plan features. It is crucial to note that this can be quite costly, and exploiting such glitches may have unforeseen repercussions.


## Random webcam feature

The bot has a /random_webcam command
You can get random webcams from around the world using Shodan & insecam!

Insecam is a free website where you can see webcams from around the world. The bot uses beautifulsoup to scrape the information for the user. 
Shodan is a free/paid API you can use to find unsecured webcams

## Bot Installation

To invite the bot that utilizes this code and is operational 24/7, use the following link to add it to your server: [Invite ByteSecure](https://discord.com/oauth2/authorize?client_id=1116086186172219473&permissions=0&scope=bot).

To install the bot locally you have to have python3 installed and then run the command:

pip install discord.py requests colorama aiohttp beautifulsoup4 lxml

replace the token with your own 
replace the shodan key with your own and follow the steps above for 'breachbase'
