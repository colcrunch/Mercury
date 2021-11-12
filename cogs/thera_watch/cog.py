import traceback

import discord
import aiohttp
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from esipy import EsiClient
from utils import get_json as get

from .models import *
from utils import checks
from utils.loggers import get_logger

logger = get_logger(__name__)


class TheraWatch(Cog, command_attrs=dict(hidden=True)):
    """
    Watch the EVE-Scout API for new Thera wormhole connections.
    """
    def __init__(self, bot):
        self.bot = bot

        self.TYPE_MODELS = {
            'region': TheraEveRegion,
            'system': TheraEveSystem,
            'constellation': TheraEveConstellation
        }

        self.last_thera = None
        self.channels = None

        self.esi = EsiClient(
            retry_requests=True,
            headers={'User-Agent': f'application: MercuryBot contact: {self.bot.config["bot"]["user_agent"]}'},
            raw_body_only=False
        )

        self.thera.start()

    def cog_unload(self):
        self.thera.cancel()

    async def load_channels(self):
        """
        Updates self.channels.
        :return:
        """
        systems = await TheraEveSystem.all()
        constellations = await TheraEveConstellation.all()
        regions = await  TheraEveRegion.all()
        self.channels = {
            'systems': {x.system_id: await x.channels.all() for x in systems},
            'constellations': {x.constellation_id: await x.channels.all() for x in constellations},
            'regions': {x.region_id: await x.channels.all() for x in regions}
        }

    async def update_channels(self, location_type: str, location):
        """
        Updates self.channels
        :param location: A location object
        :param location_type: string
        :return:
        """
        plural = f'{location_type}s'
        self.channels[plural][location.pk] = await location.channels.all()

    async def location_from_id(self, location_type: str, location_id: int):
        """
        Checks if the ID provided is valid for the type provided.
        :param location_type: string
        :param location_id: integer
        :return: Thera location model.
        """
        RANGES = {
            'region': [10000000, 13000000],
            'constellation': [20000000, 23000000],
            'system': [30000000, 33000000]
        }
        if not RANGES[location_type][0] <= location_id <= RANGES[location_type][1] and location_id is not 0:
            return -1

        if await self.TYPE_MODELS[location_type].filter(pk=location_id).exists():
            return await self.TYPE_MODELS[location_type].filter(pk=location_id).first()

        if location_id is not 0:
            post_op = self.bot.esi_app.op['post_universe_names'](ids=[location_id])
            response = self.esi.request(post_op)
            if location_type not in response.data[0]['category']:
                logger.debug(response.data)
                return -1
            model_kwargs = {
                f'{location_type}_id': response.data[0]['id'],
                'name': response.data[0]['name']
            }
            location = self.TYPE_MODELS[location_type](**model_kwargs)
            await location.save()
        else:
            # If we want to add all regions take care of this special case.
            location = self.TYPE_MODELS[location_type](name="All Regions", region_id=0)
            await location.save()

        return location

    async def location_from_name(self, location_type: str, location_name: str):
        """
        Returns the location object for a location using its name.
        :param location_type: string
        :param location_name: string
        :return: Thera location model.
        """
        plural = f'{location_type}s'

        # Check the DB for the item
        if await self.TYPE_MODELS[location_type].filter(name=location_name).exists():
            return await self.TYPE_MODELS[location_type].filter(name=location_name).first()

        if location_name.lower() != "all regions":
            # Get the system ID from ESI.
            post_op = self.bot.esi_app.op['post_universe_ids'](names=[location_name])
            response = self.esi.request(post_op)
            if plural not in response.data:
                return -1
            model_kwargs = {
                f'{location_type}_id': response.data[plural][0]['id'],
                'name': response.data[plural][0]['name']
            }
            location = self.TYPE_MODELS[location_type](**model_kwargs)
            await location.save()
        else:
            # If we want to add all regions take care of this special case.
            location = self.TYPE_MODELS[location_type](name="All Regions", region_id=0)
            await location.save()

        return location

    async def load_last(self):
        """
        Loads the last thera id seen.
        """
        last_thera = await LastThera.first()
        if last_thera is not None:
            self.last_thera = last_thera.last_thera

    @commands.command(aliases=['set_tc', 'tc'])
    @checks.is_admin()
    async def set_thera_channel(self, ctx):
        """
        Set the channel to post new thera connections into.
        """
        channels = await TheraChannel.filter(pk=ctx.guild.id)
        if len(channels) is not 0:
            return await ctx.send(f'Thera channel already set for `{ctx.guild.name}`. '
                                  f'To change it, please first unset the thera channel using '
                                  f'the `unset_thera_channel` command.')

        # Set the Thera Channel
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        channel = TheraChannel(guild_id=guild_id, channel_id=channel_id)
        await channel.save()

        return await ctx.send(f'{ctx.channel.mention} has been set as the '
                              f'Thera notifications channel for `{ctx.guild.name}`')

    @commands.command(aliases=['utc', 'delete_tc'])
    @checks.is_admin()
    async def unset_thera_channel(self, ctx):
        """
        This command unsets the channel used for thera connection posts.
            Note: This command can be run from any channel.
        """
        channels = await TheraChannel.filter(pk=ctx.guild.id)
        if len(channels) is 0:
            return await ctx.send(f'Thera channel not set for `{ctx.guild.name}`. '
                                  f'Use the `set_thera_channel` command from '
                                  f'the target channel to set it.')

        await channels[0].delete()
        # Update self.channels
        await self.load_channels()  # Reloading channels is easier on delete.

        return await ctx.send(f'Unset thera channel for `{ctx.guild.name}`')

    @commands.command(aliases=['ts', 'tsys'])
    @checks.is_admin()
    async def thera_system(self, ctx, action, *, system):
        """
        Add or remove watchlisted system.
            Both names and IDs are accepted.

            Valid Actions: add, remove
        """
        # Get the TheraChannel
        channel = await TheraChannel.filter(pk=ctx.guild.id).first()
        if channel is None:
            return await ctx.send(f'A thera notifications channel must be set up before you can manage watchlisted '
                                  f'locations. To set a thera notifications channel run the '
                                  f'`set_thera_channel` from the target channel.')

        # First check if we have a name or id
        name = not system.isnumeric()

        # Get / Validate the system ID
        system_obj = None
        if name:
            # Get the system ID from ESI.
            system_obj = await self.location_from_name('system', system)
            if system_obj == -1:
                return await ctx.send(f'The system name provided does not appear to be valid. Please '
                                      f'check the spelling and try again or try adding the system by ID.')
        else:
            system = int(system)
            system_obj = await self.location_from_id('system', system)
            if system_obj == -1:
                return await ctx.send(f'The system ID provided is not valid. Please check the ID and try again '
                                      f'or try adding the system by name.')

        if action.lower() == 'add':
            # Make sure we dont have the same system on the list twice.
            if system_obj in await channel.systems.all():
                return await ctx.send(f'System `{system}` already on watchlist.')

            # Add the system to the list and save the model.
            await channel.systems.add(system_obj)
        elif action.lower() == 'remove':
            # Make sure the system is on the list.
            if system_obj not in await channel.systems.all():
                return await ctx.send(f'System `{system}` is not on the watchlist.')

            await channel.systems.remove(system_obj)
        else:
            return await ctx.send(f'`{action}` is an invalid action. Valid actions are `add` or `remove`.')

        actioned = f'{action}ed'
        await self.update_channels('system', system_obj)

        return await ctx.send(f'Watchlist System `{system}` {actioned}.')

    @commands.command(aliases=['tcon'])
    @checks.is_admin()
    async def thera_constellation(self, ctx, action, *, constellation):
        """
        Add or remove a watchlisted constellation.
            Both names and IDs accepted.

            Valid Actions: add, remove
        """
        # Get the TheraChannel
        channel = await TheraChannel.filter(pk=ctx.guild.id).first()
        if channel is None:
            return await ctx.send(f'A thera notifications channel must be set up before you can manage watchlisted '
                                  f'locations. To set a thera notifications channel run the '
                                  f'`set_thera_channel` from the target channel.')

        name = not constellation.isnumeric()

        constellation_obj = None
        # Get / Validate constellation id
        if name:
            # Get the constellation ID from ESI
            constellation_obj = await self.location_from_name('constellation', constellation)
            if constellation_obj == -1:
                return await ctx.send(f'The constellation name provided does not appear to be valid. '
                                      f'Please check the spelling and try again or try adding using its ID.')
        else:
            constellation = int(constellation)
            constellation_obj = await self.location_from_id('constellation', constellation)
            if constellation_obj == -1:
                return await ctx.send(f'The constellation ID provided is not valid. Please check the ID and '
                                      f'try again or try adding using its name.')

        if action.lower() == 'add':
            if constellation_obj in await channel.constellations.all():
                return await ctx.send(f'Constellation `{constellation}` is already on watchlist.')
            await channel.constellations.add(constellation_obj)
        elif action.lower() == 'remove':
            if constellation_obj not in await channel.constellations.all():
                return await ctx.send(f'Constellation `{constellation}` is not on the watchlist.')
            await channel.constellations.remove(constellation_obj)
        else:
            return await ctx.send(f'`{action}` is an invalid action. Valid actions are `add` and `remove`')

        await self.update_channels('constellation', constellation_obj)

        return await ctx.send(f'Watchlist Constellation `{constellation}` {action}ed')

    @commands.command(aliases=['tr', 'treg'])
    @checks.is_admin()
    async def thera_region(self, ctx, action, *, region):
        """
        Add or remove a watchlisted region.
            Both names and IDs accepted.

            Valid Actions: add, remove
        """
        # Get the TheraChannel
        channel = await TheraChannel.filter(pk=ctx.guild.id).first()
        if channel is None:
            return await ctx.send(f'A thera notifications channel must be set up before you can manage watchlisted '
                                  f'locations. To set a thera notifications channel run the '
                                  f'`set_thera_channel` from the target channel.')

        name = not region.isnumeric()

        region_obj = None
        # Get / Validate region id
        if name:
            # Get the region ID from ESI
            region_obj = await self.location_from_name('region', region)
            if region_obj == -1:
                return await ctx.send(f'The region name provided does not appear to be valid. Please check '
                                      f'the spelling and try again or try adding it by ID.')
        else:
            region = int(region)
            region_obj = await self.location_from_id('region', region)
            if region_obj == -1:
                return await ctx.send(f'The region ID provided is not valid. Please check the ID and try again '
                                      f'or try adding it by name.')

        if action.lower() == 'add':
            if region_obj in await channel.regions.all():
                return await ctx.send(f'`{region}` already on the watchlist.')
            await channel.regions.add(region_obj)
        elif action.lower() == 'remove':
            if region_obj not in await channel.regions.all():
                return await ctx.send(f'`{region}` is not on the watchlist.')
            await channel.regions.remove(region_obj)
        else:
            return await ctx.send(f'`{action}` is an invalid action. Valid actions are `add` and `remove`.')

        await self.update_channels('region', region_obj)

        return await ctx.send(f'Watchlist Region `{region}` {action}ed.')

    @tasks.loop(seconds=60.0)
    async def thera(self):
        url = 'https://www.eve-scout.com/api/wormholes'
        try:
            async with aiohttp.ClientSession() as session:
                resp = await get(session, url)
            hole = list(resp['resp'])[0]
            hole_id = hole['id']
            source = hole['sourceSolarSystem']
            if self.last_thera == hole_id:
                pass    # Do nothing
            elif source['name'] == "Thera":
                self.last_thera = hole_id   # Ensure we keep track of the last thera id
                destination = hole['destinationSolarSystem']
                if destination['id'] in self.channels['systems']:
                    await self.process_hole(hole)
                elif destination['constellationID'] in self.channels['constellations']:
                    await self.process_hole(hole)
                elif destination['regionId'] in self.channels['regions'] or 0 in self.channels['regions']:
                    await self.process_hole(hole)

        except Exception as e:
            logger.warning("Exception occurred in thera loop.")
            logger.warning(traceback.format_exc())

    @thera.before_loop
    async def before_thera(self):
        # Wait until the bot is ready
        await self.bot.wait_until_ready()
        # Load channels and the last thera id.
        await self.load_channels()
        await self.load_last()

    @thera.after_loop
    async def on_thera_cancel(self):
        if self.thera.is_being_cancelled():
            if self.last_thera is not None:
                # Save last_thera.
                last_thera_obj = await LastThera.first()
                if last_thera_obj is None:
                    new_obj = LastThera(last_thera=self.last_thera)
                    await new_obj.save()
                else:
                    last_thera_obj.last_thera = self.last_thera
                    await last_thera_obj.save()

    async def process_hole(self, hole):
        """
        Build the embed for a given hole, and build a dict of which channels to send it to.
        :param hole:
        :return:
        """
        # Pull info from hole dict
        d_system = hole['destinationSolarSystem']
        hole_type = hole['destinationWormholeType']['name']
        if hole_type == 'K162':
            hole_type = hole['sourceWormholeType']['name']
        system = d_system['name']
        region = d_system['region']['name']
        c_id = d_system['constellationID']
        try:
            c_name = self.esi.request(
                self.bot.esi_app.op['get_universe_constellations_constellation_id'](constellation_id=c_id)
            ).data['name']
        except:
            print("oops")
        in_sig = hole['wormholeDestinationSignatureId']
        out_sig = hole['signatureId']

        # Build Discord Embed
        embed = discord.Embed(title="Thera Alert", color=discord.Color.blurple())
        embed.set_author(name='EVE-Scout', icon_url='http://games.chruker.dk/eve_online/graphics/ids/128/20956.jpg')
        embed.set_thumbnail(url='https://www.eve-scout.com/images/eve-scout-logo.png')

        embed.add_field(name='Region', value=region, inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='System (Constellation)', value=f'{system} ({c_name})', inline=True)

        embed.add_field(name='Signature (In - Out)', value=f'`{in_sig}` - `{out_sig}`', inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='Type', value=hole_type, inline=True)

        # Build channels for this hole
        send_channels = {'system': list(), 'constellation': list(), 'region': list()}

        if d_system['id'] in self.channels['systems']:
            send_channels['system'] += self.channels['systems'][d_system['id']]
        elif d_system['constellationID'] in self.channels['constellations']:
            send_channels['constellation'] += self.channels['constellation'][d_system['constellationId']]
        elif d_system['regionId'] in self.channels['regions'] or 0 in self.channels['regions']:
            if 0 in self.channels['regions']:   # Send to anyone that specified all regions
                send_channels['region'] += self.channels['regions'][0]
            if d_system['regionId'] in self.channels['regions']:    # Send to anyone that specified *this* region.
                send_channels['region'] += self.channels['regions'][d_system['regionId']]

        return await self.send_thera(embed, send_channels)

    async def send_thera(self, embed: discord.Embed, channels: dict):
        mentions = {'system': "@everyone", 'constellation': "@here", 'region': ""}

        for k, v in channels.items():
            for c in v:
                # Get channel
                channel = self.bot.get_channel(c.channel_id)
                await channel.send(content=mentions[k], embed=embed)


def setup(bot):
    bot.add_cog(TheraWatch(bot))


def teardown(bot):
    bot.remove_cog(TheraWatch)
