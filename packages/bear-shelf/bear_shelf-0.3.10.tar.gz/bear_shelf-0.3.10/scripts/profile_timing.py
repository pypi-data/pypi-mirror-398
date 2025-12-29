"""cProfile-based profiling script for Bear Shelf database operations.

This script uses the generic profiler_lib to profile Bear Shelf performance.

Usage:
    python profile_timing.py --iterations 100
    python profile_timing.py -n 50 --output profile.stats
    python profile_timing.py --debug  # Show detailed debug info
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, NamedTuple

from profiler_cub.core import CodeProfiler
from profiler_cub.display import display_all
from profiler_cub.models import ProfileConfig, SortMode
from rich.console import Console
from sqlalchemy import Integer, Select, String, select
from sqlalchemy.orm import Mapped, MappedColumn

from bear_shelf.database import BearShelfDB
from funcy_bear.tools.gradient import ColorGradient, DefaultColorConfig

if TYPE_CHECKING:
    from collections.abc import Sequence


console = Console()

config = ProfileConfig(
    module_name="bear_shelf",
    stats_file=Path("bear_shelf_profile.stats"),
    module_map={
        "Dialect": {"dialect/"},
        "Datastore Adapter": {"datastore/adapter/"},
        "BearBase": {"datastore/database.py", "datastore/__init__.py"},
        "Table": {"datastore/tables/"},
        "Storage": {"datastore/storage/"},
        "Database": {"database/"},
        "WAL": {"datastore/wal/"},
    },
)

SUCCESS, FAILURE = 0, 1


class ProfileDB(BearShelfDB):
    """Custom BearShelfDB for profiling purposes."""


Base = ProfileDB.get_base()


class Logins(Base):
    """Test table for profiling database operations."""

    __tablename__ = "logins"
    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = MappedColumn(String, nullable=False)
    timestamp: Mapped[str] = MappedColumn(String, nullable=False)
    salt: Mapped[int] = MappedColumn(Integer, nullable=False)


class SetupReturn(NamedTuple):
    db: ProfileDB
    iterations: int


def get_db(db_path: str, iterations: int) -> SetupReturn:
    """Provide a temporary BearShelfDB instance for profiling."""
    from bear_shelf.database.config import DatabaseConfig  # noqa: PLC0415

    config = DatabaseConfig(path=db_path, scheme="bearshelf")

    db = ProfileDB(database_config=config, enable_wal=True)
    db.create_tables()
    return SetupReturn(db=db, iterations=iterations)


def run_crud_operations(db: ProfileDB, iterations: int) -> ProfileDB:
    """Run a series of CRUD operations to profile performance."""
    with db.open_session() as session:
        # INSERT operations
        for i in range(iterations):
            login = Logins(user_name=f"user_{i}", timestamp=f"2024-12-09T{i % 24:02d}:00:00Z", salt=i * 1000)
            session.add(login)

    with db.open_session() as session:
        # SELECT operations (range query)
        for _ in range(iterations // 10):
            stmt: Select[tuple[Logins]] = select(Logins).where(Logins.id > 5)  # noqa: PLR2004
            __: Sequence[Logins] = session.execute(stmt).scalars().all()

        # UPDATE operations
        for i in range(iterations // 10):
            stmt = select(Logins).where(Logins.id == i + 1)
            login: Logins | None = session.execute(stmt).scalar_one_or_none()
            if login is not None:
                login.timestamp = "2024-12-09T12:00:00Z"

    with db.open_session() as session:
        # DELETE operations
        for i in range(iterations // 20):
            stmt = select(Logins).where(Logins.id == i + 1)
            login = session.execute(stmt).scalar_one_or_none()
            if login is not None:
                session.delete(login)

    return db


def get_args(args: list[str]) -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description="Profile Bear Shelf database stack performance with cProfile")
    parser.add_argument("-n", "--iterations", type=int, default=100, help="Number of operations to run (default: 100)")
    parser.add_argument(
        "-f", "--full", action="store_true", help="Profile full database operations including setup/teardown"
    )
    parser.add_argument("--top", type=int, default=20, help="Number of top functions to show (default: 20)")
    parser.add_argument(
        "--sort",
        type=str,
        choices=["cumulative_time", "total_time", "load_order", "call_count"],
        default="cumulative_time",
        help="How to sort function panels (default: cumulative_time)",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Show detailed breakdown of functions matching this module name",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the profiling suite."""
    if args is None:
        args = sys.argv[1:]

    try:
        arguments: Namespace = get_args(args)

        if arguments.sort == "load_order":
            original_iterations: int = arguments.iterations
            arguments.iterations = 1
            console.print(
                f"[yellow]Note: Forcing 1 iteration for load_order mode (requested {original_iterations})[/yellow]\n"
            )

        profiler = CodeProfiler(
            pkg_name=config.module_name,
            module_map=config.module_map,
            threshold_ms=config.threshold_ms,
            sort_mode=arguments.sort,
            iterations=arguments.iterations,
        )

        tmpdir: str = TemporaryDirectory(delete=False).name
        db_path = str(Path(tmpdir) / "profile_database.toml")
        db_path_obj = Path(db_path)

        def setup_fn() -> SetupReturn:
            return get_db(db_path, arguments.iterations)

        def workload(db: ProfileDB, iterations: int) -> ProfileDB:
            return run_crud_operations(db, iterations)

        def teardown_fn(db: ProfileDB) -> None:
            db.close()
            if db_path_obj.exists():
                db_path_obj.unlink()

        def workload_wrapper() -> None:
            setup_return: SetupReturn = setup_fn()
            try:
                workload(setup_return.db, setup_return.iterations)
            finally:
                teardown_fn(setup_return.db)

        if arguments.full:
            profiler.run(
                workload_wrapper,
                stats_file=config.stats_file,
            )
        else:
            profiler.run(
                workload,
                stats_file=config.stats_file,
                setup_fn=setup_fn,
                teardown_fn=teardown_fn,
            )

        color_config = DefaultColorConfig()
        color_config.update_thresholds(mid=0.7)
        color_gradient = ColorGradient(config=color_config, reverse=True)
        sort_mode = SortMode(arguments.sort)

        display_all(
            profiler,
            top_n=arguments.top,
            console=console,
            color_gradient=color_gradient,
            sort_mode=sort_mode,
            decimal_precision=config.decimal_precision,
            dependency_search=arguments.search,
        )

        config.cleanup()

        return SUCCESS
    except Exception:
        console.print_exception()
        return FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
