import discord
from discord.ext import commands
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os


_connection = None

def create_connection():
    global _connection
    if _connection and _connection.is_connected():
        return _connection
    try:
        _connection = mysql.connector.connect(
            host=os.getenv('MOD_HOST'),
            port=os.getenv('MOD_PORT'),
            user=os.getenv('MOD_USER'),
            password=os.getenv('MOD_PASSWORD'),
            database=os.getenv('MOD_DATABASE')
        )
        return _connection
    except Error as e:
        print("Error connecting to database:", e)
        return None

def add_mod_log(user_id, reason, moderator_id, action_type):
    """Adds a new moderation log to the 'mod_logs' table."""
    connection = create_connection()
    if connection is None:
        print("No connection to database. Cannot insert log.")
        return False
    try:
        cursor = connection.cursor()
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')  # Get current UTC timestamp
        insert_query = """
        INSERT INTO mod_logs (user_id, reason, moderator_id, action_type, timestamp)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (user_id, reason, moderator_id, action_type, timestamp))
        connection.commit()
        print(f"Log added for user {user_id} with action_type {action_type}.")
        return True
    except Error as e:
        print(f"Error inserting moderation log: {e}")
        return False
    finally:
        cursor.close()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def warn(ctx, user: discord.User, *, reason: str):
    """Adds a warning for a user."""
    # Log the warning to the database
    result = add_mod_log(user.id, reason, ctx.author.id, "minor_warning")
    
    if result:
        await ctx.send(f"User {user.mention} has been warned for: {reason}")
    else:
        await ctx.send("Failed to log the warning.")

@bot.command()
async def majorwarn(ctx, user: discord.User, *, reason: str):
    """Adds a major warning for a user."""
    # Log the major warning to the database
    result = add_mod_log(user.id, reason, ctx.author.id, "major_warning")
    
    if result:
        await ctx.send(f"User {user.mention} has been majorly warned for: {reason}")
    else:
        await ctx.send("Failed to log the major warning.")

# Run the bot
bot.run('MTMxMDk3MDI1MjQ0NzcxMTM0Mw.GIMoPt.HekvBc1hriUoE_hxQSV79xSpvQVSNhNAVzSOnc')
