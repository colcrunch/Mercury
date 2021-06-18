'''
********************************************
***** THIS IS NOT THE BOT CONFIG FILE! *****
***** DO NOT MANUALLY EDIT THIS FILE!  *****
********************************************
'''

from pathlib import Path
from os import path
from tomlkit import loads

# Load the bot config.
conf = False
if path.exists('config.toml'):
    conf = True
    with open("config.toml", "r") as c:
        config = loads(c.read())

if conf:
    db_set = config['db']
    TORTOISE_ORM = {
        "connections": {
            "default": f"postgres://"
                       f"{db_set['user']}:{db_set['pass']}@{db_set['host']}:{db_set['port']}/{db_set['db_name']}"
        },
        "apps": {
            "models": {
                "models": ['aerich.models'],
                "default_connection": "default",
            }
        }
    }
else:
    TORTOISE_ORM = None