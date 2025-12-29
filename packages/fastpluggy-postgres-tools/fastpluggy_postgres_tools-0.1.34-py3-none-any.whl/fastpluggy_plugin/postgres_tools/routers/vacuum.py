from typing import Optional, Annotated

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.flash import FlashMessage
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.widgets import TableWidget
from fastpluggy.core.widgets.categories.input.button import AutoLinkWidget
from fastpluggy.core.widgets.categories.input.button_list import ButtonListWidget

vacuum_router = APIRouter(prefix="/vacuum", tags=["postgres_vacuum"])


class VacuumRequest(BaseModel):
    schema_name: Optional[str] = None
    table_name: Optional[str] = None
    analyze: bool = True
    full: bool = False


def get_table_vacuum_status(db: Session, schema: str = None, days_since_vacuum: int = None):
    """
    Get vacuum status for tables
    """
    where_clause = "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
    if schema:
        where_clause += f" AND schemaname = '{schema}'"
    if days_since_vacuum:
        where_clause += f" AND EXTRACT(EPOCH FROM (now() - COALESCE(last_vacuum, last_autovacuum, '1970-01-01'::timestamp)))/86400 > {days_since_vacuum}"

    query = text(f"""
        SELECT 
          schemaname, 
          relname, 
          last_vacuum, 
          last_autovacuum, 
          n_dead_tup,
          EXTRACT(EPOCH FROM (now() - COALESCE(last_vacuum, last_autovacuum, '1970-01-01'::timestamp)))/86400 AS days_since_vacuum,
          CASE 
            WHEN EXTRACT(EPOCH FROM (now() - COALESCE(last_vacuum, last_autovacuum, '1970-01-01'::timestamp)))/86400 > 30 THEN 'error'
            WHEN EXTRACT(EPOCH FROM (now() - COALESCE(last_vacuum, last_autovacuum, '1970-01-01'::timestamp)))/86400 > 14 THEN 'warning'
            ELSE 'ok'
          END AS status
        FROM pg_stat_user_tables
        {where_clause}
        ORDER BY days_since_vacuum DESC
    """)

    result = db.execute(query).mappings()
    rows = [dict(row) for row in result]

    # Enhance status field with color-coded badge and tooltip reason
    def _status_color(status: str) -> str:
        key = (status or '').lower()
        return 'green' if key == 'ok' else 'yellow' if key == 'warning' else 'red' if key == 'error' else 'secondary'

    enhanced = []
    for r in rows:
        status = r.get('status')
        color = _status_color(status)
        days = r.get('days_since_vacuum')
        try:
            days_val = float(days) if days is not None else None
        except Exception:
            days_val = None
        last_ts = r.get('last_vacuum') or r.get('last_autovacuum')
        last_txt = last_ts.strftime('%Y-%m-%d %H:%M:%S') if last_ts else 'Never'
        n_dead = r.get('n_dead_tup')
        if status == 'error':
            reason = f"Last vacuum/autovacuum {days_val:.1f} days ago (>30 days threshold). Dead tuples: {n_dead}. Last: {last_txt}." if days_val is not None else f"Over 30 days since last vacuum/autovacuum. Dead tuples: {n_dead}. Last: {last_txt}."
        elif status == 'warning':
            reason = f"Last vacuum/autovacuum {days_val:.1f} days ago (>14 days threshold). Dead tuples: {n_dead}. Last: {last_txt}." if days_val is not None else f"Over 14 days since last vacuum/autovacuum. Dead tuples: {n_dead}. Last: {last_txt}."
        else:
            reason = f"Last vacuum/autovacuum {days_val:.1f} days ago. Dead tuples: {n_dead}. Last: {last_txt}." if days_val is not None else f"Vacuum recently run. Dead tuples: {n_dead}. Last: {last_txt}."
        badge = f'<span class="badge bg-{color}" title="{reason}">{(status.title() if status else "N/A")}</span>'
        r['status'] = badge
        enhanced.append(r)

    return enhanced


def get_current_vacuum_progress(db: Session):
    """
    Get current vacuum progress
    """
    query = text("""
                 SELECT a.pid,
                        a.datname,
                        a.usename,
                        p.relid::regclass                                                    AS table_name,
                        p.phase,
                        p.heap_blks_total,
                        p.heap_blks_scanned,
                        p.heap_blks_vacuumed,
                        ROUND(100.0 * p.heap_blks_scanned / NULLIF(p.heap_blks_total, 0), 2) AS percent_complete
                 FROM pg_stat_progress_vacuum p
                          JOIN pg_stat_activity a ON p.pid = a.pid
                 """)

    result = db.execute(query).mappings()
    return [dict(row) for row in result]


def get_autovacuum_settings(db: Session):
    """
    Get autovacuum settings
    """
    query = text("""
                 SELECT name,
                        setting,
                        unit,
                        context
                 FROM pg_settings
                 WHERE name LIKE 'autovacuum%'
                 """)

    result = db.execute(query).mappings()
    return [dict(row) for row in result]


