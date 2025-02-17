import discord
from discord.ext import commands
from datetime import timedelta
from datetime import timezone
import mysql.connector
from mysql.connector import Error
from discord.utils import utcnow  
from dbconnMOD import add_mod_log, get_warnings, remove_warning
import os

# Role IDs
JRMOD_ROLE_ID = os.getenv('JRMOD_ROLE_ID')
MODS_ROLE_ID = os.getenv('MODS_ROLE_ID')
ADMINS_ROLE_ID = os.getenv('ADMINS_ROLE_ID')
CO_OWNERS_ROLE_ID = os.getenv('CO_OWNERS_ROLE_ID')
OWNERS_ROLE_ID = os.getenv('OWNERS_ROLE_ID')
BOT_MANAGER_ID = os.getenv('BOT_MANAGER_ID')

warnings = {"minor": {}, "major": {}}

def get_permissions(permissions):
    return [perm.replace("_", " ").title() for perm, value in permissions if value]


class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    async def issue_warning(self, ctx, member: discord.Member, warning_type: str, reason: str):
        if not reason:
            await ctx.send(f'Please provide a reason for the warning, {ctx.author.mention}.')
            return

        if member.id not in warnings[warning_type]:
            warnings[warning_type][member.id] = []
        warnings[warning_type][member.id].append(reason)

        embed = discord.Embed(title=f"{warning_type.capitalize()} Warning Issued", color=discord.Color.orange())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Warned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name=f"Total {warning_type.capitalize()} Warnings", value=len(warnings[warning_type][member.id]), inline=False)
        await ctx.send(embed=embed)

        # Log to database
        add_mod_log(member.id, reason, ctx.author.id, f"{warning_type}_warning")

        try:
            await member.send(f'You have received a {warning_type} warning in {ctx.guild.name} for: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')

    @commands.command(name="warn_minor", aliases=["wminor"])
    @commands.has_any_role(JRMOD_ROLE_ID, MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def warn_minor(self, ctx, member: discord.Member, *, reason=None):
        await self.issue_warning(ctx, member, "minor", reason)


    @commands.command(name="warn_major", aliases=["wmajor"])
    @commands.has_any_role(JRMOD_ROLE_ID, MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def warn_major(self, ctx, member: discord.Member, *, reason=None):
        await self.issue_warning(ctx, member, "major", reason)



    @commands.command()
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.ban(reason=reason)

        embed = discord.Embed(title="User Banned", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Banned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

        # Log to database
        add_mod_log(member.id, reason, ctx.author.id, "ban")

        try:
            await member.send(f'You have been banned from {ctx.guild.name} for: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')

    @commands.command()
    @commands.has_any_role(JRMOD_ROLE_ID, MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def timeout(self, ctx, member: discord.Member, duration: int, unit: str, *, reason="No reason provided"):
        if unit not in ["minutes", "hours", "days"]:
            await ctx.send('Invalid time unit. Please use "minutes", "hours", or "days".')
            return

        delta = timedelta(minutes=duration) if unit == "minutes" else timedelta(hours=duration) if unit == "hours" else timedelta(days=duration)

        if delta.total_seconds() > 2592000:
            await ctx.send('Timeout duration cannot exceed 30 days. Please adjust the duration.')
            return

        await member.edit(timed_out_until=utcnow() + delta)

        embed = discord.Embed(title="User Timed Out", color=discord.Color.orange())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Timed out by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Duration", value=f'{duration} {unit}', inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

        # Log to database
        add_mod_log(member.id, f"timeout: {duration} {unit}", ctx.author.id, "timeout")


    @commands.command()
    @commands.has_any_role(JRMOD_ROLE_ID, MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.kick(reason=reason)

        embed = discord.Embed(title="User Kicked", color=discord.Color.yellow())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Kicked by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

        # Log to database
        add_mod_log(member.id, reason, ctx.author.id, "kick")

        try:
            await member.send(f'You have been kicked from {ctx.guild.name} for: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')
            
    @commands.command(name="wremoveminor")
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def wremoveminor(self, ctx, user_id: int, *, reason: str):
        if remove_warning(user_id, "minor", reason):
            await ctx.send(f"✅ Successfully removed **minor** warning for user <@{user_id}>: `{reason}`")
        else:
            await ctx.send(f"❌ Failed to remove **minor** warning for user <@{user_id}>. Either the warning doesn't exist or there was an error.")

    @commands.command(name="wremovemajor")
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def wremovemajor(self, ctx, user_id: int, *, reason: str):
        if remove_warning(user_id, "major", reason):
            await ctx.send(f"✅ Successfully removed **major** warning for user <@{user_id}>: `{reason}`")
        else:
            await ctx.send(f"❌ Failed to remove **major** warning for user <@{user_id}>. Either the warning doesn't exist or there was an error.")

    @commands.command(name="whois")
    async def whois(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        
        # Get user information
        username = member.name
        user_id = member.id
        created_at = member.created_at.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        joined_at = member.joined_at.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        roles = ", ".join([role.mention for role in member.roles if role.name != "@everyone"])
        permissions = get_permissions(member.guild_permissions)
        
        # Fetch warnings from the database
        minor_warnings, major_warnings = get_warnings(user_id)
        minor_count = len(minor_warnings)
        major_count = len(major_warnings)
        
        # Embed response
        embed = discord.Embed(title=f"User Info - {username}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.add_field(name="Username", value=username, inline=True)
        embed.add_field(name="User ID", value=user_id, inline=True)
        embed.add_field(name="Account Created", value=created_at, inline=False)
        embed.add_field(name="Joined Server", value=joined_at, inline=False)
        embed.add_field(name="Roles", value=roles if roles else "None", inline=False)
        embed.add_field(name="Permissions", value=", ".join(permissions) if permissions else "None", inline=False)
        embed.add_field(name="Minor Warnings", value=f"{minor_count} ({', '.join(minor_warnings)})" if minor_warnings else "0", inline=True)
        embed.add_field(name="Major Warnings", value=f"{major_count} ({', '.join(major_warnings)})" if major_warnings else "0", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModCog(bot))
