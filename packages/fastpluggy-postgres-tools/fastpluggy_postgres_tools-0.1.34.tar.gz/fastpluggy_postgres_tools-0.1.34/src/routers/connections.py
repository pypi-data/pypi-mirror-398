from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy.core.menu.decorator import menu_entry

connections_router = APIRouter(prefix="/connections", tags=["postgres_connections"])


def get_active_connections(db: Session , min_duration: float = None, state: str = None):
    """
    Get active connections from the database
    """
    where_conditions = ["state <> 'idle'"]

    if min_duration:
        where_conditions.append(f"EXTRACT(EPOCH FROM (now() - query_start)) > {min_duration}")

    if state:
        where_conditions.append(f"state = '{state}'")

    where_clause = " AND ".join(where_conditions)

    query = f"""
        SELECT 
          pid,
          datname, 
          usename, 
          state, 
          backend_start, 
          query_start,
          EXTRACT(EPOCH FROM (now() - query_start)) AS duration_seconds,
          query
        FROM pg_stat_activity
        WHERE {where_clause}
        ORDER BY duration_seconds DESC
    """

    result = db.execute(text(query))
    # Convert SQLAlchemy Result to list of dicts for TableWidget compatibility
    return [dict(row) for row in result.mappings().all()]


def get_lock_contention(db_manager: Session):
    """
    Get lock contention information from the database
    """
    query = """
        SELECT 
          l.locktype, 
          l.mode, 
          l.granted, 
          a.query AS blocking_query, 
          a.pid AS blocking_pid,
          w.query AS waiting_query,
          w.pid AS waiting_pid,
          EXTRACT(EPOCH FROM (now() - w.query_start)) AS waiting_duration_seconds
        FROM pg_locks l
        JOIN pg_stat_activity a ON l.pid = a.pid
        JOIN pg_locks bl ON (l.database = bl.database AND l.relation = bl.relation)
        JOIN pg_stat_activity w ON bl.pid = w.pid
        WHERE NOT l.granted AND bl.granted
        ORDER BY waiting_duration_seconds DESC
    """

    result = db_manager.execute(text(query))
    # Convert SQLAlchemy Result to list of dicts for TableWidget compatibility
    return [dict(row) for row in result.mappings().all()]


@connections_router.get("")
async def get_connections_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder),
    min_duration: float = None,
    state: str = None
):
    """
    Get the PostgreSQL connections and locks view
    """
    # Create a connection manager for this request
    # Get active connections
    connections = get_active_connections(db, min_duration, state)

    # Get lock contention information
    locks = get_lock_contention(db)

    # Create a table for active connections
    connections_table = TableWidget(
        title="Active Connections",
        endpoint="/postgres/connections",
        data=connections,
        description="Active database connections and their current queries."
    )

    # Create a table for lock contention
    locks_table = TableWidget(
        title="Lock Contention",
        endpoint="/postgres/connections/locks",
        data=locks,
        description="Blocking and waiting queries causing lock contention."
    )

    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Connections & Locks",
        widgets=[
            connections_table,
            locks_table
        ]
    )
