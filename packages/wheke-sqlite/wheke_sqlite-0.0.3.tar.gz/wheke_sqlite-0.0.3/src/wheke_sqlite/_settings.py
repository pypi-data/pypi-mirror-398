from typing import ClassVar

from wheke import FeatureSettings


class DatabaseSettings(FeatureSettings):
    __feature_name__: ClassVar[str] = "database"

    connection_string: str = "sqlite:///database.db"
