import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import random
import string
from discord import Embed
import os

# Configuration constants
REQUIRED_ROLE_ID = os.getenv('REQUIRED_ROLE_ID') 
UNVERIFIED_ROLE_ID = os.getenv('UNVERIFIED_ROLE_ID')
WELCOME_CHANNEL_ID = os.getenv('WELCOME_CHANNEL_ID') 
NOTICE_CHANNEL_ID = os.getenv('NOTICE_CHANNEL_ID')
NOTICE_MESSAGE = "You must get the 'Verified' role within 48 hours by sending the password I just DMed you in this chat."
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')

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

    async def log_event(self, message: str, member: discord.Member):
        """Helper function to log events in the verification log channel"""
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        
        if log_channel:
            embed = Embed(
                title="Verification Log",
                description=message,
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            embed.add_field(name="User", value=f"<@{member.id}> | {member.id}", inline=True)

            await log_channel.send(embed=embed)
        else:
            print("Log channel not found.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        password = self.generate_password()
        unverified_role = discord.utils.get(member.guild.roles, id=UNVERIFIED_ROLE_ID)
        
        if unverified_role:
            # Log member join event in the log channel
            await self.log_event(f"{member.name} has joined the server and was sent a verification password.", member)


        add_user(member.id, datetime.now(), password)

        try:
            await member.send(f"Welcome to the server, {member.name}! Here is your password, make sure to send this password in the notice chat!")
            await member.send(f"{password}")
        except discord.Forbidden:
            print(f"Could not send DM to {member.name}. They may have DMs disabled.")
            notice_channel = self.bot.get_channel(NOTICE_CHANNEL_ID)
            
            if notice_channel:
                embed = Embed(
                    title="Didn't get a message?",
                    description=(
                        "Make sure that you have your DMs enabled!\n"
                        "**Settings > Content & Social** (check the image below)\n\n"
                        "Once you have turned your DMs on, run the command:\n"
                        "`!DMuser YourUserID` (e.g., `!DMuser 766005564190359552`)\n\n"
                        "If you are still having trouble getting the password, please contact our staff via <#1243567293750050887>."
                    ),
                    color=discord.Color.red()
                )

                embed.set_image(url="https://media.discordapp.net/attachments/1245431550942904341/1336622814542696468/image-2.png?ex=67b1a980&is=67b05800&hm=4c2e1dec22d38e5803c4fcc8f715d363505f1ce9bf40219a5c85555f33ece0e3&=&format=webp&quality=lossless&width=614&height=218")
                
                await notice_channel.send(content=f"{member.mention}", embed=embed)
            else:
                print(f"Notice channel with ID {NOTICE_CHANNEL_ID} not found.")


        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if welcome_channel:
            await welcome_channel.send(
                f"Welcome {member.mention}! {NOTICE_MESSAGE}"
            )
        else:
            print(f"Welcome channel with ID {WELCOME_CHANNEL_ID} not found.")

        # Log member join event in the log channel
        await self.log_event(f"{member.name} has joined the server and was sent a verification password.")


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

                    # Log password verification event
                    await self.log_event(f"{message.author.name} has been successfully verified.", message.author)

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

        # Log DM request event
        await self.log_event(f"{member.name} requested to resend their verification password.")

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

        # Log DM request for another user
        await self.log_event(f"Verification password was resent to {user.name} by {ctx.author.name}.")

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

                                # Log kick event
                                await self.log_event(f"{member.name} was kicked for failing to verify within 48 hours.")
        except Exception as e:
            print(f"Error in check_roles task: {e}")

async def setup(bot):
    await bot.add_cog(Security(bot))
