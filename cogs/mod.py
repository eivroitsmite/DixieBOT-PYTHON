import discord
from discord.ext import commands
from datetime import timedelta
from dbconnMOD import (
    add_mod_log,
    get_mod_logs_by_user,
    get_mod_logs_by_moderator,
    check_log_exists,
    delete_mod_log_by_id
)

# Role IDs
JRMOD_ROLE_ID = 1334950965408956527
MODS_ROLE_ID = 1243559774847766619
ADMINS_ROLE_ID = 1243929060145631262
CO_OWNERS_ROLE_ID = 1243930541234065489
OWNERS_ROLE_ID = 1240455108047671406
BOT_MANAGER_ID = 1244254759561592893

warnings = {"minor": {}, "major": {}}

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
        add_mod_log(member.id, reason, ctx.author.id)

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
        add_mod_log(member.id, "ban", ctx.author.id)

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
            await ctx.send('Timeout duration cannot exceed 30 days.')
            return

        await member.edit(timed_out_until=discord.utils.utcnow() + delta)

        embed = discord.Embed(title="User Timed Out", color=discord.Color.orange())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Timed out by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Duration", value=f'{duration} {unit}', inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

        # Log to database
        add_mod_log(member.id, f"timeout: {duration} {unit}", ctx.author.id)

    @commands.command()
    @commands.has_any_role(JRMOD_ROLE_ID, MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.kick(reason=reason)

        embed = discord.Embed(title="User Kicked", color=discord.Color.blue())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Kicked by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)

        # Log to database
        add_mod_log(member.id, "kick", ctx.author.id)

        try:
            await member.send(f'You have been kicked from {ctx.guild.name} for: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')

    @warn_minor.error
    @warn_major.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to use this command.')

async def setup(bot):
    print("✅ ModCog is being loaded!")
    await bot.add_cog(ModCog(bot))
