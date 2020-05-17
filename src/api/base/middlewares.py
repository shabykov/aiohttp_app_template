from aiohttp import web

@web.middleware
async def auth(request, handler):
    #TODO
    return await handler(request)

@web.middleware
async def session(request, handler):
    #TODO
    return await handler(request)

