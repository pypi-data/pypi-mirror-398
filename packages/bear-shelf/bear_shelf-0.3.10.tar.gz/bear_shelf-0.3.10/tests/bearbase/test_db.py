from pathlib import Path
from typing import Any

from sqlalchemy.orm import DeclarativeMeta, Mapped, mapped_column

from bear_shelf.database import BearShelfDB
from bear_shelf.database.config import DatabaseConfig
from bear_shelf.dialect.bear_dialect import BearShelfDialect


class SettingsDB(BearShelfDB):
    """Database manager for settings storage."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the SettingsDB with default parameters."""
        super().__init__(*args, **kwargs)

    @property
    def dialect(self) -> BearShelfDialect:
        """Get the database dialect."""
        return self.engine.dialect  # type: ignore[return-value]


Base: DeclarativeMeta = SettingsDB.get_base()


class Settings(Base):
    """SQLAlchemy model for settings storage."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(nullable=False, default="")
    value: Mapped[str] = mapped_column(nullable=False, default="")
    type: Mapped[str] = mapped_column(nullable=False, default="str")


def test_database_settings() -> None:
    """Main function to create the settings database."""
    path: Path = Path(__file__).parent / "data" / "example33.toml"
    if path.exists():
        path.unlink()
    db_config = DatabaseConfig(scheme="bearshelf", name=str(path))
    db = SettingsDB(database_config=db_config)
    db.create_tables()

    with db.open_session() as session:
        setting = Settings(key="theme", value="dark", type="str")
        session.add(setting)

    retrieved_setting: Settings | None = db.query().filter_by(key="theme").first()

    print(db.get_orm_tables())  # type: ignore[no-untyped-call]

    assert retrieved_setting is not None
    assert retrieved_setting.value == "dark"
    assert retrieved_setting.type == "str"
