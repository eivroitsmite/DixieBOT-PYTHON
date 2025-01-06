import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import string

# Configuration constants
REQUIRED_ROLE_ID = 1243576135481294859  # ID of the role that members must acquire to be verified
UNVERIFIED_ROLE_ID = 1305172270486126663  # ID of the role assigned to unverified members
WELCOME_CHANNEL_ID = 1305164254797893703  # ID of the welcome channel to greet new members
NOTICE_CHANNEL_ID = 1305164254797893703  # ID of the channel where members must send their password
NOTICE_MESSAGE = "You must get the 'Verified' role within 48 hours by sending the password I just DMed you in this chat."

# Bot intents and setup
intents = discord.Intents.default()
intents.members = True  # Enables the bot to listen to member events
bot = commands.Bot(command_prefix="$", intents=intents)

# Importing database functions
from dbconn import (
    add_user,
    get_user_by_id,
    get_password_by_user_id,
    get_join_time_by_user_id,
    check_user_exists,
    delete_user_by_id
)

# Security Cog: Handles member verification process
class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_roles.start()  # Start the role-checking task loop

    # Generates a random alphanumeric password for member verification
    def generate_password(self, length=8):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    # Event listener: Triggered when a new member joins the server
    @commands.Cog.listener()
    async def on_member_join(self, member):
        password = self.generate_password()  # Generate a random password
        unverified_role = discord.utils.get(member.guild.roles, id=UNVERIFIED_ROLE_ID)
        
        # Assign the 'Unverified' role to the new member
        if unverified_role:
            await member.add_roles(unverified_role, reason="New member - assigned Unverified role")

        # Save user details (ID, join time, and password) in the database
        add_user(member.id, datetime.now(), password)

        # Send the verification password via DM
        try:
            await member.send(f"Welcome to the server, {member.name}! Here is your password, make sure to send this password in the notice chat!")
            await member.send(f"{password}")
        except discord.Forbidden:
            # If DM fails, notify the member in the notice channel
            print(f"Could not send DM to {member.name}. They may have DMs disabled.")
            notice_channel = self.bot.get_channel(NOTICE_CHANNEL_ID)
            if notice_channel:
                await notice_channel.send(
                    f"{member.mention}, I couldn't send you a DM with your verification password. "
                    f"Please check your DM settings and let me know if you need help."
                )
            else:
                print(f"Notice channel with ID {NOTICE_CHANNEL_ID} not found.")

        # Send a welcome message in the welcome channel
        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if welcome_channel:
            await welcome_channel.send(
                f"Welcome {member.mention}! {NOTICE_MESSAGE}"
            )
        else:
            print(f"Welcome channel with ID {WELCOME_CHANNEL_ID} not found.")

    # Event listener: Triggered when a message is sent in the server
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return  # Ignore messages from the bot itself

        # Check if the message is sent in the notice channel
        if message.channel.id == NOTICE_CHANNEL_ID:
            member_id = message.author.id

            # Validate the user's password
            if check_user_exists(member_id):
                stored_password = get_password_by_user_id(member_id)
                if message.content == stored_password:
                    # Assign the 'Verified' role and remove the 'Unverified' role
                    verified_role = discord.utils.get(message.guild.roles, id=REQUIRED_ROLE_ID)
                    unverified_role = discord.utils.get(message.guild.roles, id=UNVERIFIED_ROLE_ID)

                    if verified_role:
                        await message.author.add_roles(verified_role, reason="Correct verification password provided.")
                    if unverified_role:
                        await message.author.remove_roles(unverified_role, reason="Member verified - removed Unverified role")

                    await message.channel.send(f"{message.author.mention} has been verified successfully!")
                    delete_user_by_id(member_id)  # Remove the user from the database
                else:
                    # Notify the user if the password is incorrect
                    await message.channel.send(
                        f"{message.author.mention}, the password you provided is incorrect. Please try again."
                    )
            else:
                # Notify the user if their details are not found
                await message.channel.send(
                    f"{message.author.mention}, I couldn't find your verification details. Please ensure you've recently joined the server."
                )

    # Command: Resends the verification password to the member
    @commands.command(name="dmme", help="Resends your verification password if you have updated your DM settings.")
    async def dm_me(self, ctx):
        member = ctx.author
        member_id = member.id

        if not check_user_exists(member_id):
            # Notify the user if they are not in the database
            await ctx.send(
                f"{member.mention}, I couldn't find your verification details. Please make sure you've recently joined the server."
            )
            return

        password = get_password_by_user_id(member_id)
        if not password:
            # Notify the user if no password is found in the database
            await ctx.send(
                f"{member.mention}, something went wrong. Please contact a moderator for assistance."
            )
            return

        # Attempt to resend the password via DM
        try:
            await member.send(f"Hello {member.name}, here is your verification password: **{password}**")
            await ctx.send(f"{member.mention}, I've sent your verification password to your DMs. Please check!")
        except discord.Forbidden:
            # Notify the user if DMs are disabled
            await ctx.send(
                f"{member.mention}, I still couldn't DM you. Please ensure that your DMs are enabled and try again."
            )

    # Command: Allows an admin to resend a password to a specific user
    @commands.command(name="DMuser", help="DMs the verification password again to a specific user by mention or ID.")
    async def dm_user(self, ctx, user: discord.Member):
        member_id = user.id

        if not check_user_exists(member_id):
            # Notify if the user is not in the database
            await ctx.send(
                f"{user.mention}, I couldn't find your verification details. Please make sure you've recently joined the server."
            )
            return

        password = get_password_by_user_id(member_id)
        if not password:
            # Notify if no password is found in the database
            await ctx.send(
                f"{user.mention}, something went wrong. Please contact a moderator for assistance."
            )
            return

        # Attempt to resend the password via DM
        try:
            await user.send(f"Hello {user.name}, here is your verification password: **{password}**")
            await ctx.send(f"{user.mention}, I've sent your verification password to your DMs. Please check!")
        except discord.Forbidden:
            # Notify if DMs are disabled
            await ctx.send(
                f"{user.mention}, I couldn't DM you. Please ensure that your DMs are enabled and try again."
            )

    #Periodically checks roles and kicks unverified members after 48 hours
    @tasks.loop(minutes=60)
    async def check_roles(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if check_user_exists(member.id):  
                    join_time = get_join_time_by_user_id(member.id)

                    if not join_time:
                        print(f"No join time found for {member.name}. Skipping.")
                        continue

                    try:
                        if isinstance(join_time, str):
                            join_time = datetime.strptime(join_time, '%Y-%m-%d %H:%M:%S')

                        if not isinstance(join_time, datetime):
                            print(f"join_time for {member.name} is not a datetime object. Skipping.")
                            continue

                        time_since_join = datetime.now() - join_time

                        if time_since_join >= timedelta(hours=48):
                            required_role = discord.utils.get(guild.roles, id=REQUIRED_ROLE_ID)

                            if not required_role:
                                print(f"Required role not found in {guild.name}. Skipping member checks.")
                                continue

                            if required_role not in member.roles:
                                try:
                                    await member.kick(reason="Failed to get required role within 48 hours.")
                                    print(f"Kicked {member.name} for not verifying in time.")
                                    delete_user_by_id(member.id)
                                except discord.Forbidden:
                                    print(f"Cannot kick {member.name}: insufficient permissions.")
                                except discord.HTTPException as e:
                                    print(f"HTTPException when kicking {member.name}: {e}")
                    except Exception as e:
                        print(f"Error processing {member.name}: {e}")
