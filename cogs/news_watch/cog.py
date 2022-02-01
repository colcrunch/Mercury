import traceback
from datetime import datetime

import discord
import aiohttp
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from esipy import EsiClient
from webpreview import OpenGraph as og

from utils import checks, get_json
from utils.loggers import get_logger
from .models import *

logger = get_logger(__name__)


class NewsWatch(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

        self.esi = EsiClient(
            retry_requests=True,
            headers={'User-Agent': f'application: MercuryBot contact: {self.bot.config["bot"]["user_agent"]}'},
            raw_body_only=False,
        )

        self.channels = None
        self.news_task.start()

    def cog_unload(self):
        self.news_task.cancel()

    async def load_channels(self):
        """
        Loads self.channels
        :return:
        """
        news = await NewsChannel.filter(news=True)
        devblogs = await NewsChannel.filter(devblogs=True)
        patchnotes = await NewsChannel.filter(patchnotes=True)
        self.channels = {
            'news': news,
            'devblogs': devblogs,
            'patchnotes': patchnotes
        }

    async def _get_character_id_from_name(self, character_name: str) -> int:
        """
        Returns the character_id for a given character name
        :param character_name:
        :return:
        """

        id_op = self.bot.esi_app.op["get_search"](
            categories=['character'],
            search=character_name,
            strict=True
        )

        id_resp = self.esi.request(id_op)

        if 'character' not in id_resp.data:
            return -1

        return id_resp.data['character'][0]

    @commands.command(aliases=['nc', 'newschan', 'nchan', 'news_chan', 'n_chan'])
    @checks.is_admin()
    async def news_channel(self, ctx, action):
        """
        Sets or unsets the server's news feed channel.

        Valid Actions:
         - set (aliases: add)
         - unset (aliases: delete, remove)
         - edit

         The set and edit actions must be run from the intended channel, however,
         the unset action can be run from any channel.
        """
        action = action.lower()
        if action in ('set', 'add'):
            # Check if the news channel is already set for this guild.
            if await NewsChannel.filter(pk=ctx.guild.id).exists():
                return await ctx.send(f"The news channel for this server is already set! To change it"
                                      f"please run the `edit` action from the intended channel. To unset the news "
                                      f"channel run the `unset` action from any channel.")

            # Set the channel
            channel = await NewsChannel(guild_id=ctx.guild.id, channel_id=ctx.channel.id)
            await channel.save()

            return await ctx.send(f"{ctx.channel.mention} has been set as the news channel for `{ctx.guild.name}`")

        elif action in ('unset', 'delete', 'remove'):
            # Make sure the channel exists
            if not await NewsChannel.filter(pk=ctx.guild.id).exists():
                return await ctx.send(f"The news channel for this server is not yet set! To set it,"
                                      f"run the `set` action from the intended channel.")

            # Unset the channel
            channel = await NewsChannel.filter(pk=ctx.guild.id).first()
            await channel.delete()

            return await ctx.send(f"The news channel for `{ctx.guild.id}` has been unset.")

        elif action == 'edit':
            # Make sure the channel exists
            if not await NewsChannel.filter(pk=ctx.guild.id).exists():
                return await ctx.send(f"The news channel for this server is not yet set! To set it,"
                                      f"run the `set` action from the intended channel.")

            # Get the current channel.
            channel = await NewsChannel.filter(pk=ctx.guild.id).first()
            channel.channel_id = ctx.channel.id
            await channel.save()

            return await ctx.send(f"The news channel for this server has been updated. "
                                  f"New channel is {ctx.channel.mention}")
        else:
            return await ctx.send(f"{action} is not a valid action for this command. To see valid actions run"
                            f"the help command. (`/help news_channel`)")

    @commands.command(aliases=['news_track', 'nt', 'track_news', 'track_type', 'tt'])
    @checks.is_admin()
    async def news_type(self, ctx, action, *, news_type: str):
        """
        Sets the news channel for the current guild to track the specified type.

            Valid Actions:
            add, remove (aliases: delete)

            Valid Types are:
            news, devblogs (including plural variations), patchnotes (including plural variations), all
        """
        action = action.lower()

        # Check that the channel is set
        if not await NewsChannel.filter(pk=ctx.guild.id).exists():
            return await ctx.send(f"The news channel for this server is not yet set. To set it please run the "
                                  f"`news_channel` command from the intended channel.")

        channel = await NewsChannel.filter(pk=ctx.guild.id).first()
        bad_type = False

        if action == 'add':
            if news_type == 'news':
                channel.news = True
            elif news_type in ("patchnotes", "patch notes", "patch_notes", "patch-notes"):
                channel.patchnotes = True
            elif news_type in ('devblogs', 'dev blogs', 'dev-blogs', 'dev_blogs'):
                channel.devblogs = True
            elif news_type == 'all':
                channel.news = True
                channel.patchnotes = True
                channel.devblogs = True
            else:
                bad_type = True

            if not bad_type:
                await channel.save()
        elif action in ('remove', 'delete'):
            if news_type == 'news':
                channel.news = False
            elif news_type in ("patchnotes", "patch notes", "patch_notes", "patch-notes"):
                channel.patchnotes = False
            elif news_type in ('devblogs', 'dev blogs', 'dev-blogs', 'dev_blogs'):
                channel.devblogs = False
            elif news_type == 'all':
                channel.news = False
                channel.patchnotes = False
                channel.devblogs = False
            else:
                bad_type = True

            if not bad_type:
                await channel.save()
        else:
            return await ctx.send(f"{action} is not a valid action for this command. To see valid actions run "
                                  f"the help command. (`/help news_type`)")

        if bad_type:
            return await ctx.send(f"{news_type} is not a valid news type. To see valid news types run "
                                  f"the help command. (`/help news_type`)")

        await self.load_channels()
        return await ctx.send(f'The news channel for `{ctx.guild.name}` is now tracking `{news_type}` news articles.')

    @tasks.loop(seconds=300.0)
    async def news_task(self):
        dev_blog_url = "https://www.eveonline.com/rss/json/dev-blogs"
        news_url = "https://www.eveonline.com/rss/json/news"
        patch_url = "https://www.eveonline.com/rss/json/patch-notes"

        articles_to_save = []

        try:
            async with aiohttp.ClientSession() as session:
                devs = await get_json(session, dev_blog_url)
                news = await get_json(session, news_url)
                patches = await get_json(session, patch_url)

            resps = (devs['resp'], news['resp'], patches['resp'])

            # Get list of posted articles
            article_ids = await PostedArticles.all().values_list('article_id', flat=True)
            for resp in resps:
                for article in resp:
                    if article['id'] not in article_ids:
                        articles_to_save.append(await PostedArticles(article_id=article['id']))

                        await self.post(article, article['category'].replace('-', ''))
                    else:
                        continue

        except Exception as e:
            logger.error(f"Error occurred in the news task! Error: {e}")
            logger.error(traceback.print_exc())
        finally:
            await PostedArticles.bulk_create(articles_to_save)

    @news_task.before_loop
    async def before_news_task(self):
        # Wait for the bot to be ready
        await self.bot.wait_until_ready()
        # Load channels and articles
        await self.load_channels()

    @news_task.after_loop
    async def on_news_task_cancel(self):
        pass

    async def post(self, article, category):
        """
        Processes and posts the article to the channels defined in self.channels.
        :param article:
        :param category:
        :return:
        """
        title = article["title"].replace('"', '""')
        image = og(article['link'], ['og:image']).image
        author_id = await self._get_character_id_from_name(article['author'])
        if author_id == -1:
            author_id = 3019582
        author_img = f'https://imageserver.eveonline.com/Character/{author_id}_128.jpg'

        desc = article['description']
        if len(desc) > 1000:
            desc = article['description'][:1000].replace('__*', '***').replace('*__', '***')\
                                    .replace('__', '**').replace('###', '').replace('##', '')+'...'
        time = datetime.strptime(article['publishingDate'].strip('Z'), '%Y-%m-%dT%H:%M:%S')

        embed = discord.Embed(title=title, timestamp=time,
                              description=desc)
        embed.set_author(name=f'EVE Online {article["category"].title()}',
                         icon_url='https://www.ccpgames.com/img/ccp_logo.png')

        embed.add_field(name="Link", value=f'{article["link"]}')
        embed.set_image(url=image)
        embed.set_footer(text=f'{article["author"]}', icon_url=author_img)

        for channel in self.channels[category]:
            channel = self.bot.get_channel(channel.channel_id)
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(NewsWatch(bot))


def teardown(bot):
    bot.remove_cog(NewsWatch)