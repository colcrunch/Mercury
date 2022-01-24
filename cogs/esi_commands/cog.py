import traceback
import re
from datetime import datetime, timezone
from typing import Optional, Union
from urllib.parse import quote_plus

import discord
from discord.ext import commands
from discord.ext.commands import Cog
from esipy import EsiClient
from esipy.exceptions import APIException

from utils import strftdelta
from utils.loggers import get_logger

logger = get_logger(__name__)


class EsiCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.esi = EsiClient(
            retry_requests=True,
            headers={'User-Agent': f'application: MercuryBot contact: {self.bot.config["bot"]["user_agent"]}'}
        )

    def _get_esi_id(self, search: str, category: str, strict: bool) -> Union[list, int]:
        """
        Returns the ID for the specified query from ESI.
        :param search: string representing the search query
        :param category: the category to search against
        :param strict:
        :return: int ID if strict is true, otherwise list of IDs; -1 if not found
        """
        search_op = self.bot.esi_app.op['get_search'](
            categories=[category],
            search=search,
            strict=strict,
        )

        search_response = self.esi.request(search_op)

        if category not in search_response.data:
            return -1

        if strict:
            return search_response.data[category][0]
        else:
            return search_response.data[category]

    def _get_char_from_esi(self, char_id: int) -> Optional[dict]:
        """
        Gets public data for the specified character_id.
        :param char_id:
        :return:
        """
        char_op = self.bot.esi_app.op['get_characters_character_id'](
            character_id=char_id,
        )

        try:
            char_response = self.esi.request(char_op)
        except APIException as e:
            logger.error(f"Error getting char with id {char_id} from ESI! Error: {e}")
            logger.error(traceback.print_exc())
            return None

        return char_response.data

    def _get_alliance_from_esi(self, ally_id: int) -> Optional[dict]:
        """
        Gets public data for the specified alliance_id
        :param ally_id:
        :return:
        """
        ally_op = self.bot.esi_app.op['get_alliances_alliance_id'](
            alliance_id=ally_id,
        )

        try:
            ally_response = self.esi.request(ally_op)
        except APIException as e:
            logger.error(f"Error getting alliance with id {ally_id} from ESI! Error: {e}")
            logger.error(traceback.print_exc())
            return None

        return ally_response.data

    def _get_corporation_from_esi(self, corp_id: int) -> Optional[dict]:
        """
        Gets public data for the specified corporation_id
        :param corp_id:
        :return:
        """
        corp_op = self.bot.esi_app.op['get_corporations_corporation_id'](
            corporation_id=corp_id,
        )

        try:
            corp_response = self.esi.request(corp_op)
        except APIException as e:
            logger.error(f"Error getting corporation with id {corp_id} from ESI! Error: {e}")
            logger.error(traceback.print_exc())
            return None

        return corp_response.data

    def _get_system_from_esi(self, system_id: int) -> Optional[dict]:
        """
        Gets static system data from esi for the specified system_id
        :param system_id:
        :return:
        """
        sys_op = self.bot.esi_app.op['get_universe_systems_system_id'](
            system_id=system_id,
        )

        try:
            system_response = self.esi.request(sys_op)
        except APIException as e:
            logger.error(f"Error getting system with id {system_id} from ESI! Error: {e}")
            logger.error(traceback.print_exc())
            return None

        return system_response.data

    def _get_region_from_esi(self, region_id: int) -> Optional[dict]:
        """
        Gets static region data from esi for the specified region_id.
        :param region_id:
        :return:
        """
        reg_op = self.bot.esi_app.op['get_universe_regions_region_id'](
            region_id=region_id
        )

        try:
            region_response = self.esi.request(reg_op)
        except APIException as e:
            logger.error(f"Error getting region with id {region_id} from ESI! Error: {e}")
            logger.error(traceback.print_exc())
            return None

        return region_response.data

    def _get_constellation_from_esi(self, constellation_id: int) -> Optional[dict]:
        """
        Gets static constellation data from ESI for the specified constellation_id.
        :param constellation_id:
        :return:
        """
        const_op = self.bot.esi_app.op['get_universe_constellations_constellation_id'](
            constellation_id=constellation_id
        )

        try:
            constellation_response = self.esi.request(const_op)
        except APIException as e:
            logger.error(f"Error getting constellation with id {constellation_id} from ESI! Error: {e}")
            logger.error(traceback.print_exc())
            return None

        return constellation_response.data

    def _get_star_from_esi(self, star_id: int) -> Optional[dict]:
        """
        Gets the static star data from ESI for the given star_id.
        :param star_id:
        :return:
        """
        star_op = self.bot.esi_app.op['get_universe_stars_star_id'](
            star_id=star_id
        )

        try:
            star_response = self.esi.request(star_op)
        except APIException as e:
            logger.error(f"Error getting star with id {star_id} from ESI! Error: {a}")
            logger.error(traceback.print_exc())
            return None

        return star_response.data

    def _get_system_stats(self, system_id: int) -> Optional[dict]:
        """
        Returns the following data for a given system:
            - Jumps
            - Kills
            - Sovereignty
        :param system_id:
        :return:
        """
        # Get System Stats
        jump_op = self.bot.esi_app.op['get_universe_system_jumps']()
        kills_op = self.bot.esi_app.op['get_universe_system_kills']()
        sov_op = self.bot.esi_app.op['get_sovereignty_map']()

        try:
            jump_response = self.esi.request(jump_op)
            kills_response = self.esi.request(kills_op)
            sov_response = self.esi.request(sov_op)
        except APIException as e:
            logger.error(f"Error getting system stats from ESI! Error: {e}")
            logger.error(traceback.print_exc())
            return None

        ret = dict()
        ret['sov'] = None
        for sys in jump_response.data:
            if sys['system_id'] == system_id:
                ret['ship_jumps'] = sys['ship_jumps']
                break
        for sys in kills_response.data:
            if sys['system_id'] == system_id:
                ret['kills'] = sys
                break
        for sys in sov_response.data:
            if sys['system_id'] == system_id:
                if len(sys) == 1:
                    break
                ret['sov'] = sys
                break

        return ret

    @commands.command(aliases=('char', 'ch'))
    async def character(self, ctx, *, character_name: str):
        """
        Returns public data about the named character.
        """
        # Get ID from ESI
        char_id = self._get_esi_id(character_name, "character", True)
        if char_id == -1:
            return await ctx.send("Character not found. Please check your spelling and try again.")

        # Get Public data
        char = self._get_char_from_esi(char_id)
        if char is None:
            return await ctx.send("Something went wrong, please try again later.")

        corp = self._get_corporation_from_esi(char['corporation_id'])
        if corp is None:
            return await ctx.send("Something went wrong, please try again later.")

        urln = quote_plus(char['name'])

        urls = {
            'zkb': f'https://zkillboard.com/character/{char_id}/',
            'who': f'https://evewho.com/pilot/{urln}'
        }

        dob = char['birthday'].v
        age = datetime.now(timezone.utc) - dob

        embed = discord.Embed(title=f'{char["name"]} Character Info')
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png'))
        embed.set_thumbnail(url=f'https://imageserver.eveonline.com/Character/{char_id}_128.jpg')

        # Fields

        embed.add_field(name='Corporation', value=f'{corp["name"]} [{corp["ticker"]}]', inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        if corp['alliance_id'] is not None:
            ally = self._get_alliance_from_esi(corp['alliance_id'])
            if ally is None:
                return await ctx.send("Something went wrong, please try again later.")
            embed.add_field(name='Alliance', value=f'{ally["name"]} [{ally["ticker"]}]')
        embed.add_field(name='Birthday', value=dob.strftime("%a %d %b, %Y"), inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='Age', value=strftdelta(age), inline=True)
        embed.add_field(name='Additional Information', value=f'{urls["zkb"]}\n{urls["who"]}', inline=False)

        return await ctx.send(embed=embed)

    @commands.command(aliases=('corp', 'co'))
    async def corporation(self, ctx, *, corporation: str):
        """
        Returns public data about the specified corporation.
        """
        # Get ID
        corp_id = self._get_esi_id(corporation, "corporation", True)
        if corp_id == -1:
            return await ctx.send("Corporation not found. Please check your spelling and try again.")

        # Get Corp data
        corp = self._get_corporation_from_esi(corp_id)
        if corp is None:
            return await ctx.send("Something went wrong, please try again later.")

        ceo = self._get_char_from_esi(corp['ceo_id'])
        if ceo is None:
            return await ctx.send("Something went wrong, please try again later.")

        urls = {
            'zkb': f'https://zkillboard.com/corporation/{corp_id}/',
            'dotlan': f'https://evemaps.dotlan.net/corp/{corp_id}'
        }

        embed = discord.Embed(title=f'{corp["name"]} Corp Info', color=discord.Color.green())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png'))
        embed.set_thumbnail(url=f'https://imageserver.eveonline.com/Corporation/{corp_id}_128.png')

        # Fields

        embed.add_field(name='Ticker', value=f'[{corp["ticker"]}]', inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='Member Count', value=f'{corp["member_count"]}', inline=True)
        embed.add_field(name='CEO', value=f'{ceo["name"]}', inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        if corp['date_founded'] is not None:
            embed.add_field(name='Founded', value=corp["date_founded"].v.strftime("%a %d %b, %Y"), inline=True)
        if corp['alliance_id'] is not None:
            ally = self._get_alliance_from_esi(corp['alliance_id'])
            if ally is None:
                return ctx.send("Something went wrong, please try again later.")
            embed.add_field(name='Alliance', value=f'{ally["name"]} [{ally["ticker"]}]', inline=False)
        embed.add_field(name='Additional Information', value=f'{urls["zkb"]}\n{urls["dotlan"]}', inline=False)

        return await ctx.send(embed=embed)

    @commands.command(aliases=('ally',))
    async def alliance(self, ctx, *, alliance: str):
        """
        Returns public data about the specified alliance.
        """
        ally_id = self._get_esi_id(alliance, "alliance", True)
        if ally_id == -1:
            return await ctx.send("Alliance not found. Please check your spelling and try again.")

        ally = self._get_alliance_from_esi(ally_id)
        if ally is None:
            return await ctx.send("Something went wrong, please try again later.")

        found_corp = self._get_corporation_from_esi(ally['creator_corporation_id'])
        if found_corp is None:
            return await ctx.send("Something went wrong, please try again later.")

        founder = self._get_char_from_esi(ally['creator_id'])
        if founder is None:
            return await ctx.send("Something went wrong, please try again later.")

        exec_corp = None
        if 'executor_corporation_id' in ally:
            exec_corp = self._get_corporation_from_esi(ally['executor_corporation_id'])
            if exec_corp is None:
                return await ctx.send("Something went wrong, please try again later.")

        urls = {
            'zkb': f'https://zkillboard.com/alliance/{ally_id}/',
            'dotlan': f'https://evemaps.dotlan.net/alliance/{ally_id}'
        }

        title = f'{ally["name"]} Alliance Info'
        if exec_corp is None:
            title = title + ' (Closed)'

        embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png'))
        embed.set_thumbnail(url=f'https://imageserver.eveonline.com/Alliance/{ally_id}_128.png')

        # Fields

        embed.add_field(name='Ticker', value=f'[{ally["ticker"]}]', inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        if exec_corp is not None:
            embed.add_field(name='Executor Corp', value=f'{exec_corp["name"]} [{exec_corp["ticker"]}]', inline=True)

        embed.add_field(name='Founder', value=f'{founder["name"]}', inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='Founding Corp', value=f'{found_corp["name"]} [{found_corp["ticker"]}]', inline=True)

        embed.add_field(name='Founding Date', value=ally["date_founded"].v.strftime("%a %d %b, %Y"), inline=True)
        embed.add_field(name='Additional Information', value=f'{urls["zkb"]}\n{urls["dotlan"]}', inline=False)

        return await ctx.send(embed=embed)

    @commands.command()
    async def status(self, ctx):
        """
        Returns the current status of Tranquility
        """
        # Get ESI status
        status_op = self.bot.esi_app.op['get_status']()

        try:
            status_response = self.esi.request(status_op)
            status_response = status_response.data
        except APIException as e:
            embed = discord.Embed(title="Tranquility Status", color=discord.Color.red())
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png'))
            embed.set_thumbnail(url=f'https://en.wikipedia.org/wiki/CCP_Games#/media/File:CCP_Games_Logo.svg')

            embed.add_field(name="Status", value="*Offline*", inline=True)

            return await ctx.send(embed=embed)

        embed = discord.Embed(title="Tranquility Status", color=discord.Color.green())
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url_as(format='png'))
        embed.set_thumbnail(url=f'https://e.dotlan.net/images/Alliance/434243723_128.png')

        status = "Online"
        if "vip" in status_response:
            if status_response["vip"]:
                status = f"*{status} (VIP)*"

        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name="Player Count", value='{:,}'.format(status_response['players']), inline=True)

        embed.add_field(name="Server Version", value=status_response['server_version'], inline=True)
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(
            name="Uptime",
            value=strftdelta(datetime.now(timezone.utc) - status_response['start_time'].v),
            inline=True)

        return await ctx.send(embed=embed)

    @commands.command(aliases=('sys',))
    async def system(self, ctx, *, system_name: str):
        """
        Returns data about the specified system.
        """
        if re.match(r'[Jj]([0-9]{6})', system_name) or system_name == "Thera":
            return await ctx.send('System Information not available for wormhole systems.')

        # Get System ID
        sys_id = self._get_esi_id(system_name, 'solar_system', True)
        if sys_id == -1:
            return await ctx.send("System not found. Please check your spelling and try again.")

        # Get System Data
        system = self._get_system_from_esi(sys_id)
        if system is None:
            return await ctx.send("Something went wrong, please try again later.")

        if 'planets' in system:
            planets = len(system['planets'])
            moons = 0
            for planet in system['planets']:
                if 'moons' in planet:
                    moons += len(planet['moons'])
        else:
            planets = 0
            moons = 0

        star = self._get_star_from_esi(system['star_id'])

        constellation = self._get_constellation_from_esi(system['constellation_id'])
        if constellation is None:
            return await ctx.send("Something went wrong, please try again later.")

        region = self._get_region_from_esi(constellation['region_id'])
        if region is None:
            return await ctx.send("Something went wrong, please try again later.")

        stats = self._get_system_stats(sys_id)
        thumb_url = f'https://images.evetech.net/types/{star["type_id"]}/icon'
        if stats['sov'] is not None:
            if 'faction_id' in stats['sov']:
                thumb_url = f'https://images.evetech.net/corporations/{stats["sov"]["faction_id"]}/logo'
            elif 'alliance_id' in stats['sov']:
                thumb_url = f'https://images.evetech.net/alliances/{stats["sov"]["alliance_id"]}/logo'
            elif 'corporation_id' in stats['sov']:
                thumb_url = f'https://images.evetech.net/corporations/{stats["sov"]["corporation_id"]}/logo'

        dotlan = f'http://evemaps.dotlan.net/system/{sys_id}/'
        zkill = f'https://zkillboard.com/system/{sys_id}/'

        embed = discord.Embed(title=f'{system["name"]} System Information')
        embed.set_author(name='CCP Games',
                         icon_url='https://e.dotlan.net/images/Alliance/434243723_128.png')
        embed.set_thumbnail(url=thumb_url)

        # Fields

        embed.add_field(
            name='Sec Status / Class',
            value=f'{"{:.2f}".format(system["security_status"])} / {system["security_class"]}'
        )
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        embed.add_field(name='Region (Constellation)', value=f'{region["name"]} ({constellation["name"]})')

        embed.add_field(name='Planets / Moons', value=f'{planets} / {moons}')
        embed.add_field(name='\u200B', value='\u200B', inline=True)  # Empty Field
        if 'stargates' in system:
            embed.add_field(name='Stargates', value=str(len(system['stargates'])))

        embed.add_field(
            name='Stats (Last Hour)',
            value=f'**Jumps:** {stats["ship_jumps"]} \n'
                  f'**Ship Kills**: {stats["kills"]["ship_kills"]} \n'
                  f'**NPC Kills:** {stats["kills"]["npc_kills"]}\n'
                  f'**Pod Kills:** {stats["kills"]["pod_kills"]}',
            inline=False
        )
        embed.add_field(name='Additional Info', value=f'{dotlan} \n{zkill}')

        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(EsiCommands(bot))


def teardown(bot):
    bot.remove_cog(EsiCommands)