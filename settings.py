'''
********************************************
***** THIS IS NOT THE BOT CONFIG FILE! *****
***** DO NOT MANUALLY EDIT THIS FILE!  *****
********************************************
'''

import os
from os import path, listdir
from tomlkit import loads
import logging

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
    TORTOISE_ORM["apps"]["models"]["models"] += [
        f"cogs.{name}.models"
        for name in listdir('cogs/')
        if os.path.isdir(os.path.join('cogs/', name)) and not name.__contains__("__") and os.path.exists(f"cogs/{name}/models.py")
    ]

    log_level = logging.getLevelName(config['logging']['level'])
else:
    TORTOISE_ORM = None
