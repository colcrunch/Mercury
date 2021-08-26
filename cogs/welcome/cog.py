import discord
from discord.ext import commands
from discord.ext.commands import Cog

from .models import *
from utils import checks
from utils.loggers import get_logger

logger = get_logger(__name__)


class Welcome(Cog, command_attrs=dict(hidden=True)):
    """
    Automatically welcome new people!
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['welcome', 'wc'])
    @checks.is_admin()
    async def set_welcome_channel(self, ctx):
        """
        This command sets the channel to be used to welcome members in.
        """
        channels = await WelcomeChannel.filter(pk=ctx.guild.id)
        if len(channels) is not 0:
            return await ctx.send(f'Welcome channel already set for `{ctx.guild.name}`. '
                                  f'To change it, please first unset the welcome channel using '
                                  f'the `unset_welcome_channel` command.')

        # Set the welcome channel.
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        channel = WelcomeChannel(guild_id=guild_id, channel_id=channel_id)
        await channel.save()

        return await ctx.send(f'{ctx.channel.mention} has been set as the welcome channel for `{ctx.guild.name}`.')

    @commands.command(aliases=['delete_wc','wcd'])
    @checks.is_admin()
    async def unset_welcome_channel(self, ctx):
        """
        This command unsets the welcome channel for the server.
            Note: This command can be run from any channel.
        """
        guild_id = ctx.guild.id
        channels = await WelcomeChannel.filter(pk=guild_id)
        if len(channels) is 0:
            return await ctx.send(f'Welcome channel not set for `{ctx.guild.name}.'
                                  f' Use the `set_welcome_channel` command to set it.')

        await channels[0].delete()
        return await ctx.send(f'Unset welcome channel for `{ctx.guild.name}`')

    @commands.command(aliases=['wmessage', 'wm'])
    @checks.is_admin()
    async def set_welcome_message(self, ctx, *, message):
        """
        This command sets the welcome message to be displayed when someone new joins.

        If you would like to mention the user in the welcome message include {mention} (with the brackets)
        in the message.
        """
        guild_id = ctx.guild.id
        messages = await WelcomeMessage.filter(pk=guild_id)
        if len(messages) is not 0:
            return await ctx.send(f'Welcome message for `{ctx.guild.name}` is already set. '
                                  f'To change it, please first unset the welcome message '
                                  f'by running the `unset_welcome_message` command.')

        welcome_message = WelcomeMessage(guild_id=guild_id, message=message)
        await welcome_message.save()

        return await ctx.send(f'`{message}` set as welcome message for `{ctx.guild.name}`')

    @commands.command(aliases=['wmessage_delete','wmd'])
    @checks.is_admin()
    async def unset_welcome_message(self, ctx):
        """
        This command unsets the welcome message for the current server.
        """
        guild_id = ctx.guild.id
        messages = await WelcomeMessage.filter(pk=guild_id)
        if len(messages) is 0:
            return await ctx.send(f'Welcome message for `{ctx.guild.name}` is not yet set. '
                                  f'To set the welcome message, please run the '
                                  f'`set_welcome_message` command.')

        await messages[0].delete()

        return await ctx.send(f'Unset welcome message for `{ctx.guild.name}`')

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Sends the guild welcome message to a new member when they join.
        """
        logger.debug("Member Join Listener Called")
        guild = member.guild.id
        channel = await WelcomeChannel.filter(pk=guild).first()
        message = await WelcomeMessage.filter(pk=guild).first()
        logger.debug(f"{channel}   |   {message}")

        fmt = {'mention': member.mention}
        formatted_msg = message.message.format(**fmt)

        channel = member.guild.get_channel(channel.channel_id)
        return await channel.send(formatted_msg)


def setup(authbot):
    authbot.add_cog(Welcome(authbot))


def teardown(authbot):
    authbot.remove_cog(Welcome)
