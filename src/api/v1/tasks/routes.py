from aiohttp import web
from tortoise.query_utils import Prefetch

from api.base.views.generics import (
    CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
)
from . import (
    models, serializers
)

api_v1_tasks_crud = web.RouteTableDef()


@api_v1_tasks_crud.view("/api/v1/tasks")
class TaskCreateListAPIView(CreateAPIView, ListAPIView):
    model_class = models.Task
    serializer_class = serializers.TaskModelSerializer


@api_v1_tasks_crud.view("/api/v1/tasks/{pk:\d+}")
class TaskUpdateRetrieveDeleteAPIView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    model_class = models.Task
    serializer_class = serializers.TaskModelSerializer


api_v1_nmap_scan_tasks_crud = web.RouteTableDef()


@api_v1_nmap_scan_tasks_crud.view("/api/v1/tasks/nmap-scan-tasks")
class NmapScanTaskCreateListAPIView(CreateAPIView, ListAPIView):
    model_class = models.NmapScanTask
    serializer_class = serializers.NmapScanTaskModelSerializer

    async def get_queryset(self):
        queryset = await self.model_class.all()
        return queryset


@api_v1_nmap_scan_tasks_crud.view("/api/v1/tasks/nmap-scan-tasks/{pk:\d+}")
class NmapScanTaskUpdateRetrieveDeleteAPIView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    model_class = models.NmapScanTask
    serializer_class = serializers.NmapScanTaskModelSerializer
