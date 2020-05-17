from api.base import serializers

from api.v1.agents.models import RapidAgent
from api.v1.targets.models import Target

from .models import (
    Task, NmapScanTask
)
from ..agents.serializers import RapidAgentModelSerializer
from ..targets.serializers import TargetModelSerializer


class TaskModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = (
            'id',
            'type',
            'created',
            'updated'
        )
        read_only_fields = (
            'id',
            'created',
            'updated'
        )


class NmapScanTaskModelSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyField(
        model_class=Task
    )

    agent = serializers.PrimaryKeyField(
        model_class=RapidAgent
    )

    targets = serializers.PrimaryKeyField(
        model_class=Target
    )

    class Meta:
        model = NmapScanTask
        fields = (
            'id',
            'name',
            'description',
            'options',
            'enabled',
            'created',
            'updated',
            'task',
            'agent',
            'targets'
        )
        read_only_fields = (
            'id',
            'created',
            'updated'
        )

    async def to_representation(self, instance):
        self.fields['agent'] = RapidAgentModelSerializer()
        self.fields['targets'] = TargetModelSerializer()
        return await super().to_representation(instance)
