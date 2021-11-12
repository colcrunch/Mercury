import traceback
import json
import asyncio

import discord
import websockets
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from esipy import EsiClient

from .models import *
from .helpers import *
from utils import checks
from utils.loggers import get_logger

logger = get_logger(__name__)


class KillWatch(Cog, command_attrs=dict(hidden=True)):
    """
    Listen to the zKillboard websocket for new kills.
    """
    def __init__(self, bot):
        self.bot = bot

        self.TYPE_MODELS = {
            'system': KillEveSystem,
            'constellation': KillEveConstellation,
            'region': KillEveRegion,
            'corporation': KillEveCorporation,
            'alliance': KillEveAlliance,
            'character': KillEveCharacter,
            'ship': KillEveShipType
        }

        self.channels = None

        self.esi = EsiClient(
            retry_requests=True,
            headers={'User-Agent': f'application: MercuryBot contact: {self.bot.config["bot"]["user_agent"]}'},
            raw_body_only=False
        )

        self.ws_task = asyncio.create_task(self.listen())

    def cog_unload(self):
        self.ws_task.cancel()

    async def load_channels(self):
        """
        Loads self.channels
        :return:
        """
        systems = await KillEveSystem.all()
        constellations = await KillEveConstellation.all()
        regions = await  KillEveRegion.all()
        corporations = await  KillEveCorporation.all()
        alliances = await  KillEveAlliance.all()
        characters = await  KillEveCharacter.all()
        ships = await  KillEveShipType.all()
        self.channels = {
            'systems': {x.system_id: await x.channels.all() for x in systems},
            'constellations': {x.constellation_id: await x.channels.all() for x in constellations},
            'regions': {x.region_id: await x.channels.all() for x in regions},
            'corporations': {x.corporation_id: await x.channels.all() for x in corporations},
            'alliances': {x.alliance_id: await x.channels.all() for x in alliances},
            'characters': {x.character_id: await x.channels.all() for x in characters},
            'ships': {x.type_id: await x.channels.all() for x in ships},
        }

    async def update_channels(self, id_type: str, id_obj):
        """
        Updates self.channels
        :param id_type:
        :param id_obj:
        :return:
        """
        plural = f'{id_type}s'
        self.channels[plural][id_obj.pk] = await id_obj.channels.all()

    async def item_from_name(self, track_type, to_track):
        """
        Gets or creates an item from name.
        :param track_type:
        :param to_track:
        :return:
        """
        plural = f'{track_type}s'

        # Check if the item is already in the db and return it
        if await self.TYPE_MODELS[track_type].filter(name=to_track).exists():
            return await self.TYPE_MODELS[track_type].filter(name=to_track).first()

        # If its not in the database, get info from ESI and save a DB record for it.
        cat = 'inventory_types' if track_type == 'ship' else plural

        post_op = self.bot.esi_app.op['post_universe_ids'](names=[to_track])
        response = self.esi.request(post_op)
        if cat not in response.data:
            logger.debug(response.data)
            return -1
        model_kwargs = {
            f'{"type" if track_type == "ship" else track_type}_id': response.data[cat][0]['id'],
            'name': response.data[cat][0]['name']
        }
        item = self.TYPE_MODELS[track_type](**model_kwargs)
        await item.save()

        return item

    async def item_from_id(self, track_type, to_track):
        """
        Gets or creates an item from id.
        :param track_type:
        :param to_track:
        :return:
        """
        RANGES = {
            'region': [10000000, 13000000],
            'constellation': [20000000, 23000000],
            'system': [30000000, 33000000],
            'alliance': [99000000, 2100000000],
            'corporation': [98000000, 99000000],
            'character': [90000000, 98000000],
            'alt_char_corp': [100000000, 2100000000],
            'alt_char': [2100000000, 2147483647],
            'ship': [0, 10000]
        }
        # Check that the id is valid
        if track_type in ('corporation', 'alliance'):
            if (
                not RANGES[track_type][0] <= to_track <= RANGES[track_type][1] and
                not RANGES['alt_char_corp'][0] <= to_track <= RANGES['alt_char_corp'][1]
            ):
                return -1
        elif track_type == 'character':
            if (
                not RANGES[track_type][0] <= to_track <= RANGES[track_type][1] and
                not RANGES['alt_char_corp'][0] <= to_track <= RANGES['alt_char_corp'][1] and
                not RANGES['alt_char'] <= to_track <= RANGES['alt_char'][1]
            ):
                return -1
        else:
            if not RANGES[track_type][0] <= to_track <= RANGES[track_type][1]:
                return -1

        # If its already in the database, get and return the item.
        if await self.TYPE_MODELS[track_type].filter(pk=to_track).exists():
            return await self.TYPE_MODELS[track_type].filter(pk=to_track).first()

        # If its not in the database already, pull it from ESI and create a record.
        cat = 'inventory_type' if track_type == 'ship' else track_type

        post_op = self.bot.esi_app.op['post_universe_names'](ids=[to_track])
        response = self.esi.request(post_op)
        if cat not in response.data[0]['category']:
            logger.debug(response.data)
            return -1
        model_kwargs = {
            f'{"type" if track_type == "ship" else track_type}_id': response.data[0]['id'],
            'name': response.data[0]['name']
        }
        item = self.TYPE_MODELS[track_type](**model_kwargs)
        await item.save()

        return item

    async def get_item(self, track_type, to_track):
        name = not to_track.isnumeric()

        if name:
            item_object = await self.item_from_name(track_type, to_track)
        else:
            item_object = await self.item_from_id(track_type, to_track)

        return item_object

    @commands.command(aliases=['track_id', 'track'])
    @checks.is_admin()
    async def tracking_id(self, ctx, action, track_type, *, to_track):
        """
        Adds or removes the specified entity to the guilds kill channel for tracking.
            IDs and Names are valid for entities.

            Valid Actions:
            add, remove (aliases: delete)

            Valid Types are:
            system, constellation, region, alliance, corporation, character, ship
        """
        action = action.lower()
        # Get Kill Channel
        channel = await KillChannel.filter(pk=ctx.guild.id).first()
        if channel is None:
            return await ctx.send(f'A kill feed channel must be set up before you can manage tracked'
                                  f'entities. To set a kill feed channel run the'
                                  f'`set_kill_channel` command from the target channel.')

        TYPES = {
            'system': channel.systems,
            'constellation': channel.constellation,
            'region': channel.regions,
            'alliance': channel.alliances,
            'corporation': channel.corporations,
            'character': channel.characters,
            'ship': channel.ships
        }

        # Ensure the type is valid
        if track_type not in TYPES.keys():
            return await ctx.send(f'`{track_type}` is not a valid type. Please chose from one of the following:\n '
                                  f'{", ".join(TYPES.keys())}')

        # First check if we have a name or id
        item_object = await self.get_item(track_type, to_track)

        if item_object == -1:
            return await ctx.send(f'`{to_track}` is not a valid name or ID for type `{track_type}`,'
                                  f' please check it and try again.')

        if action == 'add':
            await TYPES[track_type].add(item_object)
            await self.update_channels(track_type, item_object)

            return await ctx.send(f'Kills for {item_object.name} are now being tracked!')
        elif action == 'remove' or action == 'delete':
            await TYPES[track_type].remove(item_object)
            await self.update_channels(track_type, item_object)

            return await ctx.send(f'No longer tracking kills for {item_object.name}')
        else:
            return await ctx.send(f'`{action}` is not a valid action.')

    @commands.command(aliases=['kc', 'kchan', 'killchan', 'kill_chan'])
    @checks.is_admin()
    async def kill_channel(self, ctx, action):
        """
        Sets or unsets the server's kill feed channel.

        Valid Actions:
         - set (aliases: add)
         - unset (aliases: delete, remove)
         - edit

         The set and edit actions must be run from the intended channel, however,
         the unset action can be run from any channel.
        """
        action = action.lower()
        if action in ('set', 'add'):
            # Check if kill channel is already set...
            if await KillChannel.filter(pk=ctx.guild.id).exists():
                return await ctx.send(f'The kill feed channel for this server is already set! To change it '
                                      f'please run the `edit` action from the intended channel. To unset the kill '
                                      f'feed channel run the `unset` action from any channel.')

            # Set the channel
            channel = await KillChannel(guild_id=ctx.guild.id, channel_id=ctx.channel.id)
            await channel.save()

            return await ctx.send(f'{ctx.channel.mention} set as the kill feed channel for `{ctx.guild.name}`')

        elif action in ('unset', 'delete', 'remove'):
            # Make sure the channel is set.
            if not await KillChannel.filter(pk=ctx.guild.id).exists():
                return await ctx.send(f'The kill feed channel for this server is not yet set! To set it, '
                                      f'run the `set` action from the intended channel.')

            # Unset the channel
            channel = await KillChannel.filter(pk=ctx.guild.id).first()
            await channel.delete()

            return await ctx.send(f'The kill feed channel for `{ctx.guild.name}` has been unset.')

        elif action == 'edit':
            # Make sure the channel is set
            if not await KillChannel.filter(pk=ctx.guild.id).exists():
                return await ctx.send(f'The kill feed channel for this server is not yet set! To set it, '
                                      f'run the `set` action from the intended channel.')

            # Get the current channel
            channel = await KillChannel.filter(pk=ctx.guild.id).first()
            channel.channel_id = ctx.channel.id
            await channel.save()

            return await ctx.send(f'The kill feed channel for this server has been updated. '
                                  f'New channel is {ctx.channel.mention}')

        else:
            return await ctx.send(f'`{action}` is not a valid action for this command. To see valid actions run'
                                  f'the help command. (`/help kill_channel`)')

    async def listen(self):
        """
        Subscribe to the killstream on zKill's websocket
        :return:
        """
        if self.channels is None:
            await self.load_channels()
        uri = 'wss://zkillboard.com/websocket/'

        ws = await websockets.connect(uri, ssl=True)
        await ws.send(json.dumps({'action': 'sub', 'channel': 'killstream'}))

        while 'KillWatch' in self.bot.cogs:
            if not ws.open:
                logger.info("Not connected to zKill; attempting to connect...")
                try:
                    ws = await websockets.connect(uri, ssl=True)
                    await ws.send(json.dumps({'action': 'sub', 'channel': 'killstream'}))

                except Exception as e:
                    logger.error("Error connecting to zKill's websocket.")
                    logger.error(traceback.format_exc())
            try:
                async for message in ws:
                    if message is not None:
                        await self.process_killmail(json.loads(message))
            except asyncio.CancelledError:
                pass    # We dont want to log this
            except Exception as e:
                logger.error(f"Error receiving message from zKill: {e}")
                logger.error(traceback.format_exc())
            finally:
                await ws.close()

    async def process_killmail(self, message: dict):
        """
        Decides whether or not to send the killmail to discord, and which channels to send to.
        :param message:
        :return:
        """
        mail_ids = {
            'alliance_id': [],
            'character_id': [],
            'corporation_id': [],
            'ship_type_id': []
        }
        for attacker in message['attackers']:
            for key in attacker:
                if 'id' in key and 'faction' not in key and 'weapon' not in key:
                    mail_ids[key].append(attacker[key])
        for key in message['victim']:
            if 'id' in key and 'faction' not in key:
                mail_ids[key].append(message['victim'][key])
        mail_ids = {
            **mail_ids,
            **get_location_dict(
                self.bot.esi_app,
                self.esi,
                message['solar_system_id']
            )
        }

        # Build channel set
        send_channels = set()

        for key in mail_ids:
            channel_key = 'ships' if key == 'ship_type_id' else f'{key.strip("_id")}s'
            for item_id in mail_ids[key]:
                if item_id in self.channels[channel_key]:
                    send_channels.update([(x, channel_key) for x in self.channels[channel_key][item_id]])

        if len(send_channels) != 0:
            await self.send_kill(message, send_channels)

    async def send_kill(self, kill_mail: dict, send_channels: set):
        """
        Builds and sends embed for the given killmail.
        :param kill_mail:
        :param send_channels:
        :return:
        """
        data = extract_mail_data(
            self.bot.esi_app,
            self.esi,
            kill_mail
        )

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

        embed.add_field(name='Value', value=f'{data["value"]} ISK', inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='Damage Taken', value=data['victim']['damage_taken'], inline=True)

        embed.add_field(name='System', value=data['location']['system'], inline=False)
        embed.add_field(name='Link', value=data['link'], inline=False)

        # Send to channels
        for channel_tuple in send_channels:
            channel = channel_tuple[0]
            kill_key = 'ship_type_id' if channel_tuple[1] == 'ships' else channel_tuple[1].replace('s', '_id')
            KEY_METHODS = {
                'alliances': channel.alliances,
                'corporations': channel.corporations,
                'characters': channel.characters,
                'ships': channel.ships
            }
            # Check if we are watching for char/corp/ally/ship of victim
            color = discord.Color.green()
            if await KEY_METHODS[channel_tuple[1]].filter(pk=data['victim'][kill_key]).exists():
                color = discord.Color.red()

            embed.colour = color

            # Get the channel
            channel = self.bot.get_channel(channel.channel_id)
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(KillWatch(bot))


def teardown(bot):
    bot.remove_cog(KillWatch)
