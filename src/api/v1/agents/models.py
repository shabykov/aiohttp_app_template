from tortoise import (
    fields, models
)


class RapidAgent(models.Model):
    id = fields.IntField(
        pk=True
    )

    enabled = fields.BooleanField(
        default=True
    )

    address_space = fields.CharField(
        max_length=255
    )

    title = fields.CharField(
        max_length=255
    )

    uid = fields.UUIDField(
        unique=True
    )

    sleep_time = fields.FloatField(
        default=1.0
    )

    timezone = fields.CharField(
        max_length=60
    )

    http_proxy = fields.CharField(
        max_length=255,
        null=True
    )

    https_proxy = fields.CharField(
        max_length=255,
        null=True
    )

    token = fields.CharField(
        max_length=500,
        null=True
    )

    verify_path = fields.CharField(
        max_length=500,
        null=True
    )

    auth_path = fields.CharField(
        max_length=500,
        null=True
    )

    class Meta:
        table = 'scans_rapidagent'
