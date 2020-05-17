from aiohttp import web

from api.base.views.generics import (
    CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
)
from . import (
    models, serializers
)

api_v1_targets_crud = web.RouteTableDef()


@api_v1_targets_crud.view("/api/v1/targets")
class TargetCreateListAPIView(CreateAPIView, ListAPIView):
    model_class = models.Target
    serializer_class = serializers.TargetModelSerializer


@api_v1_targets_crud.view("/api/v1/targets/{pk:\d+}")
class TargetUpdateRetrieveDeleteAPIView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    model_class = models.Target
    serializer_class = serializers.TargetModelSerializer
