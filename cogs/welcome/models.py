from tortoise.models import Model
from tortoise import fields


class WelcomeChannel(Model):
    guild_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField(null=False)

    def __str__(self):
        return f'Welcome Channel for <{self.guild_id}>'


class WelcomeMessage(Model):
    guild_id = fields.BigIntField(pk=True)
    message = fields.TextField()

    def __str__(self):
        return f'Welcome Message for <{self.guild_id}>'
