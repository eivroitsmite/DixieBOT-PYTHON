# DO NOT DELETE
# This bot has been made by Vanesa Smite (web: https://captaineivroit.com/)

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import sys
import datetime
import subprocess
from verification import Security

CREATOR_ID = 766005564190359552 

from dbconn import (
    create_table,
)
from dbconnMOD import (
     create_mod_log_table,
)

load_dotenv()

create_table()
create_mod_log_table()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if DISCORD_TOKEN is None:
    raise ValueError('Bot token not found. Please ensure the token variable is set correctly.')

VERSION = "1.0.0" 
LAST_UPDATED = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@bot.event
async def on_ready():
    print(f'Yo, It\'s me, {bot.user}')
    print(f'Bot restarted at {LAST_UPDATED} with version {VERSION}')
    
    for filename in os.listdir("./cogs"):
        if filename.endswith('.py') and filename != "Security.py":
            cog_name = filename[:-3]
            print(f"Cog : {cog_name} has been loaded")
            await bot.load_extension(f"cogs.{cog_name}")

    await bot.add_cog(Security(bot))

@bot.command()
async def restart(ctx):
    if ctx.author.id == CREATOR_ID:
        await ctx.send("Restarting bot...")
        subprocess.Popen([sys.executable] + sys.argv) 
        await bot.close() 
    else:
        await ctx.send("You don't have permission to restart the bot.")

@bot.command()
async def status(ctx):
    """Check the status of the bot."""
    await ctx.send(f"Bot Version: {VERSION}\nLast Updated: {LAST_UPDATED}\nCurrent Status: Online")

try:
    bot.run(DISCORD_TOKEN)
except discord.errors.LoginFailure as e:
    print(f"Failed to log in: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
