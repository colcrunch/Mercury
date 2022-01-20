import traceback
from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog
import aiohttp
from esipy import EsiClient

from utils.loggers import get_logger

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

    async def _get_market_data(self, type_id, region_id=None, station_id=None) -> dict:
        """
        Returns market data from the fuzzwork API for the given type_id at the given location.
            If no region or station id is provided default will be Jita 4-4 CNAP.
        :param type_id:
        :param region_id: The API will accept both region and system IDs for this field.
        :param station_id:
        :return:
        """
        location = "station=60003760"
        if station_id:
            location = f"station={station_id}"
        elif region_id:
            location = f"region={region_id}"

        url = f"https://market.fuzzwork.co.uk/aggregates/?{location}&types={type_id}"
        headers = {
            "User-Agent": f"application: Mercury contact: {self.bot.config['bot']['user_agent']}",
            "content-type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                resp = await response.json()
                resp_code = response.status
                return {'data': resp, "status_code": resp_code}

    async def build_embed(self, type_data: dict, market_data: dict) -> discord.Embed:
        """
        Builds and returns a discord Embed object for the given type and market data.
        :param type_data:
        :param market_data:
        :return:
        """
        type_name, type_id = (type_data["name"], type_data["id"])
        data = market_data[str(type_id)]

        # Header

        embed = discord.Embed(title=f"{type_name} Market Data")
        embed.set_author(
            name="Fuzzwork Market Data",
            url="https://market.fuzzwork.co.uk",
            icon_url="http://image.eveonline.com/Corporation/98072480_128.png"
        )
        embed.set_thumbnail(url=f'https://imageserver.eveonline.com/Type/{type_id}_64.png')

        # Fields

        embed.add_field(name="Sell Min", value="{:,.2f}".format(float(data['sell']['min'])), inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name="Sell Max", value="{:,.2f}".format(float(data['sell']['max'])), inline=True)

        embed.add_field(
            name='Sell Avg',
            value="{:,.2f} ISK".format(float(data['sell']['weightedAverage'])),
            inline=True
        )
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        if type_name.lower() == 'plex':
            embed.add_field(
                name='Monthly Sub Sell Avg',
                value='{:,.2f}'.format(round(float(data['sell']['weightedAverage']) * 500, 2)),
                inline=True
            )
        else:
            embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field

        embed.add_field(name='\u200B', value='\u200B', inline=False)  # Empty Field

        embed.add_field(name='Buy Min', value="{:,.2f}".format(float(data['buy']['min'])), inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='Buy Max', value="{:,.2f}".format(float(data['sell']['max'])), inline=True)

        embed.add_field(name='Buy Avg', value="{:,.2f}".format(float(data['sell']['weightedAverage'])), inline=True)
        if type_name.lower() == 'plex':
            embed.add_field(
                name='Monthly Sub Buy Avg',
                value='{:,.2f}'.format(round(float(data['buy']['weightedAverage']) * 500, 2)),
                inline=True
            )

        return embed

    @commands.command(aliases=['pc'])
    async def price_check(self, ctx, item_name):
        """
        Check the price of a given item.
            Returns Jita price data.
        """
        type_data = self.type_from_name(item_name)
        market_data = await self._get_market_data(type_data['id'])

        return await ctx.send(embed=await self.build_embed(type_data, market_data['data']))


def setup(bot):
    bot.add_cog(Market(bot))


def teardown(bot):
    bot.remove_cog(Market)
