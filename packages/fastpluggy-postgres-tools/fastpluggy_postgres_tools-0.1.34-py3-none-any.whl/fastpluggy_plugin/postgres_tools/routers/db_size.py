from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy_plugin.ui_tools.extra_widget.display.card import CardWidget
from fastpluggy.core.menu.decorator import menu_entry

db_size_router = APIRouter(prefix="/db/size", tags=["postgres_db_size"])


def get_total_db_size(db: Session):
    query = text("""
        SELECT 
          pg_size_pretty(pg_database_size(current_database())) AS total_size,
          pg_database_size(current_database()) AS total_bytes
    """)
    
    result = db.execute(query).mappings().first()
    return {
        "total_size": result["total_size"],
        "total_bytes": result["total_bytes"]
    }


def get_schema_sizes(db: Session, include_system: bool = False):
    where_clause = ""
    if not include_system:
        where_clause = "WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'"
        
    query = text(f"""
        SELECT 
          nspname AS schema, 
          pg_size_pretty(SUM(pg_total_relation_size(c.oid))) AS size,
          SUM(pg_total_relation_size(c.oid)) AS bytes
        FROM pg_class c
        JOIN pg_namespace n ON c.relnamespace = n.oid
        {where_clause}
        GROUP BY nspname
        ORDER BY SUM(pg_total_relation_size(c.oid)) DESC
    """)
    
    result = db.execute(query).mappings()
    return [dict(row) for row in result]


def get_tablespace_sizes(db: Session):
    query = text("""
        SELECT 
          spcname,
          pg_size_pretty(pg_tablespace_size(spc.oid)) AS size,
          pg_tablespace_size(spc.oid) AS bytes
        FROM pg_tablespace spc
    """)
    
    result = db.execute(query).mappings()
    return [dict(row) for row in result]


def get_largest_tables(db: Session, limit: int = 20, schema: str = None):
    where_clause = ""
    if schema:
        where_clause = f"WHERE schemaname = '{schema}'"
        
    query = text(f"""
        SELECT 
          schemaname,
          relname,
          pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
          pg_size_pretty(pg_relation_size(relid)) AS table_size,
          pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size,
          pg_total_relation_size(relid) AS total_bytes
        FROM pg_stat_user_tables
        {where_clause}
        ORDER BY pg_total_relation_size(relid) DESC
        LIMIT {limit}
    """)
    
    result = db.execute(query).mappings()
    return [dict(row) for row in result]


@db_size_router.get("")
async def get_db_size_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder),
    include_system: bool = False,
    schema: str = None
):
    """
    Get the PostgreSQL database size view
    """
    # Get database size information
    total_size = get_total_db_size(db)
    schema_sizes = get_schema_sizes(db, include_system)
    tablespace_sizes = get_tablespace_sizes(db)
    largest_tables = get_largest_tables(db, schema=schema)
    
    # Create a summary card
    summary_card = CardWidget(
        title="Database Size Summary",
        content=f"Total Database Size: {total_size['total_size']}"
    )
    
    # Create tables for different size metrics
    schema_table = TableWidget(
        title="Schema Sizes",
        endpoint="/postgres/db/size",
        data=schema_sizes
    )
    
    tablespace_table = TableWidget(
        title="Tablespace Sizes",
        endpoint="/postgres/db/size",
        data=tablespace_sizes
    )
    
    largest_tables_table = TableWidget(
        title="Largest Tables",
        endpoint="/postgres/db/size",
        data=largest_tables
    )
    
    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Database Size",
        widgets=[
            summary_card,
            schema_table,
            tablespace_table,
            largest_tables_table
        ]
    )