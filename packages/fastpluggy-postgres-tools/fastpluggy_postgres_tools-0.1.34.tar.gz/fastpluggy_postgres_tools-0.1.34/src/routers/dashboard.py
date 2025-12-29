from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy.core.widgets.categories.display.custom import CustomTemplateWidget
from fastpluggy_plugin.ui_tools.extra_widget.display.card import CardWidget
from fastpluggy.core.menu.decorator import menu_entry

dashboard_router = APIRouter()


def get_cluster_health(db: Session):
    """
    Get overall cluster health status
    """
    # Check for high table bloat
    bloat_query = text("""
        SELECT 
          COUNT(*) AS count,
          MAX(ROUND(100.0 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2)) AS max_bloat
        FROM pg_stat_user_tables
        WHERE ROUND(100.0 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2) > 40
    """)
    
    # Check for unused indexes
    index_query = text("""
        SELECT COUNT(*) AS count
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0 AND pg_relation_size(indexrelid) > 10000000
    """)
    
    # Check for long-running queries
    query_query = text("""
        SELECT COUNT(*) AS count
        FROM pg_stat_activity
        WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes'
    """)
    
    # Check for replication lag
    replication_query = text("""
        SELECT 
          COUNT(*) AS count,
          MAX(pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn)) AS max_lag
        FROM pg_stat_replication
        WHERE pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn) > 50000000
    """)
    
    alerts = []
    status = "green"
    
    try:

            # Check table bloat
            bloat_result = db.execute(bloat_query).mappings().first()
            if bloat_result and bloat_result["count"] > 0:
                alerts.append({
                    "module": "tables",
                    "message": f"{bloat_result['count']} tables with bloat > 40% (max: {bloat_result['max_bloat']}%)",
                    "severity": "error"
                })
                status = "red"
            
            # Check unused indexes
            index_result = db.execute(index_query).mappings().first()
            if index_result and index_result["count"] > 0:
                alerts.append({
                    "module": "indexes",
                    "message": f"{index_result['count']} unused indexes larger than 10MB",
                    "severity": "warning"
                })
                if status == "green":
                    status = "yellow"
            
            # Check long-running queries
            query_result = db.execute(query_query).mappings().first()
            if query_result and query_result["count"] > 0:
                alerts.append({
                    "module": "queries",
                    "message": f"{query_result['count']} queries running for more than 5 minutes",
                    "severity": "warning"
                })
                if status == "green":
                    status = "yellow"
            
            # Check replication lag
            try:
                replication_result = db.execute(replication_query).mappings().first()
                if replication_result and replication_result["count"] > 0:
                    alerts.append({
                        "module": "replication",
                        "message": f"{replication_result['count']} replicas with lag > 50MB",
                        "severity": "error"
                    })
                    status = "red"
            except Exception:
                # This might fail if not running on a primary server
                pass
    except Exception as e:
        alerts.append({
            "module": "system",
            "message": f"Error checking cluster health: {str(e)}",
            "severity": "error"
        })
        status = "red"
    
    return {
        "status": status,
        "alerts": alerts
    }


