from re import L
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta
import sys, traceback

from verification import Security


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

warnings = {}

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if DISCORD_TOKEN is None:
    raise ValueError('Bot token not found. Please ensure the token variable is set correctly.')

@bot.event
async def on_ready():
    print(f'Yo, It\'s me, {bot.user}')
    
    for filename in os.listdir("./cogs"):
        if(filename.endswith('.py')): 
            print("Cog : " + filename[:-3] + " has been loaded")
            await bot.load_extension(f"cogs.{filename[:-3]}")
            await bot.add_cog(Security(bot))
            
    

try:
    bot.run(DISCORD_TOKEN)
except discord.errors.LoginFailure as e:
    print(f"Failed to log in: {e}")
except Exception as e:
    print(f"An error occurred: {e}")