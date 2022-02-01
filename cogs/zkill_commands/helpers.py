import aiohttp
from typing import Optional
from datetime import datetime

from discord import Embed

from utils import get_json
from utils.loggers import get_logger

logger = get_logger(__name__)


async def get_char_stats_from_zkill(char_id: int) -> Optional[dict]:
    """
    Returns a character's zkill stats, or None if the character does not have any.
    :param char_id:
    :return:
    """
    zkill_stats_url = f"https://zkillboard.com/api/stats/characterID/{char_id}/"

    async with aiohttp.ClientSession() as session:
        zkill_stats = await get_json(session, zkill_stats_url)

    zkill_data = zkill_stats['resp']

    if 'shipsDestroyed' not in zkill_data:
        return None

    month_stats = None
    if 'months' in zkill_data:
        month = datetime.utcnow().strftime('%Y%m')
        if month in zkill_data['months']:
            k = zkill_data['months'][month].get('shipsDestroyed', 0)
            l = zkill_data['months'][month].get('shipsLost', 0)
            month_stats = {'kills': k, 'losses': l}

    ret = {
        "kills": zkill_data['shipsDestroyed'],
        "deaths": zkill_data['shipsLost'],
        "iskDestroyed": zkill_data['iskDestroyed'],
        "iskLost": zkill_data['iskLost'],
        "gangRatio": zkill_data['gangRatio'],
        "dangerRatio": zkill_data['dangerRatio'],
        "month_stats": month_stats
    }
    return ret


async def build_embed(stats: dict, character_name: str, character_id: int) -> Embed:
    """
    Returns an embed for the threat command.
    :param stats: zkill stats returned from a call to get_char_stats_from_zkill
    :param char_name: name of the character
    :param character_id: id of the character
    :return:
    """

    monthly_kdr = "No Kills Yet"
    if stats["month_stats"] is not None:
        monthly_kdr = (
            f"Kills: {stats['month_stats']['kills']} \n"
            f"Losses: {stats['month_stats']['losses']} \n"
            f"KDR: {round(stats['month_stats']['kills'] / max(stats['month_stats']['losses'], 1), 2)}"
        )

    embed = Embed(title=f'{character_name} Threat Analysis')
    embed.set_author(name='zKillboard', url=f'http://zkillboard.com/character/{character_id}/',
                     icon_url='http://zkillboard.com/img/wreck.png')
    embed.set_thumbnail(url=f'https://imageserver.eveonline.com/Character/{character_id}_128.jpg')

    # Fields

    embed.add_field(name='Gang Ratio', value=f'{stats["gangRatio"]}%')
    embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
    embed.add_field(name='Danger Ratio', value=f'{stats["dangerRatio"]}%')

    embed.add_field(name='KDR All Time', value=f'Kills: {stats["kills"]} \nLosses: {stats["deaths"]} \n'
                                               f'KDR: {round(stats["kills"]/stats["deaths"], 2)}')
    embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field

    embed.add_field(name='KDR Month', value=monthly_kdr)

    embed.add_field(name='ISK Efficiency', value=(
        f'ISK Killed: {"{:,}".format(stats["iskDestroyed"])} \n'
        f'ISK Lost: {"{:,}".format(stats["iskLost"])} \n'
        f'Efficiency: {round((1.0 - (stats["iskLost"] / stats["iskDestroyed"])) * 100, 1)}%'))

    return embed