def get_recommendations(db: Session):
    """
    Get recommendations for database improvements
    """
    recommendations = []
    
    # Check for pgstattuple extension
    pgstattuple_query = text("""
        SELECT COUNT(*) AS count
        FROM pg_extension
        WHERE extname = 'pgstattuple'
    """)
    
    # Check for pg_stat_statements extension
    pg_stat_statements_query = text("""
        SELECT COUNT(*) AS count
        FROM pg_extension
        WHERE extname = 'pg_stat_statements'
    """)

    # Check shared_preload_libraries for pg_stat_statements
    shared_preload_check = text("""
        SELECT current_setting('shared_preload_libraries', true) AS shared_preload_libraries
    """)
    
    # Check autovacuum settings
    autovacuum_query = text("""
        SELECT setting::int AS threshold
        FROM pg_settings
        WHERE name = 'autovacuum_vacuum_threshold'
    """)
    
    # Check max_connections usage
    connections_query = text("""
        SELECT 
          COUNT(*) AS current_connections,
          (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_connections
    """)
    
    try:

            # Check pgstattuple extension
            pgstattuple_result = db.execute(pgstattuple_query).mappings().first()
            if pgstattuple_result and pgstattuple_result["count"] == 0:
                recommendations.append({
                    "type": "extension",
                    "message": "Install pgstattuple for accurate bloat metrics",
                    "action": "CREATE EXTENSION pgstattuple;"
                })
            
            # Check pg_stat_statements extension
            pg_stat_statements_result = db.execute(pg_stat_statements_query).mappings().first()
            if pg_stat_statements_result:
                if pg_stat_statements_result["count"] == 0:
                    recommendations.append({
                        "type": "extension",
                        "message": "Enable pg_stat_statements for query analysis",
                        "action": "CREATE EXTENSION pg_stat_statements;"
                    })
                else:
                    # Extension installed; check if preloaded
                    preload_row = db.execute(shared_preload_check).mappings().first()
                    preload_val = (preload_row or {}).get("shared_preload_libraries") or ""
                    if "pg_stat_statements" not in preload_val:
                        recommendations.append({
                            "type": "extension",
                            "message": "pg_stat_statements installed but not loaded at startup",
                            "action": "Set shared_preload_libraries to include pg_stat_statements and restart PostgreSQL; then ensure CREATE EXTENSION pg_stat_statements; is run in each database as needed."
                        })
            
            # Check autovacuum settings
            autovacuum_result = db.execute(autovacuum_query).mappings().first()
            if autovacuum_result and autovacuum_result["threshold"] > 50:
                recommendations.append({
                    "type": "setting",
                    "message": "Lower autovacuum_vacuum_threshold for more frequent vacuuming",
                    "action": "ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;"
                })
            
            # Check max_connections usage
            connections_result = db.execute(connections_query).mappings().first()
            if connections_result:
                current = connections_result["current_connections"]
                maximum = connections_result["max_connections"]
                if current > 0.8 * maximum:
                    recommendations.append({
                        "type": "setting",
                        "message": f"Current connections ({current}) approaching max_connections ({maximum})",
                        "action": "ALTER SYSTEM SET max_connections = 200; # Adjust as needed"
                    })
    except Exception as e:
        recommendations.append({
            "type": "error",
            "message": f"Error generating recommendations: {str(e)}",
            "action": "Check database connection and permissions"
        })
    
    return recommendations


