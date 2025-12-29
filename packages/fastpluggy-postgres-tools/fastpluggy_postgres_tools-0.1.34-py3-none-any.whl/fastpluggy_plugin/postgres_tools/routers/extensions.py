from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget
from fastpluggy.core.menu.decorator import menu_entry

extensions_router = APIRouter(prefix="/extensions", tags=["postgres_extensions"])


def get_available_extensions(db: Session):
    """
    Returns the list of available PostgreSQL extensions on the server.
    Includes default version, currently installed version (if any), and comment.
    """
    query = text(
        """
        SELECT 
            name,
            default_version,
            installed_version,
            comment
        FROM pg_available_extensions
        ORDER BY name
        """
    )

    result = db.execute(query).mappings()
    return [dict(row) for row in result]


@extensions_router.get("")
async def get_extensions_view(
    request: Request,
    db=Depends(get_db),
    view_builder=Depends(get_view_builder)
):
    """
    Page listing available PostgreSQL extensions on the server.
    """
    try:
        extensions = get_available_extensions(db)
    except Exception as e:
        # Fallback: show an empty table with an error note in the title
        extensions = []
        title = f"PostgreSQL Extensions (error fetching: {e})"
    else:
        title = "PostgreSQL Extensions"

    table = TableWidget(
        title="Available Extensions",
        endpoint="/postgres/extensions",
        description="List of extensions available on this PostgreSQL server. 'installed_version' is null if not installed in the current database.",
        data=extensions,
        field_callbacks={
            "installed_version": lambda val: val if val else "",
        }
    )

    return view_builder.generate(
        request,
        title=title,
        widgets=[
            table
        ]
    )
