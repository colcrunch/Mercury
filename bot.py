import discord
from tomlkit import loads, dumps
from discord.ext.commands import Bot
from discord.ext import commands

import settings
from utils.loggers import get_logger
from tortoise import Tortoise

import os
import traceback
import shutil
import datetime
import logging


def setup():
    """
    Configures the bot.
    If a configuration exists, this function will serve to edit the existing config.
    :return:
    """

    # Determine if this is the first run.
    if os.path.exists("config.toml"):
        print("Configuration file already exists. Would you like to edit it?")
        x = input("[Y/N]: ")
        if x.lower() != "y":
            print("Setup Cancelled!")
            return
    else:
        shutil.copy("config.toml.example", "config.toml")

    # Clear the screen and display the banner
    os.system("cls||clear")
    print("Welcome to Mercury! Lets configure the bot!")
    print("Press [Enter] to keep the current setting...")

    # Attempt to load the config file.
    try:
        with open('config.toml', 'r') as c:
            config = c.read()
        config = loads(config)
    except Exception as e:
        print(f"An error occurred during setup! Error: {e}")
        return

    # Loop through the config tables and their settings and get input from the user for each setting.
    for _table in config:
        print(f"\n\nConfiguring {_table} settings")
        for setting in config[_table]:
            x = str(input(f"{setting} (Current: {config[_table][setting]})=> "))
            if setting == "extensions":
                x = x.split()
            config[_table][setting] = x or config[_table][setting]

    # Save the config file.
    try:
        final = dumps(config)
        with open('config.toml', 'w') as c:
            c.write(final)
    except Exception as e:
        print(f"An error occurred when saving the configuration! Error: {e}")
        return

    print("\n\nConfiguration file saved!")
    return


class MercuryBot(Bot):
    def __init__(self, config, *args, **kwargs):
        self.config = config
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True

        self.description = "A discord.py bot to do some stuff."

        self.token = config['bot']['token']
        self.prefix = config['bot']['prefix']
        self.started = datetime.datetime.utcnow()

        self.logger = get_logger(__name__)

        super().__init__(
            command_prefix=self.prefix,
            description=self.description,
            pm_help=None,
            activity=discord.Activity(name=config['bot']['status'], type=discord.ActivityType.playing),
            status=discord.Status.idle,
            intents=intents,
            *args,
            **kwargs
        )

        self.loop.create_task(Tortoise.init(config=settings.TORTOISE_ORM))  # Connect to the database.

        # Load extensions
        try:
            self.load_extension(f'cogs.core.cog')
        except Exception as e:
            self.logger.fatal("Core cog failed to load. Exception:")
            self.logger.fatal(e)
            print("Core cog could not be loaded. Please check the logs for more information.")

            exit(1)

        for extension in self.config['bot']['extensions']:
            try:
                self.load_extension(f'cogs.{extension}.cog')
            except Exception as e:
                self.logger.critical(f"{extension} failed to load. Exception:")
                self.logger.critical(e)
                print(f"{extension} failed to load. Check logs for more details.")
            else:
                self.logger.info(f'{extension} loaded.')
                print(f"{extension} loaded successfully.")

    def run(self):
        super().run(self.token)

    async def on_ready(self):
        self.logger.info(f"Bot Started! (U: {self.user.name} I: {self.user.id})")
        print(f"Bot Started! (U: {self.user.name} I: {self.user.id})")

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.NoPrivateMessage):
            await context.author.send('This command cannot be used in private messages.')
        elif isinstance(exception, commands.DisabledCommand):
            await context.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(exception, commands.UserInputError):
            await context.send(exception)
        elif isinstance(exception, commands.NotOwner):
            self.logger.error('%s tried to run %s but is not the owner' % (context.author, context.command.name))
        elif isinstance(exception, commands.CommandInvokeError):
            self.logger.error('In %s:' % context.command.qualified_name)
            self.logger.error(''.join(traceback.format_tb(exception.original.__traceback__)))
            self.logger.error('{0.__class__.__name__}: {0}'.format(exception.original))
