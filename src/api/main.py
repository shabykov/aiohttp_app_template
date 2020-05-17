from aiohttp import web

from api.base.middlewares import (
    session, auth
)

from api.db import (
    init_db, close_db
)

from api.settings import config
from api.v1.agents.routes import api_v1_agents_crud
from api.v1.targets.routes import api_v1_targets_crud
from api.v1.tasks.routes import (
    api_v1_tasks_crud,
    api_v1_nmap_scan_tasks_crud
)

def init_app():
    app = web.Application()
    app['config'] = config

    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)

    app.router.add_routes(api_v1_agents_crud)
    app.router.add_routes(api_v1_targets_crud)
    app.router.add_routes(api_v1_tasks_crud)
    app.router.add_routes(api_v1_nmap_scan_tasks_crud)

    app.middlewares.append(session)
    app.middlewares.append(auth)

    return app


if __name__ == '__main__':
    application = init_app()
    web.run_app(application)
