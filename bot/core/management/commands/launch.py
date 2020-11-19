from django.core.management.base import BaseCommand, CommandError
from os import path
from tomlkit import loads

from bot.bot import MercuryBot, setup


class Command(BaseCommand):
    help = "Launch or configure the bot."

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Setup or reconfigure the bot.'
        )

        parser.add_argument(
            "--confexist",
            action='store_true',
            help="Check whether or not the bot's config has been generated."
        )

    def handle(self, *args, **options):
        config = None
        if options['confexist']:
            # Just a sanity check that our config file actually exists.
            p = path.exists('bot/config.toml')
            print("Path to config exists? " + str(p))
            return 0

        if options['setup'] or not path.exists('bot/config.toml'):
            # Run the setup process then load the config.
            # We will always do this on the first run.
            setup()

            print("Bot configuration complete... Starting Bot....")

            with open("bot/config.toml", "r") as c:
                config = loads(c.read())
        else:
            # Load the config
            with open("bot/config.toml", "r") as c:
                config = loads(c.read())

        if config is None:
            # If for some reason config is still None, then raise a CommandError
            raise CommandError(returncode=1)

        mBot = MercuryBot(config=config)
        MercuryBot.run(mBot)
