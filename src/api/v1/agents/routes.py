from aiohttp import web

from api.base.views.generics import (
    CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
)

from . import (
    models, serializers
)

api_v1_agents_crud = web.RouteTableDef()

@api_v1_agents_crud.view("/api/v1/agents")
class RapidAgentCreateListAPIView(CreateAPIView, ListAPIView):
    model_class = models.RapidAgent
    serializer_class = serializers.RapidAgentModelSerializer


@api_v1_agents_crud.view("/api/v1/agents/{pk:\d+}")
class RapidAgentUpdateRetrieveDeleteAPIView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    model_class = models.RapidAgent
    serializer_class = serializers.RapidAgentModelSerializer
