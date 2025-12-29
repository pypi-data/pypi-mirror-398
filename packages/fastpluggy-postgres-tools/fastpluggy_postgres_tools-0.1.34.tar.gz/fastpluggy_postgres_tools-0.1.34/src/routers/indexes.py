from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy.core.menu.decorator import menu_entry

indexes_router = APIRouter(prefix="/indexes", tags=["postgres_indexes"])


def get_index_usage_statistics(db: Session, schema: str = None, threshold_unused: int = 10):
    """
    Get index usage statistics from the database
    """
    where_clause = "WHERE s.schemaname NOT IN ('pg_catalog', 'information_schema')"
    if schema:
        where_clause += f" AND s.schemaname = '{schema}'"
        
    query = text(f"""
        SELECT
          s.schemaname,
          s.relname AS table_name,
          s.indexrelname AS index_name,
          s.idx_scan,
          s.idx_tup_read,
          pg_size_pretty(pg_relation_size(s.indexrelid)) AS index_size,
          pg_relation_size(s.indexrelid) AS index_bytes,
          CASE WHEN s.idx_scan < {threshold_unused} THEN true ELSE false END AS is_unused
        FROM pg_stat_user_indexes s
        {where_clause}
        ORDER BY s.idx_scan ASC, pg_relation_size(s.indexrelid) DESC
    """)
    

    result = db.execute(query).mappings()
    return [dict(row) for row in result]


@indexes_router.get("")
async def get_indexes_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder),
    schema: str = None,
    threshold_unused: int = 10
):
    """
    Get the PostgreSQL index usage statistics view
    """
    # Get index usage statistics
    index_stats = get_index_usage_statistics(db, schema, threshold_unused)
    
    # Create a table for index usage statistics
    index_table = TableWidget(
        title="Index Usage Statistics",
        endpoint="/postgres/indexes",
        data=index_stats,
        description=f"Indexes with fewer than {threshold_unused} scans are highlighted as potentially unused."
    )
    
    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Index Usage Statistics",
        widgets=[
            index_table
        ]
    )