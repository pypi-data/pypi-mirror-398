# plugin.py

from typing import Annotated, Any

from fastpluggy.core.module_base import FastPluggyBaseModule
from fastpluggy.core.tools.inspect_tools import InjectDependency
from fastpluggy.fastpluggy import FastPluggy


def get_router():
    from .routers import postgres_tools_router
    return postgres_tools_router


class PostgresToolsModule(FastPluggyBaseModule):
    module_name: str = "postgres_tools"

    module_menu_name: str = "Postgres"
    module_menu_icon: str = "fas fa-database"

    depends_on: dict = {
                "ui_tools": ">=0.0.4",
    }
    module_router: Any = get_router

    def on_load_complete(self, fast_pluggy: Annotated[FastPluggy, InjectDependency]) -> None:
        # Menu items are now added using the @menu_entry decorator in the router files
        pass
