import aiohttp

import discord

from utils import get_json
from utils.loggers import get_logger

logger = get_logger(__name__)


async def get_market_data(type_id, region_id=None, station_id=None) -> dict:
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

    async with aiohttp.ClientSession() as session:
        return await get_json(session, url)


async def build_embed(type_data: dict, market_data: dict) -> discord.Embed:
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