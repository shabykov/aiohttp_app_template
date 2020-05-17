from api.base import serializers

from .models import Target


class TargetModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = (
            'id',
            'description',
            'targets',
            'excluded_targets',
            'created'
        )
        read_only_fields = (
            'id',
            'created'
        )
