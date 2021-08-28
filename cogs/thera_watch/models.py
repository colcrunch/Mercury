from tortoise.models import Model
from tortoise import fields


class TheraEveSystem(Model):
    system_id = fields.BigIntField(pk=True, null=False)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.system_id})'


class TheraEveConstellation(Model):
    constellation_id = fields.BigIntField(pk=True, null=False)
    name = fields.CharField(max_length=255, null=False)

    def __str__(self):
        return f'{self.name} (id: {self.constellation_id}'


class TheraEveRegion(Model):
    region_id = fields.BigIntField(pk=True, null=False)
    name = fields.CharField(max_length=255)

    def __str__(self):
        return f'{self.name} (id: {self.region_id})'


class TheraChannel(Model):
    guild_id = fields.BigIntField(pk=True)
    channel_id = fields.BigIntField(null=False)
    systems = fields.ManyToManyField('models.TheraEveSystem', related_name='channels')
    constellations = fields.ManyToManyField('models.TheraEveConstellation', related_name='channels')
    regions = fields.ManyToManyField('models.TheraEveRegion', related_name='channels')

    def __str__(self):
        return f'Thera Channel for <{self.guild_id}>'


class LastThera(Model):
    last_thera = fields.BigIntField(null=False)

    def __str__(self):
        return f'Last Thera ID {self.last_thera}'
