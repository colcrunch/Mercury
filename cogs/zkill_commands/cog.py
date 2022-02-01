import traceback
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog
from esipy import EsiClient
from esipy.exceptions import APIException

from utils import get_json
from utils.loggers import get_logger
from .helpers import *

logger = get_logger(__name__)


class ZkillCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.esi = EsiClient(
            retry_requests=True,
            headers={
                'User-Agent': f'applucation: MercuryBot contact: {self.bot.config["bot"]["user_agent"]}'
            }
        )

    async def _get_character_id_from_esi(self, name: str) -> int:
        """
        Returns the character ID from ESI.
            Returns -1 when no ID is returned for a name.
        :param name:
        :return:
        """

        id_op = self.bot.esi_app.op["get_search"](
            categories="character",
            search=name,
            strict=True
        )

        id_response = self.esi.request(id_op)

        if "character" not in id_response.data:
            return -1

        return int(id_response.data['character'][0])

    async def _get_character_name_from_id(self, character_id: int) -> Optional[str]:
        """
        Returns the name of a character for a given character_id.
            Returns None if the ID is not valid.
        :param character_id:
        :return:
        """
        name_op = self.bot.esi_app.op["get_characters_character_id"](
            character_id=character_id
        )

        try:
            name_response = self.esi.request(name_op)
        except APIException:
            logger.error(f'Error getting name for character with ID {character_id} from ESI.')
            logger.error(traceback.print_exc())
            return None

        return name_response.data['name']

    @commands.command(aliases=['t'])
    async def threat(self, ctx, *, name: str):
        """
        Returns info on a character from the zKill stats API.
        """
        # Get the character_id from ESI
        char_id = await self._get_character_id_from_esi(name)
        if char_id == -1:
            return await ctx.send(f"Character `{name}` not found. Please check the spelling and try again.")

        # Get the real name from ESI (ensure it is spelled correctly... i.e. dont trust user input)
        char_name = await self._get_character_name_from_id(char_id)
        if char_name is None:
            return await ctx.send("Something went wrong, please try again later.")

        # Get Zkill Stats
        stats = await get_char_stats_from_zkill(char_id)
        if stats is None:
            return await ctx.send("The provided character has no killboard stats.")

        embed = await build_embed(stats, name, char_id)

        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ZkillCommands(bot))


def teardown(bot):
    bot.remove_cog(ZkillCommands)