from api.v1.agents.models import RapidAgent
from api.v1.targets.models import Target

from tortoise import (
    fields, models
)

class Task(models.Model):
    id = fields.IntField(
        pk=True,
    )

    type = fields.CharField(
        max_length=255
    )

    created = fields.DatetimeField(
        null=True, auto_now_add=True
    )

    updated = fields.DatetimeField(
        null=True, auto_now=True
    )

    class Meta:
        table = 'scans_task'


class NmapScanTask(models.Model):
    id = fields.IntField(
        pk=True
    )

    name = fields.CharField(
        max_length=255
    )

    description = fields.TextField(
        null=True
    )

    options = fields.CharField(
        max_length=255
    )

    enabled = fields.BooleanField(
        default=True
    )

    created = fields.DatetimeField(
        null=True, auto_now_add=True
    )

    updated = fields.DatetimeField(
        null=True, auto_now=True
    )

    task: fields.OneToOneRelation[Task] = fields.OneToOneField(
        model_name='models.Task',
        related_name='nmap_scan_task'
    )

    agent: fields.ForeignKeyRelation[RapidAgent] = fields.ForeignKeyField(
        model_name='models.RapidAgent',
        related_name='nmap_scan_task'
    )

    targets: fields.ForeignKeyRelation[Target] = fields.ForeignKeyField(
        model_name='models.Target',
        related_name='nmap_scan_task'
    )

    class Meta:
        table = 'scans_nmapscantask'
