import discord
from discord.ext import commands

from .models import *
from . import checks

import logging
from datetime import datetime
from django.core.cache import cache
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


def _get_botadmins(pk):
    return tuple(BotAdminRole.objects.filter(pk=pk))


def _save_role(guild_id, role_id):
    return BotAdminRole.objects.create(guild_id=guild_id, role_id=role_id)


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['sd'], hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        """
        Commands the bot to shutdown.
        """
        logger.critical(f"Bot shutdown called by {ctx.message.author.id}")
        print(f"But shutdown called by {ctx.message.author.id}")
        await ctx.send("Bot shutting down!")
        return exit(0)

    @commands.command(aliases=['ld'], hidden=True)
    @commands.is_owner()
    async def loaded(self, ctx):
        """Lists loaded extensions and cogs."""
        extensions = "\n".join([x.split(".")[-2] for x in list(self.bot.extensions)])
        cogs = "\n".join(list(self.bot.cogs))

        ret_str = (f"```"
                   f"Extensions: \n"
                   f"{extensions} \n\n"
                   f"Cogs: \n"
                   f"{cogs} \n\n"
                   f"{len(self.bot.extensions)} Extensions loaded with {len(self.bot.cogs)} Cogs."
                   f"```")

        return await ctx.send(ret_str)

    @commands.command(aliases=['ad'], hidden=True)
    @checks.guild_owner()
    async def set_admin_role(self, ctx, role: discord.Role):
        """
        Defines the Guild's bot admin role.
        """

        roles = await sync_to_async(_get_botadmins, thread_sensitive=True)(pk=ctx.guild.id)
        if cache.get(f'{ctx.guild.id}:botAdmin') is not None or len(roles) is not 0:
            return ctx.send(f"Admin role already set for `{ctx.guild.name}` to change it, please first unset the admin"
                            f" role using the `unset_admin_role` command.")

        # Set the admin role in the database
        role = await sync_to_async(_save_role, thread_sensitive=True)(guild_id=ctx.guild.id, role_id=role.id)

        # Add the admin role to the cache!
        # For testing purposes... lets leave this out for a second

        return await ctx.send(f"Testing cache: {cache.get('test_key')}")

    @commands.command(aliases=['rad'], hidden=True)
    @checks.guild_owner()
    async def unset_admin_role(self, ctx):
        """
        Removes the Guild's bot admin role.
        """
        admin_role = cache.get(f'{ctx.guild.id}:botAdmin')
        if admin_role is None and len(BotAdminRole.objects.get(pk=ctx.guild.id)) is 0:
            return ctx.send(f"Admin role for `{ctx.guild.name}` is not yet set, and thus can not be unset.\n"
                            f"To set an admin role for `{ctx.guild.name}` please run the `set_admin_role`"
                            f" command from any channel in `{ctx.guild.name}`")
        # Get the role from discord.
        role = ctx.guild.get_role(admin_role).name or admin_role

        # Delete the BotAdminRole entity from the DB.
        BotAdminRole.objects.delete(pk=ctx.guild.id)

        # Delete any record of the admin role from the cache.
        cache.delete(f'{ctx.guild.id}:botAdmin')
        return await ctx.send(f"Admin role for `{ctx.guild.name}` successfully unset. (Previous admin role was "
                              f"{role.name})")


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def __base_embed(self, *args, **kwargs):
        """
        Returns a basic embed to be used for core command responses when needed. All kwargs are passed directly to
        the embed constructor.
        :param args:
        :param kwargs:
        :return:
        """
        embed = discord.Embed(**kwargs)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png'))
        embed.set_thumbnail(url=self.bot.user.avatar_url_as(format='png'))

        return embed

    @commands.command(hidden=True)
    async def ping(self, ctx):
        """Just a test command."""
        return await ctx.send("pong!")

    @commands.command()
    async def about(self, ctx):
        """Display general information about the bot."""

        # Define bot information
        app_info = await self.bot.application_info()
        owner = f'{app_info.owner.name}#{app_info.owner.discriminator}'
        link = 'https://github.com/colcrunch/mercury'
        about_text = ("Mercury is a general use discord bot written in python"
                      " using discord.py and Django.")

        # Build the embed
        embed = self.__base_embed(title=f"About {self.bot.user.name}", description=about_text)
        embed.add_field(name="Bot Owner", value=owner, inline=True)
        embed.add_field(name="Bot Author", value="Col Crunch#3670", inline=True)
        embed.add_field(name="GitHub", value=link, inline=False)

        return await ctx.send(embed=embed)

    @commands.command()
    async def stats(self, ctx):
        """Displays basic stats about the bot."""
        guilds = len(self.bot.guilds)

        # Determine the bot's uptime
        now = datetime.utcnow()
        uptime = now - self.bot.started

        # Build embed
        embed = self.__base_embed(title="Bot Statistics", colour=discord.Color.green())
        embed.add_field(name="Servers", value=str(guilds), inline=True)
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=True)

        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
    bot.add_cog(Core(bot))


def teardown(bot):
    bot.remove_cog(AdminCommands)
    bot.remove_cog(Core)
