from tortoise.models import Model
from tortoise import fields


class BotAdminRole(Model):
    guild_id = fields.BigIntField(pk=True)
    role_id = fields.BigIntField(null=False)

    def __str__(self):
        return f'BotAdminRole for Guild <{self.guild_id}>'
