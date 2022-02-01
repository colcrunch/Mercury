import traceback
import re
from typing import Optional

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from esipy import EsiClient
from esipy.exceptions import APIException

from utils import get_json
from utils.loggers import get_logger
from cogs.kill_watch.helpers import extract_mail_data, build_embed as build_kill_embed
from cogs.zkill_commands.helpers import get_char_stats_from_zkill, build_embed as build_threat_embed
from cogs.market.helpers import get_market_data, build_embed as build_market_embed

logger = get_logger(__name__)


class LinkListener(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.esi = EsiClient(
            retry_requests=True,
            headers={'User-Agent': f'application: MercuryBot contact: {self.bot.config["bot"]["user_agent"]}'}
        )

    async def _get_killmail(self, kill_id: int) -> dict:
        """
        Get killmail from zkill and ESI.
        :param kill_id:
        :return:
        """

        # Get zkill data
        kill_api_url = f'https://zkillboard.com/api/killID/{kill_id}/'
        async with aiohttp.ClientSession() as session:
            zkill_km = await get_json(session, kill_api_url)

        zkill_km = zkill_km['resp'][0]

        # Get KM data via ESI
        km_op = self.bot.esi_app.op['get_killmails_killmail_id_killmail_hash'](
            killmail_id=kill_id,
            killmail_hash=zkill_km['zkb']['hash'],
        )

        km_response = self.esi.request(km_op)

        km = km_response.data
        km['zkb'] = zkill_km['zkb']

        return km

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

    async def type_from_id(self, type_id: int) -> Optional[dict]:
        """
        Returns a type ID from ESI for a given name.
            Return value of None indicates an invalid type name.
        :param type_id:
        :return:
        """
        post_op = self.bot.esi_app.op['get_universe_types_type_id'](type_id=type_id)

        try:
            response = self.esi.request(post_op)
        except APIException:
            logger.error(f"Issue getting Type with ID {type_id} from ESI!")
            logger.error(traceback.print_exc())
            return None

        return response.data

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        # Check for links
        re_match = re.match(r'(.*)(http[s]?://([A-Za-z]*).[a-zA-z]*(/[a-zA-z]*/?)([0-9]*)[a-zA-Z/]?)', message.content)
        """
         Match Groups:
         Group 1 (match[1]): anything preceding the link.
         Group 2 (match[2]): The link in its entirety
         Group 3 (match[3]): The domain of the URL. This is how we determine if/how to process it.
         Group 4 (match[4]): Only used for zkill at the moment, to determine if the URL is a kill or not.
         Group 5 (match[5]): The ID we will need for processing. We know that all the services we want to process use 
                             only numeric IDs, so this is fine. (Though probably not the best if we wanted to add 
                             dscan.me support or something.
        """
        if re_match:
            if re_match[3] == 'zkillboard':
                if re_match[4] == '/kill/':
                    km = await self._get_killmail(re_match[5])
                    data = extract_mail_data(self.bot.esi_app, self.esi, km)
                    embed = await build_kill_embed(data)

                    return await message.reply(embed=embed)
                elif re_match[4] == '/character/':
                    char_id = re_match[5]
                    stats = await get_char_stats_from_zkill(char_id)
                    if stats is None:
                        return
                    char_name = await self._get_character_name_from_id(char_id)

                    embed = await build_threat_embed(stats, char_name, char_id)

                    return await message.reply(embed=embed)
                else:
                    return
            elif re_match[3] == 'evemarketer':
                type_id = re_match[5]
                type_data = await self.type_from_id(type_id)
                # Rename the type_id key for compatability with embed builder.
                type_data['id'] = type_data.pop('type_id')
                market_data = await get_market_data(type_id)

                embed = await build_market_embed(type_data, market_data['resp'])

                return await message.reply(embed=embed)
            else:
                return


def setup(bot):
    bot.add_cog(LinkListener(bot))


def teardown(bot):
    bot.remove_cog(LinkListener)