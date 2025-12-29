from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine
from svcs import Container
from wheke import WhekeSettings, get_service, get_settings

from ._settings import DatabaseSettings


class DatabaseService:
    settings: DatabaseSettings

    engine: Engine

    def __init__(self, *, database_settings: DatabaseSettings) -> None:
        self.engine = create_engine(database_settings.connection_string)

    @property
    def session(self) -> Session:
        return Session(self.engine)

    def create_db(self) -> None:
        SQLModel.metadata.create_all(self.engine)


def database_service_factory(container: Container) -> DatabaseService:
    settings = get_settings(container, WhekeSettings).get_feature(DatabaseSettings)
    return DatabaseService(database_settings=settings)


def get_database_service(container: Container) -> DatabaseService:
    return get_service(container, DatabaseService)
