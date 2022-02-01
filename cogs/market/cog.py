import traceback
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog
from esipy import EsiClient

from utils.loggers import get_logger
from .helpers import *

logger = get_logger(__name__)


class Market(Cog):
    """
    Market related commands.
    """
    def __init__(self, bot):
        self.bot = bot

        self.esi = EsiClient(
            retry_requests=True,
            headers={'User-Agent': f'application: MercuryBot contact: {self.bot.config["bot"]["user_agent"]}'}
        )

    def type_from_name(self, name: str) -> Optional[dict]:
        """
        Returns a type ID from ESI for a given name.
            Return value of None indicates an invalid type name.
        :param name:
        :return:
        """
        post_op = self.bot.esi_app.op['post_universe_ids'](names=[name])
        response = self.esi.request(post_op)
        if 'inventory_types' not in response.data:
            return None
        return response.data['inventory_types'][0]

    @commands.command(aliases=['pc'])
    async def price_check(self, ctx, item_name):
        """
        Check the price of a given item.
            Returns Jita price data.
        """
        type_data = self.type_from_name(item_name)
        market_data = await get_market_data(type_data['id'])

        return await ctx.send(embed=await build_embed(type_data, market_data['resp']))


def setup(bot):
    bot.add_cog(Market(bot))


def teardown(bot):
    bot.remove_cog(Market)
