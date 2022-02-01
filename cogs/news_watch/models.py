from tortoise.models import Model
from tortoise import fields


class NewsChannel(Model):
    guild_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField(null=False)
    news = fields.BooleanField(default=False)
    devblogs = fields.BooleanField(default=False)
    patchnotes = fields.BooleanField(default=False)

    def __str__(self):
        return f'News Channel for <{self.guild_id}>'


class PostedArticles(Model):
    article_id = fields.CharField(max_length=255, pk=True)