import discord
from discord.ext import commands

from .models import *
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
        logger.critical(f"Bot shutdown called by {ctx.message.author.id}")
        print(f"Bot shutdown called by {ctx.message.author.id}")
        await ctx.send("Bot shutting down.")
        return exit(0)


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def ping(self, ctx):
        """Just a test command."""
        return await ctx.send("Pong!")


def setup(bot):
    bot.add_cog(AdminCommands(bot))
    bot.add_cog(Core(bot))


def teardown(bot):
    bot.remove_cog(AdminCommands)
    bot.remove_cog(Core)
