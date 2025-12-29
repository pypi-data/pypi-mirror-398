from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy.core.menu.decorator import menu_entry
from ..utils import execute_query_first

tables_router = APIRouter(prefix="/tables", tags=["postgres_tables"])


def get_table_statistics(db_manager: Session, schema: str = None, threshold_warn: int = 20, threshold_error: int = 40):
    """
    Get table statistics from the database including bloat estimation
    """
    where_clause = "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
    if schema:
        where_clause += f" AND schemaname = '{schema}'"

    query = f"""
        SELECT
          schemaname,
          relname AS table_name,
          n_live_tup AS live_rows,
          n_dead_tup AS dead_rows,
          ROUND(100.0 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2) AS bloat_percent,
          pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
          pg_total_relation_size(relid) AS total_bytes,
          last_vacuum,
          last_autovacuum,
          last_analyze,
          last_autoanalyze,
          CASE 
            WHEN ROUND(100.0 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2) > {threshold_error} THEN 'error'
            WHEN ROUND(100.0 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2) > {threshold_warn} THEN 'warning'
            ELSE 'ok'
          END AS status
        FROM pg_stat_user_tables
        {where_clause}
        ORDER BY bloat_percent DESC
    """

    result = db_manager.execute(text(query)).mappings()
    return [dict(row) for row in result]


def check_pgstattuple_extension(db_manager: Session):
    """
    Check if pgstattuple extension is installed
    """
    query = """
        SELECT COUNT(*) AS count
        FROM pg_extension
        WHERE extname = 'pgstattuple'
    """

    result = execute_query_first(db=db_manager,query_text=query)
    return result["count"] > 0


@tables_router.get("")
async def get_tables_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder),
    schema: str = None,
    threshold_warn: int = 20,
    threshold_error: int = 40
):
    """
    Get the PostgreSQL table statistics view
    """
    # Create a connection manager for this request

    # Check if pgstattuple extension is installed
    has_pgstattuple = check_pgstattuple_extension(db)

    # Get table statistics
    table_stats = get_table_statistics(db, schema, threshold_warn, threshold_error)

    # Create a table for table statistics
    table_widget = TableWidget(
        title="Table Statistics & Bloat",
        endpoint="/postgres/tables",
        data=table_stats,
        description=f"Tables with bloat > {threshold_warn}% are highlighted in yellow, > {threshold_error}% in red."
    )

    # Add a note about pgstattuple if not installed
    if not has_pgstattuple:
        table_widget.description += " For more accurate bloat estimation, install the pgstattuple extension."

    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Table Statistics & Bloat",
        widgets=[
            table_widget
        ]
    )
