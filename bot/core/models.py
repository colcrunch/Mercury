from django.db import models


# Create your models here.
class BotAdminRole(models.Model):
    guild_id = models.BigIntegerField(primary_key=True)
    role_id = models.BigIntegerField(null=False)

    def __str__(self):
        return f"BotAdminRole for Guild <{self.guild_id}>"

    class Meta:
        verbose_name = "Bot Admin Role"
        verbose_name_plural = "Bot Admin Roles"
        default_permissions = (())
