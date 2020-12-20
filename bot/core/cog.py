import discord
from discord.ext import commands

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
