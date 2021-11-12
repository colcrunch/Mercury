from tortoise.models import Model
from tortoise import fields


class KillEveSystem(Model):
    system_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.system_id}'


class KillEveConstellation(Model):
    constellation_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.constellation_id}'


class KillEveRegion(Model):
    region_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.region_id})'


class KillEveCorporation(Model):
    corporation_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.corporation_id})'


class KillEveAlliance(Model):
    alliance_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.alliance_id})'


class KillEveCharacter(Model):
    character_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.alliance_id})'


class KillEveShipType(Model):
    type_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.type_id})'


class KillChannel(Model):
    guild_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField(null=False)
    systems = fields.ManyToManyField('models.KillEveSystem', related_name='channels')
    alliances = fields.ManyToManyField('models.KillEveAlliance', related_name='channels')
    constellation = fields.ManyToManyField('models.KillEveConstellation', related_name='channels')
    regions = fields.ManyToManyField('models.KillEveRegion', related_name='channels')
    corporations = fields.ManyToManyField('models.KillEveCorporation', related_name='channels')
    characters = fields.ManyToManyField('models.KillEveCharacter', related_name='channels')
    ships = fields.ManyToManyField('models.KillEveShipType', related_name='channels')

    def __str__(self):
        return f'Kill Channel for <{self.guild_id}>'
