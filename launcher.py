import argparse
from tomlkit import loads
from os import path
from bot import MercuryBot, setup
from tortoise import run_async

parser = argparse.ArgumentParser(description="Mercury Discord Bot Launcher")
parser.add_argument("--setup", action='store_true', default=False, help="Runs the bot setup.")
parser.add_argument("--migrate", action="store_true", default=False, help="Runs migrations.")
args = parser.parse_args()


def launch():
    if args.setup:
        setup()
    if not path.exists("config.toml"):
        # First run, or other issues with config.
        setup()
        with open("config.toml", "r") as c:
            config = loads(c.read())
    else:
        with open("config.toml", "r") as c:
            config = loads(c.read())
    if args.migrate:
        pass
    return


launch()
