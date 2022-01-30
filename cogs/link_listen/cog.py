import traceback
import re

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Cog
from esipy import EsiClient
from esipy.exceptions import APIException

from utils import get_json
from utils.loggers import get_logger
from cogs.kill_watch.helpers import extract_mail_data, build_embed

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
                    embed = await build_embed(data)

                    return await message.reply(embed=embed)
                elif re_match[4] == '/character/':
                    pass
                else:
                    return


def setup(bot):
    bot.add_cog(LinkListener(bot))


def teardown(bot):
    bot.remove_cog(LinkListener)