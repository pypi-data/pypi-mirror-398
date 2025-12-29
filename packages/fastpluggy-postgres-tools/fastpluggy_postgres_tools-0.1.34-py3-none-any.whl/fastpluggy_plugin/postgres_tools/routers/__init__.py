from fastapi import APIRouter, Depends

from fastpluggy.core.auth import require_authentication
from .sequences import sequences_router
from .db_size import db_size_router
from .indexes import indexes_router
from .tables import tables_router
from .queries import queries_router
from .connections import connections_router
from .vacuum import vacuum_router
from .replication import replication_router
from .alerts import alerts_router
from .dashboard import dashboard_router
from .extensions import extensions_router

postgres_tools_router = APIRouter()
postgres_tools_router.include_router(sequences_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(db_size_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(indexes_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(tables_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(queries_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(connections_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(vacuum_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(replication_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(alerts_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(dashboard_router, dependencies=[Depends(require_authentication)])
postgres_tools_router.include_router(extensions_router, dependencies=[Depends(require_authentication)])
