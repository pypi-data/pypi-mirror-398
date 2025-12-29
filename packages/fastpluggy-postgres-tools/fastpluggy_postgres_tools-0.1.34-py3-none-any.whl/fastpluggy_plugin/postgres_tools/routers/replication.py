from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy_plugin.ui_tools.extra_widget.display.card import CardWidget

from fastpluggy.core.menu.decorator import menu_entry

replication_router = APIRouter(prefix="/replication", tags=["postgres_replication"])


def get_replication_status(db: Session):
    """
    Get replication status from pg_stat_replication
    """
    query = text("""
        SELECT 
          application_name,
          client_addr,
          state,
          sync_state,
          pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS write_lag_bytes,
          pg_wal_lsn_diff(pg_current_wal_lsn(), write_lsn) AS flush_lag_bytes,
          pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn) AS replay_lag_bytes,
          pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn)) AS write_lag,
          pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), write_lsn)) AS flush_lag,
          pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn)) AS replay_lag,
          CASE 
            WHEN pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn) > 50000000 THEN 'error'
            WHEN pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lsn) > 10000000 THEN 'warning'
            ELSE 'ok'
          END AS status
        FROM pg_stat_replication
    """)
    
    try:

            result = db.execute(query).mappings()
            return [dict(row) for row in result]
    except Exception as e:
        # This might fail if not running on a primary server
        return []


def get_replication_slots(db: Session):
    """
    Get replication slots from pg_replication_slots
    """
    query = text("""
        SELECT 
          slot_name,
          plugin,
          slot_type,
          active,
          restart_lsn,
          pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_size
        FROM pg_replication_slots
    """)
    
    try:

            result = db.execute(query).mappings()
            return [dict(row) for row in result]
    except Exception as e:
        # This might fail if not running on a primary server
        return []


def get_backup_history(db: Session, limit: int = 10):
    """
    Get backup history from pg_backup_history if it exists
    This is a placeholder - in a real implementation, you would need to
    create this table or integrate with a backup tool
    """
    # Check if pg_backup_history table exists
    check_query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = 'pg_backup_history'
        ) AS table_exists
    """)
    
    try:

            result = db.execute(check_query).mappings().first()
            if not result or not result["table_exists"]:
                return []
            
            # If table exists, query backup history
            query = text(f"""
                SELECT 
                  backup_id,
                  backup_type,
                  start_time,
                  end_time,
                  size_bytes,
                  pg_size_pretty(size_bytes) AS size,
                  status,
                  location
                FROM pg_backup_history
                ORDER BY start_time DESC
                LIMIT {limit}
            """)
            
            result = db.execute(query).mappings()
            return [dict(row) for row in result]
    except Exception as e:
        # This might fail if the table doesn't exist
        return []


@replication_router.get("")
async def get_replication_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder)
):
    """
    Get the PostgreSQL replication and backup status view
    """
    # Get replication and backup data
    replication_status = get_replication_status(db)
    replication_slots = get_replication_slots(db)
    backup_history = get_backup_history(db)
    
    # Create widgets
    widgets = []
    
    # Add a card for replication status summary
    is_primary = True
    try:
        # Check if this is a primary server
        query = text("SELECT pg_is_in_recovery()")

        result = db.execute(query).scalar()
        is_primary = not result
    except Exception:
        is_primary = False
    
    if is_primary:
        status_card = CardWidget(
            title="Replication Status",
            content=f"This is a primary server with {len(replication_status)} active replicas."
        )
    else:
        status_card = CardWidget(
            title="Replication Status",
            content="This is a replica server."
        )
    
    widgets.append(status_card)
    
    # Add tables for replication status and slots if this is a primary
    if is_primary and replication_status:
        replication_table = TableWidget(
            title="Replication Status",
            endpoint="/postgres/replication",
            data=replication_status,
            description="Replication lag > 10MB is highlighted in yellow, > 50MB in red."
        )
        widgets.append(replication_table)
    
    if is_primary and replication_slots:
        slots_table = TableWidget(
            title="Replication Slots",
            endpoint="/postgres/replication",
            data=replication_slots
        )
        widgets.append(slots_table)
    
    # Add a table for backup history if available
    if backup_history:
        backup_table = TableWidget(
            title="Backup History",
            endpoint="/postgres/replication",
            data=backup_history
        )
        widgets.append(backup_table)
    else:
        backup_card = CardWidget(
            title="Backup History",
            content="No backup history available. Consider setting up a backup solution and tracking backups in a pg_backup_history table."
        )
        widgets.append(backup_card)
    
    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Replication & Backups",
        widgets=widgets
    )