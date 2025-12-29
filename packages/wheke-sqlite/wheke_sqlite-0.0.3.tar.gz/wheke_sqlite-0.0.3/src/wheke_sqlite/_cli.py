import typer
from rich.console import Console
from typer import Context
from wheke import get_container

from wheke_sqlite._service import get_database_service

cli = typer.Typer(short_help="Database commands")
console = Console()


@cli.command()
def create_db(ctx: Context) -> None:
    container = get_container(ctx)
    database_service = get_database_service(container)

    console.print("Creating sqlite database...")

    database_service.create_db()
