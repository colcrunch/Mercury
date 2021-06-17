import discord
from discord.ext import commands


def guild_owner():
    """
    Checks if a user is the owner of a guild.
    """
    async def predicate(ctx):
        if type(ctx.channel) is discord.DMChannel:
            return False
        elif await ctx.bot.is_owner(ctx.author):
            return True
        elif ctx.author is ctx.guild.owner:
            return True
    return commands.check(predicate)
