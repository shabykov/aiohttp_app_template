from tortoise import (
    fields, models
)

class Target(models.Model):
    id = fields.IntField(
        pk=True,
    )

    description = fields.TextField(
        null=True
    )

    targets = fields.TextField()
    excluded_targets = fields.TextField()

    created = fields.DatetimeField(
        null=True, auto_now_add=True
    )

    class Meta:
        table = 'scans_targets'