def execute_vacuum(db: Session, vacuum_request: VacuumRequest):
    """
    Execute vacuum operation on specified table(s)
    Run in AUTOCOMMIT mode because VACUUM cannot run inside a transaction block.
    Uses a fresh Engine connection to avoid Session-bound transactions.
    """
    try:
        # Build the vacuum command
        vacuum_cmd = "VACUUM"
        if vacuum_request.full:
            vacuum_cmd += " FULL"
        if vacuum_request.analyze:
            vacuum_cmd += " ANALYZE"

        # Add table specification if provided
        if vacuum_request.table_name:
            if vacuum_request.schema_name:
                table_spec = f'"{vacuum_request.schema_name}"."{vacuum_request.table_name}"'
            else:
                table_spec = f'"{vacuum_request.table_name}"'
            vacuum_cmd += f" {table_spec}"

        # Use a fresh Engine connection (not the Session-bound connection)
        engine = db.get_bind()
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(vacuum_cmd)

        return {
            "success": True,
            "message": f"Vacuum operation completed successfully on table {vacuum_request.table_name}",
            "command": vacuum_cmd
        }
    except Exception as e:
        # Statement ran in autocommit mode on a fresh connection
        raise HTTPException(status_code=500, detail=f"Vacuum operation failed: {str(e)}")


@vacuum_router.post("/execute", name="trigger_vacuum")
async def trigger_vacuum(
        request: Request,
        vacuum_request: Annotated[VacuumRequest, Query()],
        db=Depends(get_db),
):
    """
    Trigger a vacuum operation.
    Accepts form-encoded parameters from UI buttons (schema_name, table_name, analyze, full).
    """
    result = execute_vacuum(db, vacuum_request)
    FlashMessage(message=result['message'], category='success' if result['success'] else 'error')
    return RedirectResponse(url=request.url_for('get_vacuum_view'), status_code=status.HTTP_303_SEE_OTHER)


@vacuum_router.get("")
async def get_vacuum_view(
        request: Request,
        db=Depends(get_db),
        view_builder=Depends(get_view_builder),
        schema: str = None,
        days_since_vacuum: int = None
):
    """
    Get the PostgreSQL vacuum status view
    """
    # Get vacuum status data
    vacuum_status = get_table_vacuum_status(db, schema, days_since_vacuum)
    vacuum_progress = get_current_vacuum_progress(db)
    autovacuum_settings = get_autovacuum_settings(db)

    # Create widgets
    vacuum_status_table = TableWidget(
        title="Table Vacuum Status",
        endpoint="/postgres/vacuum",
        data=vacuum_status,
        description="Tables that haven't been vacuumed in over 14 days are highlighted in yellow, over 30 days in red.",
        field_callbacks={
            'status': lambda v: v  # allow raw HTML for status badge with tooltip
        },
        links=[
            AutoLinkWidget(
                label="VACUUM ANALYZE this table",
                route_name="trigger_vacuum",
                css_class="btn btn-sm btn-primary",
                param_inputs={
                    "schema_name": "<schemaname>",
                    "table_name": "<relname>",
                    "analyze": True,
                    "full": False
                }
            ),
            AutoLinkWidget(
                label="VACUUM FULL ANALYZE this table",
                route_name="trigger_vacuum",
                css_class="btn btn-sm btn-warning",
                param_inputs={
                    "schema_name": "<schemaname>",
                    "table_name": "<relname>",
                    "analyze": True,
                    "full": True
                }
            )
        ]
    )

    # Create a card for vacuum progress if there are any active vacuum processes
    widgets = [vacuum_status_table]

    progress_table = TableWidget(
        title="Current Vacuum Progress",
        endpoint="/postgres/vacuum",
        data=vacuum_progress
    )
    widgets.append(progress_table)

    # Create a table for autovacuum settings
    settings_table = TableWidget(
        title="Autovacuum Settings",
        endpoint="/postgres/vacuum",
        data=autovacuum_settings
    )
    widgets.append(settings_table)

    # Add vacuum action buttons using ButtonListWidget and AutoLinkWidget
    vacuum_actions = ButtonListWidget(
        title="Vacuum Operations",
        buttons=[
            AutoLinkWidget(
                label="Run VACUUM ANALYZE (All Tables)",
                route_name="trigger_vacuum",
                css_class="btn btn-primary",
                param_inputs={"analyze": True, "full": False}
            ),
            AutoLinkWidget(
                label="Run VACUUM FULL ANALYZE (All Tables)",
                route_name="trigger_vacuum",
                css_class="btn btn-warning",
                param_inputs={"analyze": True, "full": True}
            )
        ]
    )
    widgets.append(vacuum_actions)

    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Vacuum/Autovacuum Status",
        widgets=widgets
    )