def get_metrics_summary(db: Session):
    """
    Get summary metrics for the dashboard
    """
    metrics = {}

    # Get average table bloat
    bloat_query = text("""
        SELECT AVG(ROUND(100.0 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 2)) AS avg_bloat
        FROM pg_stat_user_tables
        WHERE n_live_tup + n_dead_tup > 0
    """)

    # Check if pg_stat_statements is available
    latency_ext_check = text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
        ) AS has_pg_stat_statements
    """)

    # Check if pg_stat_statements is preloaded via shared_preload_libraries
    shared_preload_check = text("""
        SELECT current_setting('shared_preload_libraries', true) AS shared_preload_libraries
    """)

    # Column detection queries for pg_stat_statements (version-agnostic)
    has_total_exec_col_q = text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'pg_stat_statements' AND column_name = 'total_exec_time'
        ) AS has_total_exec
    """)
    has_total_time_col_q = text("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'pg_stat_statements' AND column_name = 'total_time'
        ) AS has_total_time
    """)

    # Get autovacuum runs per day (estimated)
    vacuum_query = text("""
        SELECT COUNT(*) AS table_count
        FROM pg_stat_user_tables
        WHERE last_autovacuum > NOW() - INTERVAL '24 hours'
    """)

    # Always isolate each metric to avoid one failure breaking all
    try:
        bloat_result = db.execute(bloat_query).mappings().first()
        if bloat_result:
            metrics["bloat_avg"] = round(bloat_result["avg_bloat"] or 0, 2)
    except Exception as e:
        metrics.setdefault("errors", []).append(f"bloat: {e}")

    try:
        latency_check = db.execute(latency_ext_check).mappings().first()
        if latency_check and latency_check["has_pg_stat_statements"]:
            # Check if it's preloaded; if not, warn and recommend enabling
            preload_row = db.execute(shared_preload_check).mappings().first()
            preload_val = (preload_row or {}).get("shared_preload_libraries") or ""
            is_preloaded = "pg_stat_statements" in preload_val
            if not is_preloaded:
                metrics.setdefault("warnings", []).append(
                    "pg_stat_statements extension is installed but not loaded via shared_preload_libraries; latency metrics disabled."
                )
                metrics.setdefault("recommendations", []).append(
                    "Add pg_stat_statements to shared_preload_libraries and restart PostgreSQL. Example: shared_preload_libraries = 'pg_stat_statements' (then CREATE EXTENSION pg_stat_statements; if not created)."
                )
                metrics.setdefault("notes", []).append("query_latency_avg set to N/A due to missing preload")
                metrics.setdefault("query_latency_avg", "N/A")
            else:
                # Detect which timing column exists to avoid errors on different versions
                has_total_exec = False
                has_total_time = False
                try:
                    r1 = db.execute(has_total_exec_col_q).mappings().first()
                    has_total_exec = bool(r1 and r1.get("has_total_exec"))
                except Exception:
                    pass
                try:
                    r2 = db.execute(has_total_time_col_q).mappings().first()
                    has_total_time = bool(r2 and r2.get("has_total_time"))
                except Exception:
                    pass

                latency_sql = None
                if has_total_exec:
                    latency_sql = text("""
                        SELECT AVG(total_exec_time / GREATEST(calls, 1)) AS avg_latency
                        FROM pg_stat_statements
                    """)
                elif has_total_time:
                    latency_sql = text("""
                        SELECT AVG(total_time / GREATEST(calls, 1)) AS avg_latency
                        FROM pg_stat_statements
                    """)

                if latency_sql is not None:
                    try:
                        latency_result = db.execute(latency_sql).mappings().first()
                        if latency_result:
                            metrics["query_latency_avg"] = round(latency_result["avg_latency"] or 0, 2)
                    except Exception as e:
                        # Ensure failed query doesn't poison the transaction for later ops
                        try:
                            db.rollback()
                        except Exception:
                            pass
                        # Convert specific prerequisite error into a warning with recommendation
                        msg = str(e)
                        if "pg_stat_statements must be loaded via \"shared_preload_libraries\"" in msg or "ObjectNotInPrerequisiteState" in msg:
                            metrics.setdefault("warnings", []).append(
                                "pg_stat_statements is not preloaded; cannot compute query latency."
                            )
                            metrics.setdefault("recommendations", []).append(
                                "Set shared_preload_libraries to include pg_stat_statements and restart PostgreSQL."
                            )
                            metrics.setdefault("query_latency_avg", "N/A")
                        else:
                            metrics.setdefault("errors", []).append(f"latency: {e}")
        else:
            # Extension not installed; provide a gentle recommendation
            metrics.setdefault("warnings", []).append(
                "pg_stat_statements extension is not installed; latency metrics unavailable."
            )
            metrics.setdefault("recommendations", []).append(
                "CREATE EXTENSION pg_stat_statements; and consider adding it to shared_preload_libraries for persistent loading."
            )
            metrics.setdefault("query_latency_avg", "N/A")
    except Exception as e:
        metrics.setdefault("errors", []).append(f"latency_check: {e}")

    try:
        vacuum_result = db.execute(vacuum_query).mappings().first()
        if vacuum_result:
            metrics["vacuum_runs_24h"] = vacuum_result["table_count"]
    except Exception as e:
        metrics.setdefault("errors", []).append(f"vacuum: {e}")

    # If there were errors, also keep a human-friendly message
    if "errors" in metrics and metrics["errors"]:
        metrics["error"] = "; ".join(metrics["errors"])

    return metrics


@dashboard_router.get("/")
async def get_dashboard_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder)
):
    """
    Get the PostgreSQL global dashboard view
    """
    # Get dashboard data
    health = get_cluster_health(db)
    recommendations = get_recommendations(db)
    metrics = get_metrics_summary(db)
    
    # Create widgets
    status_icon = "✅" if health["status"] == "green" else "⚠️" if health["status"] == "yellow" else "❌"
    
    health_card = CardWidget(
        title=f"Global Health: {status_icon} {health['status'].capitalize()}",
        content="Your PostgreSQL database is healthy." if health["status"] == "green" else 
                "Your PostgreSQL database has some warnings." if health["status"] == "yellow" else
                "Your PostgreSQL database has critical issues that need attention."
    )
    
    # Create alerts table if there are any alerts
    widgets = [health_card]
    
    if health["alerts"]:
        alerts_table = TableWidget(
            title="Active Alerts",
            endpoint="/postgres/dashboard",
            data=health["alerts"]
        )
        widgets.append(alerts_table)
    
    # Create recommendations table
    if recommendations:
        recommendations_table = TableWidget(
            title="Recommendations",
            endpoint="/postgres/dashboard",
            data=recommendations
        )
        widgets.append(recommendations_table)
    
    # Create metrics summary card
    metrics_content = "Key Metrics:\n"
    for key, value in metrics.items():
        metrics_content += f"- {key.replace('_', ' ').title()}: {value}\n"
    
    metrics_card = CardWidget(
        title="Metrics Summary",
        content=metrics_content
    )
    widgets.append(metrics_card)

    # Add a cool clickable cards grid for all Postgres Tools features
    cards = [
        {
            "title": "Database Size",
            "icon": "fas fa-database",
            "description": "Explore overall DB size, schemas, tablespaces and largest tables.",
            "url": request.url_for("get_db_size_view")
        },
        {
            "title": "Sequences",
            "icon": "fas fa-list-ol",
            "description": "Check sequence usage and remaining capacity.",
            "url": request.url_for("get_sequences_view")
        },
        {
            "title": "Indexes",
            "icon": "fas fa-layer-group",
            "description": "Find large or unused indexes and scan counts.",
            "url": request.url_for("get_indexes_view")
        },
        {
            "title": "Tables",
            "icon": "fas fa-table",
            "description": "Detect table bloat, last vacuum/analyze and sizes.",
            "url": request.url_for("get_tables_view")
        },
        {
            "title": "Queries",
            "icon": "fas fa-tachometer-alt",
            "description": "Analyze heavy queries with pg_stat_statements.",
            "url": request.url_for("get_queries_view")
        },
        {
            "title": "Connections & Locks",
            "icon": "fas fa-link",
            "description": "Inspect active connections and lock contention.",
            "url": request.url_for("get_connections_view")
        },
        {
            "title": "Vacuum Status",
            "icon": "fas fa-broom",
            "description": "Track vacuum activity and autovacuum settings.",
            "url": request.url_for("get_vacuum_view")
        },
        {
            "title": "Replication & Backups",
            "icon": "fas fa-sync",
            "description": "Monitor replicas, slots and backup history.",
            "url": request.url_for("get_replication_view")
        },
        {
            "title": "Alerts & Webhooks",
            "icon": "fas fa-bell",
            "description": "Configure alert rules and send notifications.",
            "url": request.url_for("get_alerts_view")
        },
        {
            "title": "Extensions",
            "icon": "fas fa-plug",
            "description": "List and manage available PostgreSQL extensions.",
            "url": request.url_for("get_extensions_view")
        },
    ]

    widgets.append(
        CustomTemplateWidget(
            template_name="postgres_tools/dashboard_cards.html.j2",
            context={
                "title": "PostgreSQL Tools",
                "cards": cards
            }
        )
    )
    
    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Global Dashboard",
        widgets=widgets
    )