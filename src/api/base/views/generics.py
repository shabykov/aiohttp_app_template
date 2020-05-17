from aiohttp import web
from tortoise import exceptions

from api.base.backends import (
    filter, pagination
)

from api.base.views.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
)


class GenericAPIView(web.View):
    """
    Concrete base view for generating API view.
    """

    model_class = None
    serializer_class = None

    # If you want to use object lookups other than pk, set 'lookup_field'.
    # For more complex lookup requirements override `get_object()`.
    lookup_field = 'pk'
    lookup_url_kwarg = None

    # The filter backend classes to use for queryset filtering
    filter_backends = filter.DEFAULT_FILTER_BACKENDS

    # The style to use for queryset pagination.
    pagination_class = pagination.DEFAULT_PAGINATION_CLASS

    async def get_queryset(self):
        return await self.model_class.all()

    async def get_object(self):
        lookup_url_kwargs = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.request.match_info[lookup_url_kwargs]}
        try:
            obj = await self.model_class.get(**filter_kwargs)
        except exceptions.DoesNotExist:
            obj = None

        return obj

    async def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = await backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer(self, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(**kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        return {
            'request': self.request,
            'view': self
        }


class CreateAPIView(CreateModelMixin, GenericAPIView):
    """
    Concrete view for creating a model instance.
    """

    async def post(self):
        return await self.create(self.request)


class ListAPIView(ListModelMixin, GenericAPIView):
    """
    Concrete view for listing a queryset.
    """

    async def get(self):
        return await self.list(self.request)


class RetrieveAPIView(RetrieveModelMixin, GenericAPIView):
    """
    Concrete view for retrieving a model instance.
    """

    async def get(self):
        return await self.retrieve(self.request)


class DestroyAPIView(DestroyModelMixin, GenericAPIView):
    """
    Concrete view for deleting a model instance.
    """

    async def delete(self):
        return await self.destroy(self.request)


class UpdateAPIView(UpdateModelMixin, GenericAPIView):
    """
    Concrete view for updating or patching a model instance.
    """

    async def put(self):
        return await self.update(self.request)

    async def patch(self):
        return await self.partial_update(self.request)
