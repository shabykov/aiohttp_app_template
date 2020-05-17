import json

from aiohttp import web


class ListModelMixin(object):
    """
    List a queryset.
    """

    async def list(self, request):
        queryset = await self.get_queryset()

        # queryset = await self.filter_queryset(queryset)
        # page = await self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=queryset, many=True)
        return web.Response(
            body=json.dumps(await serializer.data),
            status=web.HTTPOk.status_code,
            content_type='application/json'
        )


class RetrieveModelMixin(object):
    """
    Retrieve a model instance.
    """

    async def retrieve(self, request):
        instance = await self.get_object()
        if not instance:
            return web.Response(
                status=web.HTTPNotFound.status_code
            )

        serializer = self.get_serializer(instance=instance)
        return web.Response(
            body=json.dumps(await serializer.data),
            status=web.HTTPOk.status_code,
            content_type='application/json'
        )


class DestroyModelMixin(object):
    """
    Destroy a model instance.
    """

    async def destroy(self, request):
        instance = await self.get_object()
        if not instance:
            return web.Response(
                status=web.HTTPNotFound.status_code
            )

        await  self.perform_destroy(instance)
        return web.Response(status=web.HTTPAccepted.status_code)

    async def perform_destroy(self, instance):
        await instance.delete()


class CreateModelMixin(object):
    """
    Create a model instance.
    """

    async def create(self, request):
        serializer = self.get_serializer(data=await request.json())
        if not await serializer.is_valid():
            return web.Response(
                body=json.dumps({"errors": serializer.errors}),
                status=web.HTTPBadRequest.status_code,
                content_type='application/json'
            )
        await self.perform_create(serializer)
        return web.Response(
            body=json.dumps(await serializer.data),
            status=web.HTTPCreated.status_code,
            content_type='application/json'
        )

    async def perform_create(self, serializer):
        await serializer.save()


class UpdateModelMixin(object):
    """
    Update a model instance.
    """

    async def update(self, request, partial=False):
        instance = await self.get_object()
        if not instance:
            return web.Response(
                status=web.HTTPNotFound.status_code
            )

        serializer = self.get_serializer(instance=instance, data=await request.json(), partial=partial)
        if not await serializer.is_valid():
            return web.Response(
                body=json.dumps({"errors": serializer.errors}),
                status=web.HTTPBadRequest.status_code,
                content_type='application/json'
            )
        await self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return web.Response(
            body=json.dumps(await serializer.data),
            status=web.HTTPOk.status_code,
            content_type='application/json'
        )

    async def perform_update(self, serializer):
        await serializer.save()

    async def partial_update(self, request):
        return await self.update(request, partial=True)
