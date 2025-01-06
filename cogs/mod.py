import discord
from discord.ext import commands

ASSISTANT_ROLE_ID = 1243929202785386527
MODS_ROLE_ID = 1243559774847766619
ADMINS_ROLE_ID = 1243929060145631262
CO_OWNERS_ROLE_ID = 1243930541234065489
OWNERS_ROLE_ID = 1240455108047671406
BOT_MANAGER_ID = 1244254759561592893

warnings = {}

class ModCog(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot

    @commands.command()
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            await ctx.send(f'Please provide a reason for the warning, {ctx.author.mention}.')
            return
    
        if member.id not in warnings:
            warnings[member.id] = []
        warnings[member.id].append(reason)
    
        embed = discord.Embed(title="User Warned", color=discord.Color.orange())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Warned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=len(warnings[member.id]), inline=False)
    
        await ctx.send(embed=embed)
        try:
            await member.send(f'You have been warned in {ctx.guild.name} for the following reason: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')

    
    
    @commands.command()
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def removewarn(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            await ctx.send(f'Please provide a reason for removing the warning, {ctx.author.mention}.')
            return
    
        if member.id not in warnings or not warnings[member.id]:
            await ctx.send(f'{member.mention} has no warnings.')
            return

        warnings[member.id].pop()

        embed = discord.Embed(title="Warning Removed", color=discord.Color.green())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Removed by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Total Warnings", value=len(warnings[member.id]), inline=False)
    
        await ctx.send(embed=embed)
        try:
            await member.send(f'Your warning in {ctx.guild.name} has been removed for the following reason: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')


    @commands.command()
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            await ctx.send(f'Please provide a reason for the ban, {ctx.author.mention}.')
            return
    
        await member.ban(reason=reason)
        embed = discord.Embed(title="User Banned", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Banned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
    
        await ctx.send(embed=embed)
        try:
            await member.send(f'You have been banned from {ctx.guild.name} for the following reason: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')

    @commands.command()
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            await ctx.send(f'Please provide a reason for the kick, {ctx.author.mention}.')
            return
    
        await member.kick(reason=reason)
        embed = discord.Embed(title="User Kicked", color=discord.Color.blue())
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Kicked by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)

        await ctx.send(embed=embed)
        try:
            await member.send(f'You have been kicked from {ctx.guild.name} for the following reason: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to {member.mention}, they might have DMs disabled.')

    @commands.command()
    @commands.has_any_role(MODS_ROLE_ID, ADMINS_ROLE_ID, CO_OWNERS_ROLE_ID, OWNERS_ROLE_ID, BOT_MANAGER_ID)
    async def unban(self, ctx, user_id: int, *, reason=None):
        user = discord.Object(user_id)
        await ctx.guild.unban(user, reason=reason)
    
        embed = discord.Embed(title="User Unbanned", color=discord.Color.green())
        embed.add_field(name="User ID", value=user_id, inline=True)
        embed.add_field(name="Unbanned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
    
        await ctx.send(embed=embed)
        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(f'You have been unbanned from {ctx.guild.name} for the following reason: {reason}')
        except discord.Forbidden:
            await ctx.send(f'Could not send DM to user with ID {user_id}, they might have DMs disabled.')
        except discord.NotFound:
            await ctx.send(f'Could not find user with ID {user_id}.')

    @warn.error
    @removewarn.error
    @kick.error
    @ban.error
    @unban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send(f'Sorry {ctx.author.mention}, you do not have permission to use this command.')



async def setup(bot):
    await bot.add_cog(ModCog(bot))
