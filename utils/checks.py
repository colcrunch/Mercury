import discord
from discord.ext import commands
from cogs.core.models import BotAdminRole

from .loggers import get_logger

logger = get_logger(__name__)


def guild_owner():
    """
    Checks if a user is the owner of a guild.
    :return:
    """
    async def predicate(ctx):
        if type(ctx.channel) is discord.DMChannel:
            return False
        elif await ctx.bot.is_owner(ctx.author):
            return True
        elif ctx.author is ctx.guild.owner:
            return True
    return commands.check(predicate)


def is_admin():
    """
    Checks if the user is a bot admin.
    :return:
    """
    async def predicate(ctx):
        if type(ctx.channel) is discord.DMChannel:
            return False
        elif await ctx.bot.is_owner(ctx.author):
            return True
        elif ctx.author is ctx.guild.owner:
            return True
        admin_role_obj = await BotAdminRole.filter(pk=ctx.guild.id).first()
        if admin_role_obj is None:
            return False

        # Get Role
        admin_role_id = admin_role_obj.role_id
        admin_role = ctx.guild.get_role(admin_role_id)
        user_roles = ctx.author.roles
        if admin_role in user_roles:
            return True
        else:
            return False
    return commands.check(predicate)
