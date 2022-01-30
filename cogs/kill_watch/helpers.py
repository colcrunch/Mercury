from datetime import datetime, timezone

import discord
from pyswagger.primitives import Datetime


def get_location_dict(esi_app, esi_client, system_id: int, names=False) -> dict:
    """
    Returns ESI data for a system_id.
    :param esi_app:
    :param esi_client:
    :param system_id:
    :param names:
    :return:
    """
    system = esi_client.request(
        esi_app.op['get_universe_systems_system_id'](system_id=system_id)
    )
    constellation_id = system.data['constellation_id']
    region = esi_client.request(
        esi_app.op['get_universe_constellations_constellation_id'](constellation_id=constellation_id)
    ).data
    if names:
        return {'system': system.data['name'], 'region': region['name']}
    return {'system_id': (system_id,), 'constellation_id': (constellation_id,), 'region_id': (region['region_id'],)}


def extract_mail_data(esi_app, esi_client, killmail: dict) -> dict:
    """
    Extracts all the relevant information from a killmail, returns a dict to be used when constructing
    the embed to be sent.
    :param esi_app:
    :param esi_client:
    :param killmail:
    :return:
    """
    # Get Basic Data
    final_blow = None
    for x in killmail['attackers']:
        if x['final_blow'] is True:
            final_blow = x
    victim = killmail['victim']
    ship = {'type_id': killmail['victim']['ship_type_id']}
    if type(killmail['killmail_time']) is str:
        time = datetime.strptime(killmail['killmail_time'], '%Y-%m-%dT%H:%M:%SZ')
    elif type(killmail['killmail_time']) is Datetime:
        time = killmail['killmail_time'].v
    if 'url' in killmail['zkb']:
        link = killmail['zkb']['url']
    else:
        link = f'https://zkillboard.com/kill/{killmail["killmail_id"]}/'
    location = get_location_dict(esi_app, esi_client, killmail['solar_system_id'], True)
    value = killmail['zkb']['totalValue']

    # Get info to be added to victim
    vic_corp_name = esi_client.request(
        esi_app.op['get_corporations_corporation_id'](corporation_id=victim['corporation_id'])
    ).data['name']
    victim['corporation_name'] = vic_corp_name

    vic_ally_name = None
    if 'alliance_id' in victim:
        vic_ally_name = esi_client.request(
            esi_app.op['get_alliances_alliance_id'](alliance_id=victim['alliance_id'])
        ).data['name']
    victim['alliance_name'] = vic_ally_name

    vic_char_name = None
    if 'character_id' in victim:
        vic_char_name = esi_client.request(
            esi_app.op['get_characters_character_id'](character_id=victim['character_id'])
        ).data['name']
    victim['character_name'] = vic_char_name

    # Get info to be added to final blow
    final_corp_name = None
    if 'corporation_id' in final_blow:
        final_corp_name = esi_client.request(
            esi_app.op['get_corporations_corporation_id'](corporation_id=final_blow['corporation_id'])
        ).data['name']
    final_blow['corporation_name'] = final_corp_name

    final_char_name = '<Corpless NPC>'
    if 'character_id' in final_blow:
        final_char_name = esi_client.request(
            esi_app.op['get_characters_character_id'](character_id=final_blow['character_id'])
        ).data['name']
    final_blow['character_name'] = final_char_name

    final_ally_name = None
    if 'alliance_id' in final_blow:
        final_ally_name = esi_client.request(
            esi_app.op['get_alliances_alliance_id'](alliance_id=final_blow['alliance_id'])
        ).data['name']
    final_blow['alliance_name'] = final_ally_name

    final_ship_name = None
    if 'ship_type_id' in final_blow:
        final_ship_name = esi_client.request(
            esi_app.op['get_universe_types_type_id'](type_id=final_blow['ship_type_id'])
        ).data['name']
    final_blow['ship_name'] =final_ship_name

    # Get and add ship name to ship dict.
    ship_name = esi_client.request(
        esi_app.op['get_universe_types_type_id'](type_id=ship['type_id'])
    ).data['name']
    ship['name'] = ship_name

    processed = {
        'final_blow': final_blow,
        'victim': victim,
        'ship': ship,
        'time': time,
        'link': link,
        'location': location,
        'value': value,
    }

    return processed


async def build_embed(extracted_data: dict) -> discord.Embed:
    """
    Builds a discord embed for the provided data.
        It is expected that the data passed in here is the result of passing a killmail to extract_mail_data.
    :param extracted_data:
    :return:
    """
    data = extracted_data
    if data['victim']['character_name'] is None:
        title_victim = f'{data["victim"]["corporation_name"]}'
        if data['victim']['alliance_name'] is not None:
            title_victim = f'{data["victim"]["corporation_name"]} ({data["victim"]["alliance_name"]})'
    else:
        title_victim = f'{data["victim"]["character_name"]} ({data["victim"]["corporation_name"]})'

    # Build Embed
    embed = discord.Embed(title=f'{title_victim} lost their {data["ship"]["name"]}', timestamp=data['time'])

    embed.set_author(name='zKillboard', icon_url='https://zkillboard.com/img/wreck.png', url=data['link'])
    embed.set_thumbnail(url=f'https://imageserver.eveonline.com/Type/{data["ship"]["type_id"]}_64.png')

    if data['final_blow']['character_name'] is None:
        embed.add_field(name='Final Blow', value=data['final_blow']['ship_name'], inline=True)
    else:
        embed.add_field(name='Final Blow', value=data['final_blow']['character_name'], inline=True)
    embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field

    if data['final_blow']['alliance_name'] is None:
        embed.add_field(name='Corp', value=data['final_blow']['corporation_name'], inline=True)
    else:
        embed.add_field(
            name='Corp',
            value=f'{data["final_blow"]["corporation_name"]} ({data["final_blow"]["alliance_name"]})',
            inline=True
        )

    embed.add_field(name='Value', value=f'{"{:,.2f}".format(data["value"])} ISK', inline=True)
    embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
    embed.add_field(name='Damage Taken', value="{:,.2f}".format(data['victim']['damage_taken']), inline=True)

    embed.add_field(name='System', value=data['location']['system'], inline=False)
    embed.add_field(name='Link', value=data['link'], inline=False)

    return embed