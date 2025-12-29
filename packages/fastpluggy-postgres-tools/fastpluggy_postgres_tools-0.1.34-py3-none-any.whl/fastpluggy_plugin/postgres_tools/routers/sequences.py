from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy.core.menu.decorator import menu_entry

sequences_router = APIRouter(prefix="/sequences", tags=["postgres_sequences"])


def get_sequences_data(db: Session):
    query = text("""
        SELECT
            schemaname || '.' || sequencename AS sequence_name,
            last_value,
            max_value,
            COALESCE(max_value - last_value, 0) AS remaining
        FROM pg_sequences
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY remaining ASC
    """)


    result = db.execute(query).mappings()
    rows = []
    for row in result:
        last_value = row["last_value"]
        max_value = row["max_value"]

        if last_value is None or max_value is None or max_value == 0:
            percent_used = 0
            percent_remaining = 100
        else:
            percent_used = (last_value * 100) / max_value
            percent_remaining = 100 - percent_used

        rows.append({
            "sequence_name": row["sequence_name"],
            "last_value": last_value,
            "max_value": max_value,
            "remaining": row["remaining"],
            "percent_used": round(percent_used, 2),
            "percent_remaining": round(percent_remaining, 2),
        })
    return rows




@sequences_router.get("")
async def get_sequences_view(request: Request, db=Depends(get_db), view_builder=Depends(get_view_builder)):
    """
    Get the PostgreSQL sequences view
    """
    sequences_info = get_sequences_data(db)
    # Create a TableView for sequences

    table_view = TableWidget(
        title="Postgres Sequences",
        endpoint="/postgres/sequences",
        data=sequences_info
    )

    # Render the table view
    return view_builder.generate(
        request,
        title="Postgres Sequences",
        widgets=[
            table_view
        ]
    )
