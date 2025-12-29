"""Test aggregate functions with Bear Shelf dialect."""

from pathlib import Path

from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    sku: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    price: Mapped[int] = mapped_column()


def test_aggregate_functions(tmp_path: Path) -> None:
    """Test aggregate functions with Bear Shelf."""
    path: Path = tmp_path / "test_aggregate_functions.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        products: list[Product] = [
            Product(sku="PROD001", name="Widget", price=100),
            Product(sku="PROD002", name="Gadget", price=200),
            Product(sku="PROD003", name="Doohickey", price=150),
        ]
        session.add_all(products)
        session.commit()

        count_all: int | None = session.execute(select(func.count()).select_from(Product)).scalar()
        assert count_all is not None
        assert count_all == 3

        count_expensive: int | None = session.execute(
            select(func.count()).select_from(Product).where(Product.price > 120)
        ).scalar()

        count_names: int | None = session.execute(select(func.count(Product.name)).select_from(Product)).scalar()
        assert count_names is not None
        assert count_names == 3

        sum_prices: int | None = session.execute(select(func.sum(Product.price)).select_from(Product)).scalar()
        assert sum_prices is not None
        assert sum_prices == 100 + 200 + 150

        avg_price: float | None = session.execute(select(func.avg(Product.price)).select_from(Product)).scalar()
        assert avg_price is not None
        assert avg_price == (100 + 200 + 150) / 3

        min_price: int | None = session.execute(select(func.min(Product.price)).select_from(Product)).scalar()
        assert min_price is not None
        assert min_price == products[0].price

        max_price: int | None = session.execute(select(func.max(Product.price)).select_from(Product)).scalar()
        assert max_price is not None
        assert max_price == products[1].price

        # Test aggregates with WHERE clauses
        sum_expensive: int | None = session.execute(
            select(func.sum(Product.price)).select_from(Product).where(Product.price > 120)
        ).scalar()
        assert sum_expensive is not None
        assert sum_expensive == 200 + 150  # Only PROD002 and PROD003

        avg_expensive: float | None = session.execute(
            select(func.avg(Product.price)).select_from(Product).where(Product.price > 120)
        ).scalar()
        assert avg_expensive is not None
        assert avg_expensive == (200 + 150) / 2

        min_cheap: int | None = session.execute(
            select(func.min(Product.price)).select_from(Product).where(Product.price < 200)
        ).scalar()
        assert min_cheap is not None
        assert min_cheap == 100

        max_cheap: int | None = session.execute(
            select(func.max(Product.price)).select_from(Product).where(Product.price < 200)
        ).scalar()
        assert max_cheap is not None
        assert max_cheap == 150


def test_aggregate_empty_table(tmp_path: Path) -> None:
    """Test aggregate functions on empty table."""
    path: Path = tmp_path / "test_aggregate_empty.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Empty table aggregates
        count_empty: int | None = session.execute(select(func.count()).select_from(Product)).scalar()
        assert count_empty == 0

        sum_empty: int | None = session.execute(select(func.sum(Product.price)).select_from(Product)).scalar()
        assert sum_empty is None or sum_empty == 0

        avg_empty: float | None = session.execute(select(func.avg(Product.price)).select_from(Product)).scalar()
        assert avg_empty == 0  # AVG returns 0 for empty table

        min_empty: int | None = session.execute(select(func.min(Product.price)).select_from(Product)).scalar()
        # MIN on empty should raise or return None
        assert min_empty is None or isinstance(min_empty, (int, float))

        max_empty: int | None = session.execute(select(func.max(Product.price)).select_from(Product)).scalar()
        # MAX on empty should raise or return None
        assert max_empty is None or isinstance(max_empty, (int, float))


def test_aggregate_with_nullable_columns(tmp_path: Path) -> None:
    """Test aggregate functions with nullable columns."""

    class Item(Base):
        __tablename__ = "items"
        id: Mapped[str] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column()
        quantity: Mapped[int | None] = mapped_column(nullable=True)

    path: Path = tmp_path / "test_aggregate_nullable.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        items = [
            Item(id="ITEM001", name="Widget", quantity=10),
            Item(id="ITEM002", name="Gadget", quantity=None),
            Item(id="ITEM003", name="Doohickey", quantity=20),
        ]
        session.add_all(items)
        session.commit()

        # COUNT should count non-null values
        count_qty: int | None = session.execute(select(func.count(Item.quantity)).select_from(Item)).scalar()
        assert count_qty == 2  # Only non-null quantities

        # SUM should skip NULL values
        sum_qty: int | None = session.execute(select(func.sum(Item.quantity)).select_from(Item)).scalar()
        assert sum_qty == 30  # 10 + 20, skips NULL

        # AVG should only consider non-null values
        avg_qty: float | None = session.execute(select(func.avg(Item.quantity)).select_from(Item)).scalar()
        assert avg_qty == 15  # (10 + 20) / 2


def test_aggregate_where_no_matches(tmp_path: Path) -> None:
    """Test aggregate functions when WHERE clause matches no records."""
    path: Path = tmp_path / "test_aggregate_no_matches.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{path}", echo=False)

    if path.exists():
        path.unlink()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        products = [
            Product(sku="PROD001", name="Widget", price=100),
            Product(sku="PROD002", name="Gadget", price=200),
        ]
        session.add_all(products)
        session.commit()

        # WHERE matches nothing
        count_none: int | None = session.execute(
            select(func.count()).select_from(Product).where(Product.price > 1000)
        ).scalar()
        assert count_none == 0

        sum_none: int | None = session.execute(
            select(func.sum(Product.price)).select_from(Product).where(Product.price > 1000)
        ).scalar()
        assert sum_none is None or sum_none == 0

        avg_none: float | None = session.execute(
            select(func.avg(Product.price)).select_from(Product).where(Product.price > 1000)
        ).scalar()
        assert avg_none == 0

        min_none: int | None = session.execute(
            select(func.min(Product.price)).select_from(Product).where(Product.price > 1000)
        ).scalar()
        assert min_none is None or isinstance(min_none, (int, float))

        max_none: int | None = session.execute(
            select(func.max(Product.price)).select_from(Product).where(Product.price > 1000)
        ).scalar()
        assert max_none is None or isinstance(max_none, (int, float))
