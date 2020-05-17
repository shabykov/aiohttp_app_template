from tortoise import exceptions

from api.base import serializers
from .models import RapidAgent


class UniqueUUIDField(serializers.UUIDField):

    def __init__(self, model_class, lookup_field='pk', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_class = model_class
        self.lookup_field = lookup_field

    async def to_internal_value(self, data):
        data = await super().to_internal_value(data)
        try:
            await self.model_class.get(**{self.lookup_field: data})
        except exceptions.DoesNotExist:
            return data

        raise serializers.ValidationError('RapidAgent with uid={data} is already exist.'.format(data=data))


class RapidAgentModelSerializer(serializers.ModelSerializer):
    uid = UniqueUUIDField(
        model_class=RapidAgent,
        lookup_field='uid'
    )

    class Meta:
        model = RapidAgent
        fields = (
            'id',
            'enabled',
            'address_space',
            'title',
            'uid',
            'sleep_time',
            'timezone',
            'http_proxy',
            'https_proxy',
            'token',
            'verify_path',
            'auth_path'
        )
        read_only_fields = (
            'id',
        )
