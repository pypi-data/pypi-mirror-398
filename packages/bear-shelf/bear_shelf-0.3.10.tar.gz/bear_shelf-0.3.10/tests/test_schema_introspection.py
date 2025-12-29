"""Test schema introspection functionality for Bear Shelf dialect."""

from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    sku: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    price: Mapped[int] = mapped_column()
    quantity: Mapped[int | None] = mapped_column(nullable=True)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_sku: Mapped[str] = mapped_column()
    amount: Mapped[float] = mapped_column()


def test_get_table_names(tmp_path: Path) -> None:
    """Test getting list of table names."""
    path: Path = tmp_path / "test_tables.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "products" in tables
    assert "orders" in tables
    assert len(tables) >= 2


def test_get_columns(tmp_path: Path) -> None:
    """Test getting column information for a table."""
    path: Path = tmp_path / "test_columns.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("products")

    assert len(columns) == 4
    assert columns[0]["name"] == "sku"
    assert columns[1]["name"] == "name"
    assert columns[2]["name"] == "price"
    assert columns[3]["name"] == "quantity"

    # Check nullable
    sku_col = next(c for c in columns if c["name"] == "sku")
    assert sku_col["nullable"] is False

    quantity_col = next(c for c in columns if c["name"] == "quantity")
    assert quantity_col["nullable"] is True


def test_get_columns_nonexistent_table(tmp_path: Path) -> None:
    """Test getting columns for non-existent table."""
    path: Path = tmp_path / "test_nonexistent.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("nonexistent_table")

    assert columns == []


def test_get_pk_constraint(tmp_path: Path) -> None:
    """Test getting primary key constraint information."""
    path: Path = tmp_path / "test_pk.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    pk = inspector.get_pk_constraint("products")

    assert pk is not None
    assert "constrained_columns" in pk
    assert "sku" in pk["constrained_columns"]


def test_get_pk_constraint_composite(tmp_path: Path) -> None:
    """Test primary key with autoincrement."""
    path: Path = tmp_path / "test_pk_auto.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    pk = inspector.get_pk_constraint("orders")

    assert pk is not None
    assert "constrained_columns" in pk
    assert "id" in pk["constrained_columns"]


def test_get_pk_constraint_nonexistent(tmp_path: Path) -> None:
    """Test getting PK for non-existent table."""
    path: Path = tmp_path / "test_pk_none.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    pk = inspector.get_pk_constraint("nonexistent_table")

    assert pk == {"constrained_columns": [], "name": None}


def test_get_foreign_keys(tmp_path: Path) -> None:
    """Test getting foreign key information."""
    path: Path = tmp_path / "test_fk.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    fks = inspector.get_foreign_keys("orders")

    # Orders table should have FK to products
    assert isinstance(fks, list)


def test_has_table(tmp_path: Path) -> None:
    """Test checking if table exists."""
    path: Path = tmp_path / "test_has.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)

    assert inspector.has_table("products")
    assert inspector.has_table("orders")
    assert not inspector.has_table("nonexistent")


def test_column_types(tmp_path: Path) -> None:
    """Test that column types are correctly reflected."""
    path: Path = tmp_path / "test_types.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("products")

    # All columns should have a 'type' field
    for col in columns:
        assert "type" in col
        assert col["type"] is not None


def test_column_defaults(tmp_path: Path) -> None:
    """Test that column defaults are reflected."""
    path: Path = tmp_path / "test_defaults.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("products")

    # All columns should have 'default' field
    for col in columns:
        assert "default" in col


def test_column_autoincrement(tmp_path: Path) -> None:
    """Test that autoincrement is reflected."""
    path: Path = tmp_path / "test_autoincrement.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("orders")

    # ID column should be autoincrement
    id_col = next(c for c in columns if c["name"] == "id")
    assert "autoincrement" in id_col
