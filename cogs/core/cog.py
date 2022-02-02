import traceback

import discord
from discord.ext import commands
from datetime import datetime
from pathlib import Path

from .models import *
from utils import checks
from utils.loggers import get_logger

logger = get_logger(__name__)


class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['sd'], hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        """
        Commands the bot to shutdown.
        """
        logger.critical(f"Bot shutdown called by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")
        print(f"Bot shutdown called by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")
        await ctx.send("Bot shutting down.")
        return exit(0)

    @commands.command(aliases=['ld'], hidden=True)
    @commands.is_owner()
    async def loaded(self, ctx):
        """Lists loaded extensions and cogs"""
        extensions = "\n".join([x.split('.')[-2] for x in list(self.bot.extensions)])
        cogs = "\n".join(list(self.bot.cogs))

        ret_str = (
            f'```'
            f'Extensions:\n'
            f'-----------\n'
            f'{extensions} \n\n'
            f'Cogs: \n'
            f'---- \n'
            f'{cogs} \n\n'
            f'{len(self.bot.extensions)} Extensions loaded with {len(self.bot.cogs)} Cogs.'
            f'```'
        )

        return await ctx.send(ret_str)

    @commands.command(aliases=['sad', 'set_adminrole', 'set_admin', 'setadmin', 'setadminrole', 'ad'], hidden=True)
    @checks.guild_owner()
    async def set_admin_role(self, ctx, role: discord.Role):
        """
        Defines the guild's bot admin role.
        """

        roles = await BotAdminRole.filter(pk=ctx.guild.id)
        if len(roles) is not 0:
            return await ctx.send(f'Admin role already set for `{ctx.guild.name}`. '
                                  f'To change it, please first unset the admin role'
                                  f' using the `unset_admin_role` command.')

        # Set the Admin Role.
        role = BotAdminRole(guild_id=ctx.guild.id, role_id=role.id)
        await role.save()

        return await ctx.send(f"Set admin role for `{ctx.guild.name}`.")

    @commands.command(aliases=['rad', 'unset_adminrole', 'unsetadminrole', 'uad', 'unsetadmin', 'removeadmin'],
                      hidden=True)
    @checks.guild_owner()
    async def unset_admin_role(self, ctx):
        """
        Removes the guild's bot admin role.
        """

        admin_role = await BotAdminRole.filter(pk=ctx.guild.id)
        if len(admin_role) is 0:
            return await ctx.send(f"Admin role for `{ctx.guild.name}` is not yet set. To set the admin role"
                                  f" for `{ctx.guild.name}` please run the `set_admin_role` command.")

        # Get the role name from discord.
        name = ctx.guild.get_role(admin_role[0].role_id).name or admin_role[0].role_id

        await admin_role[0].delete()

        return await ctx.send(f"Admin role for `{ctx.guild.name}` successfully unset. (Previous Role: `{name}`)")

    @commands.command(aliases=['lad'], hidden=True)
    @checks.guild_owner()
    async def list_admin_role(self, ctx):
        """
        Displays the admin role set for the current guild.
        """
        admin_role = await BotAdminRole.filter(pk=ctx.guild.id)
        if len(admin_role) is 0:
            return await ctx.send(f"Admin role for `{ctx.guild.name}` is not yet set. To set the admin role"
                                  f" for `{ctx.guild.name}` please run the `set_admin_role` command.")

        # Get the role name from discord.
        name = ctx.guild.get_role(admin_role[0].role_id).name or admin_role[0].role_id

        return await ctx.send(f"Admin Role for `{ctx.guild.name}` is `{name}`. ")

    @commands.command(aliases=['ul'], hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, ext: str):
        """ Unloads an extension. """
        ext = ext.lower()
        try:
            check = Path(f"cogs/{ext}/cog.py")
            if not check.exists():
                return await ctx.send(f"{ext} is not a valid extension")
            elif ext == "core":
                return await ctx.send("Unloading the core extension is not allowed.")
            elif f'cogs.{ext}.cog' not in tuple(self.bot.extensions):
                return await ctx.send(f"Extension {ext} not currently loaded.")
            self.bot.unload_extension(f'cogs.{ext}.cog')
            logger.warning(f'{ext} Unloaded by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})')
            return await ctx.send(f'{ext} Unloaded.')
        except Exception as e:
            logger.error(f"Error unloading {ext}. Error: {e}")
            logger.error(traceback.print_exc())

            return await ctx.send(f'Error unloading {ext}. Check logs for more details.')

    @commands.command(aliases=['l'], hidden=True)
    @commands.is_owner()
    async def load(self, ctx, ext: str):
        """ Loads an extension. """
        ext = ext.lower()
        try:
            check = Path(f"cogs/{ext}/cog.py")
            if not check.exists():
                return await ctx.send(f"{ext} is not a valid extension.")
            elif f'cogs.{ext}.cog' in tuple(self.bot.extensions):
                return await ctx.send(f"Extension {ext} already loaded.")
            self.bot.load_extension(f"cogs.{ext}.cog")
            logger.warning(f'{ext} loaded by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})')
            return await ctx.send(f'{ext} loaded.')
        except Exception as e:
            logger.error(f"Error loading {ext}. Error: {e}")
            logger.error(traceback.print_exc())

            return await ctx.send(f"Error loading {ext}. Check logs for more details.")


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def __base_embed(self, *args, **kwargs):
        """
        Returns a basic embed to be used for core command responses when needed. All kwargs are passed directly
        to the embed constructor.
        :param args:
        :param kwargs:
        :return:
        """
        embed = discord.Embed(**kwargs)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png'))
        embed.set_thumbnail(url=self.bot.user.avatar_url_as(format='png'))

        return embed

    @commands.command(hidden=True)
    @checks.is_admin()
    async def ping(self, ctx):
        """Just a test command."""
        return await ctx.send("Pong!")

    @commands.command()
    async def about(self, ctx):
        """Displays general information about the bot."""

        # Define bot info
        app_info = await self.bot.application_info()
        owner = f'{app_info.owner.name}#{app_info.owner.discriminator}'
        link = 'https://github.com/colcrunch/mercury'
        about_text = "Mercury is a general use discord bot written in python using py-cord."

        embed = self.__base_embed(title=f'About {self.bot.user.name}', description=about_text)
        embed.add_field(name="Bot Owner", value=owner, inline=True)
        embed.add_field(name='Bot Author', value="Col Crunch#3670", inline=True)
        embed.add_field(name='GitHub', value=link, inline=False)

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

    @commands.command(aliases=['et'])
    async def evetime(self, ctx):
        """ Returns the current EVE (UTC) time. """
        return await ctx.send(f'The current EVE (UTC) time is: **{datetime.datetime.utcnow().strftime("%H:%M")}**')


def setup(bot):
    bot.add_cog(AdminCommands(bot))
    bot.add_cog(Core(bot))


def teardown(bot):
    bot.remove_cog(AdminCommands)
    bot.remove_cog(Core)
