from tomlkit import loads, dumps
import shutil
import os
from discord.ext.commands import Bot


def setup():
    """
    Configures the bot-o.
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
    print("Welcome to Mercury! Lets configure the bot-o!")
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
        pass
