from tomlkit import loads, dumps
from discord.ext.commands import Bot
from discord.ext import commands
from discord import Game

import traceback
import os
import shutil
import logging
import datetime

logger = logging.getLogger(__name__)


def setup():
    """
    Configures the bot.
    If a configuration exists, this function will serve to edit the existing config.
    :return:
    """

    # Determine if this is the first run.
    if os.path.exists("bot/config.toml"):
        print("Configuration file already exists. Would you like to edit it?")
        x = input("[Y/N]: ")
        if x.lower() != "y":
            print("Setup Cancelled!")
            return
    else:
        shutil.copy("bot/config.toml.example", "bot/config.toml")

    # Clear the screen and display the banner
    os.system("cls||clear")
    print("Welcome to Mercury! Lets configure the bot!")
    print("Press [Enter] to keep the current setting...")

    # Attempt to load the config file.
    try:
        with open('bot/config.toml', 'r') as c:
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
        with open('bot/config.toml', 'w') as c:
            c.write(final)
    except Exception as e:
        print(f"An error occurred when saving the configuration! Error: {e}")
        return

    print("\n\nConfiguration file saved!")
    return


class MercuryBot(Bot):
    def __init__(self, config, *args, **kwargs):
        self.config = config

        self.description = "A discord.py bot to do some stuff."

        self.token = config['bot']['token']
        self.prefix = config['bot']['prefix']
        self.started = datetime.datetime.utcnow()

        super().__init__(command_prefix=self.prefix, description=self.description, pm_help=None, *args, **kwargs)

    def run(self):
        super().run(self.token)

    async def on_ready(self):
        # Load Extensions
        try:
            self.load_extension(f'bot.core.cog')    # Core cog(s) should always be loaded.
        except Exception as e:
            logger.fatal("Core cog failed to load. Exception:")
            logger.fatal(e)
            print("Core cog could not be loaded. Please check the logs for more information.")

            return exit(1)
        else:
            pass

        for extension in self.config['bot']['extensions']:
            try:
                self.load_extension(f'bot.cogs.{extension}.cog')
            except Exception as e:
                logger.critical(f'{extension} failed to load. Exception:')
                logger.critical(e)
                print(f'{extension} failed to load. Check logs for details.')
            else:
                logger.debug(f'{extension} loaded')
                print(f'{extension} has loaded successfully.')

        # Set the presence for the bot.
        await self.change_presence(activity=Game(name=self.config['bot']['presence']))
        logger.info(f"Bot started! (U: {self.user.name} I: {self.user.id})")
        print(f"Bot Started! (U: {self.user.name} I: {self.user.id})")

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.NoPrivateMessage):
            await context.author.send('This command cannot be used in private messages.')
        elif isinstance(exception, commands.DisabledCommand):
            await context.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(exception, commands.UserInputError):
            await context.send(exception)
        elif isinstance(exception, commands.NotOwner):
            logger.error('%s tried to run %s but is not the owner' % (context.author, context.command.name))
        elif isinstance(exception, commands.CommandInvokeError):
            logger.error('In %s:' % context.command.qualified_name)
            logger.error(''.join(traceback.format_tb(exception.original.__traceback__)))
            logger.error('{0.__class__.__name__}: {0}'.format(exception.original))



