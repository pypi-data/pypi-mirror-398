from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastpluggy_plugin.ui_tools.extra_widget.display.card import CardWidget
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.widgets import TableWidget
from ..utils import execute_query_first, execute_query

queries_router = APIRouter(prefix="/queries", tags=["postgres_queries"])


def check_pg_stat_statements(db_manager: Session):
    """
    Check if pg_stat_statements extension is installed
    """
    query = """
        SELECT COUNT(*) AS count
        FROM pg_extension
        WHERE extname = 'pg_stat_statements'
    """

    result = execute_query_first(db=db_manager,query_text=query)
    print(
        f"pg_stat_statements extension is {'installed' if result['count'] > 0 else 'not installed'}"
    )
    return result["count"] > 0


def get_query_performance_statistics(db_manager: Session, limit: int = 10, include_p95: bool = False):
    """
    Get query performance statistics from the database
    """
    # Check if pg_stat_statements is installed
    has_pg_stat_statements = check_pg_stat_statements(db_manager)

    if not has_pg_stat_statements:
        return [], False

    # Build a version-agnostic query using COALESCE to support PG13+ and PG15+ column names
    # We compute mean/avg from total/calls to avoid relying on mean_* columns which vary by version
    p95_column = ""
    # Note: 95th percentile is based on derived per-call time for compatibility across versions
    if include_p95:
        p95_column = ", (SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY COALESCE(total_exec_time, total_time)/GREATEST(calls,1)) FROM pg_stat_statements) AS p95_time"

    query = f"""
        SELECT
          query,
          calls,
          COALESCE(total_exec_time, total_time) AS total_time,
          ROUND(COALESCE(total_exec_time, total_time) / GREATEST(calls, 1), 2) AS mean_time,
          ROUND(COALESCE(total_exec_time, total_time) / GREATEST(calls, 1), 2) AS avg_time,
          SUBSTRING(query, 1, 100) AS truncated_query
          {p95_column}
        FROM pg_stat_statements
        ORDER BY COALESCE(total_exec_time, total_time) DESC
        LIMIT :limit
    """

    result = execute_query(db_manager, query, {"limit": limit})
    return result, True


@queries_router.get("")
async def get_queries_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder),
    limit: int = 10,
    include_p95: bool = False
):
    """
    Get the PostgreSQL query performance analysis view
    """
    # Create a connection manager for this request

    # Get query performance statistics
    query_stats, has_extension = get_query_performance_statistics(db, limit, include_p95)

    if not has_extension:
        # Create a card to show extension installation instructions
        extension_card = CardWidget(
            title="Extension Required",
            content="""
            <p>The pg_stat_statements extension is required for query performance analysis.</p>
            <p>To install it, run the following SQL command:</p>
            <pre>CREATE EXTENSION IF NOT EXISTS pg_stat_statements;</pre>
            <p>You may need superuser privileges to install this extension.</p>
            """,
            links=[
                {
                    "url": request.url_for("install_pg_stat_statements"),
                    "text": "Install Extension",
                    "type": "primary"
                }
            ]
        )

        return view_builder.generate(
            request,
            title="PostgreSQL Query Performance Analysis",
            widgets=[extension_card]
        )

    # Create a table for query performance statistics
    query_table = TableWidget(
        title="Query Performance Statistics",
        endpoint="/postgres/queries",
        data=query_stats,
        description=f"Top {limit} queries by total execution time."
    )

    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Query Performance Analysis",
        widgets=[query_table]
    )


@queries_router.get("/install-pg-stat-statements", name="install_pg_stat_statements")
async def install_pg_stat_statements(request: Request, db=Depends(get_db)):
    """
    Install the pg_stat_statements extension
    """
    try:
        # Create a connection manager for this request

        # SQL command to install the extension
        query = "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

        # Execute the SQL command using our connection manager
        db.execute_command(query)
    except Exception as e:
        # If there's an error, we'll just redirect back to the queries view
        # The error will be shown there if the extension still isn't installed
        print(f"Error installing pg_stat_statements extension: {e}")

    # Redirect back to the queries view
    return RedirectResponse(url=request.url_for("get_queries_view"))
