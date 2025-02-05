import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import string

# Configuration constants
REQUIRED_ROLE_ID = 1243576135481294859  
UNVERIFIED_ROLE_ID = 1305172270486126663 
WELCOME_CHANNEL_ID = 1305164254797893703  
NOTICE_CHANNEL_ID = 1305164254797893703 
NOTICE_MESSAGE = "You must get the 'Verified' role within 48 hours by sending the password I just DMed you in this chat."

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)

from dbconn import (
    add_user,
    get_user_by_id,
    get_password_by_user_id,
    get_join_time_by_user_id,
    check_user_exists,
    delete_user_by_id
)

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_roles.start()  # Start the task here

    def generate_password(self, length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        password = self.generate_password()
        unverified_role = discord.utils.get(member.guild.roles, id=UNVERIFIED_ROLE_ID)
        
        if unverified_role:
            await member.add_roles(unverified_role, reason="New member - assigned Unverified role")

        add_user(member.id, datetime.now(), password)

        try:
            await member.send(f"Welcome to the server, {member.name}! Here is your password, make sure to send this password in the notice chat!")
            await member.send(f"{password}")
        except discord.Forbidden:
            print(f"Could not send DM to {member.name}. They may have DMs disabled.")
            notice_channel = self.bot.get_channel(NOTICE_CHANNEL_ID)
            if notice_channel:
                await notice_channel.send(
                    f"{member.mention}, I couldn't send you a DM with your verification password. Please enable your dms and then use the command `$DMuser YourUserID` so I can send you the password again!"
                    f"Please check your DM settings and let me know if you need help."
                )
            else:
                print(f"Notice channel with ID {NOTICE_CHANNEL_ID} not found.")

        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if welcome_channel:
            await welcome_channel.send(
                f"Welcome {member.mention}! {NOTICE_MESSAGE}"
            )
        else:
            print(f"Welcome channel with ID {WELCOME_CHANNEL_ID} not found.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.id == NOTICE_CHANNEL_ID:
            member_id = message.author.id

            if check_user_exists(member_id):
                stored_password = get_password_by_user_id(member_id)
                if message.content == stored_password:
                    verified_role = discord.utils.get(message.guild.roles, id=REQUIRED_ROLE_ID)
                    unverified_role = discord.utils.get(message.guild.roles, id=UNVERIFIED_ROLE_ID)

                    if verified_role:
                        await message.author.add_roles(verified_role, reason="Correct verification password provided.")
                    if unverified_role:
                        await message.author.remove_roles(unverified_role, reason="Member verified - removed Unverified role")

                    await message.channel.send(f"{message.author.mention} has been verified successfully!")
                    delete_user_by_id(member_id)
                else:
                    await message.channel.send(
                        f"{message.author.mention}, the password you provided is incorrect. Please try again."
                    )
            else:
                await message.channel.send(
                    f"{message.author.mention}, I couldn't find your verification details. Please ensure you've recently joined the server."
                )

    @commands.command(name="dmme", help="Resends your verification password if you have updated your DM settings.")
    async def dm_me(self, ctx):
        member = ctx.author
        member_id = member.id

        if not check_user_exists(member_id):
            await ctx.send(
                f"{member.mention}, I couldn't find your verification details. Please make sure you've recently joined the server."
            )
            return

        password = get_password_by_user_id(member_id)
        if not password:
            await ctx.send(
                f"{member.mention}, something went wrong. Please contact a moderator for assistance."
            )
            return

        try:
            await member.send(f"{password}")
            await ctx.send(f"{member.mention}, I've sent your verification password to your DMs. Please check!")
        except discord.Forbidden:
            await ctx.send(
                f"{member.mention}, I still couldn't DM you. Please ensure that your DMs are enabled and try again."
            )

    @commands.command(name="DMuser", help="DMs the verification password again to a specific user by mention or ID.")
    async def dm_user(self, ctx, user: discord.Member):
        member_id = user.id

        password = get_password_by_user_id(member_id)
        if not password:
            await ctx.send(
                f"{user.mention}, something went wrong. Please contact a moderator for assistance through <#1243567293750050887>."
            )
            return

        try:
            await user.send(f"Hello {user.name}, here is your verification password:")
            await user.send(f"{password}")
            await ctx.send(f"{user.mention}, I've sent your verification password to your DMs. Please check!")
        except discord.Forbidden:
            await ctx.send(
                f"{user.mention}, I couldn't DM you. Please ensure that your DMs are enabled and try again."
            )

    @tasks.loop(minutes=60)
    async def check_roles(self):
        try:
            for guild in self.bot.guilds:
                for member in guild.members:
                    if check_user_exists(member.id):  
                        join_time = get_join_time_by_user_id(member.id)
                        if not join_time:
                            print(f"No join time found for {member.name}. Skipping.")
                            continue
                        # Convert to datetime if necessary
                        if isinstance(join_time, str):
                            join_time = datetime.strptime(join_time, '%Y-%m-%d %H:%M:%S')

                        time_since_join = datetime.now() - join_time
                        if time_since_join >= timedelta(hours=48):
                            required_role = discord.utils.get(guild.roles, id=REQUIRED_ROLE_ID)
                            if required_role and required_role not in member.roles:
                                await member.kick(reason="Failed to get required role within 48 hours.")
                                print(f"Kicked {member.name} for not verifying in time.")
                                delete_user_by_id(member.id)
        except Exception as e:
            print(f"Error in check_roles task: {e}")
