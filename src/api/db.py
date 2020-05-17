from tortoise import Tortoise

async def init_db(app):
    await Tortoise.init(app['config'])

async def close_db(app):
    await Tortoise.close_connections()
