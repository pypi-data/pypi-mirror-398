"""Tests for foreign key referential integrity validation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import ForeignKey, Update, create_engine, update
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from bear_shelf.database import BearShelfDB

if TYPE_CHECKING:
    from sqlalchemy import Engine


class MockedDB4(BearShelfDB):
    """Mocked database class for testing."""


Base = MockedDB4.get_base()


class User(Base):
    """User model with integer PK."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]


class Post(Base):
    """Post model with FK to users."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class Comment(Base):
    """Comment model with nullable FK to users."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str]
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Article(Base):
    """Article model with multiple FKs."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """Create test engine with all tables."""
    db_file: Path = tmp_path / "fk_integrity_test.jsonl"
    engine: Engine = create_engine(f"bearshelf:///{db_file}")
    Base.metadata.create_all(engine)
    return engine


class TestFKIntegrityInsert:
    """Test FK integrity validation on INSERT operations."""

    def test_insert_with_nonexistent_fk_raises_error(self, engine: Engine) -> None:
        """INSERT with non-existent FK value should raise IntegrityError."""
        with Session(engine) as session:
            # Try to insert post with author_id that doesn't exist
            post = Post(title="Orphan Post", author_id=999)
            session.add(post)

            with pytest.raises(IntegrityError, match="Foreign key constraint failed"):
                session.commit()

    def test_insert_with_valid_fk_succeeds(self, engine: Engine) -> None:
        """INSERT with valid FK value should succeed."""
        with Session(engine) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()

            post = Post(title="Valid Post", author_id=user.id)
            session.add(post)
            session.commit()

            retrieved: Post | None = session.query(Post).filter_by(title="Valid Post").first()
            assert retrieved is not None
            assert retrieved.author_id == user.id

    def test_insert_null_into_nullable_fk_succeeds(self, engine: Engine) -> None:
        """INSERT with NULL into nullable FK should succeed."""
        with Session(engine) as session:
            comment = Comment(text="Anonymous comment", author_id=None)
            session.add(comment)
            session.commit()

            retrieved = session.query(Comment).first()
            assert retrieved is not None
            assert retrieved.author_id is None

    def test_bulk_insert_with_invalid_fk_raises_error(self, engine: Engine) -> None:
        """Bulk INSERT with any invalid FK should raise IntegrityError."""
        with Session(engine) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()
            user_id = user.id

            # Mix of valid and invalid FKs
            posts = [
                Post(title="Valid Post 1", author_id=user_id),
                Post(title="Invalid Post", author_id=999),  # Invalid!
                Post(title="Valid Post 2", author_id=user_id),
            ]
            session.add_all(posts)

            with pytest.raises(IntegrityError, match="Foreign key constraint failed"):
                session.commit()

    def test_insert_with_multiple_fks_all_valid_succeeds(self, engine: Engine) -> None:
        """INSERT with multiple valid FKs should succeed."""
        with Session(engine) as session:
            author = User(name="Bear")
            reviewer = User(name="Shannon")
            session.add_all([author, reviewer])
            session.flush()

            article = Article(title="Article", author_id=author.id, reviewer_id=reviewer.id)
            session.add(article)
            session.commit()

            retrieved = session.query(Article).first()
            assert retrieved is not None
            assert retrieved.author_id == author.id
            assert retrieved.reviewer_id == reviewer.id

    def test_insert_with_one_invalid_fk_of_multiple_raises_error(self, engine: Engine) -> None:
        """INSERT with one invalid FK among multiple should raise IntegrityError."""
        with Session(engine) as session:
            author = User(name="Bear")
            session.add(author)
            session.flush()

            # Valid author_id but invalid reviewer_id
            article = Article(title="Bad Article", author_id=author.id, reviewer_id=999)
            session.add(article)

            with pytest.raises(IntegrityError, match="Foreign key constraint failed"):
                session.commit()


class TestFKIntegrityUpdate:
    """Test FK integrity validation on UPDATE operations."""

    def test_update_to_nonexistent_fk_raises_error(self, engine: Engine) -> None:
        """UPDATE to non-existent FK value should raise IntegrityError."""
        with Session(engine, expire_on_commit=False) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()

            post = Post(title="Test Post", author_id=user.id)
            session.add(post)
            session.commit()

        # New session to update
        with Session(engine) as session:
            post = session.query(Post).filter_by(title="Test Post").first()
            assert post is not None

            post.author_id = 999  # Invalid FK

            with pytest.raises(IntegrityError, match="Foreign key constraint failed"):
                session.commit()

    def test_update_to_valid_fk_succeeds(self, engine: Engine) -> None:
        """UPDATE to valid FK value should succeed."""
        with Session(engine, expire_on_commit=False) as session:
            user1 = User(name="Bear")
            user2 = User(name="Shannon")
            session.add_all([user1, user2])
            session.flush()
            user1_id = user1.id
            user2_id = user2.id

            post = Post(title="Test Post", author_id=user1_id)
            session.add(post)
            session.commit()

        # Update to different valid user
        with Session(engine) as session:
            post = session.query(Post).filter_by(title="Test Post").first()
            assert post is not None
            assert post.author_id == user1_id

            post.author_id = user2_id
            session.commit()

            retrieved = session.query(Post).filter_by(title="Test Post").first()
            assert retrieved is not None
            assert retrieved.author_id == user2_id

    def test_update_nullable_fk_to_null_succeeds(self, engine: Engine) -> None:
        """UPDATE nullable FK to NULL should succeed."""
        with Session(engine, expire_on_commit=False) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()
            user_id = user.id

            comment = Comment(text="Test comment", author_id=user_id)
            session.add(comment)
            session.commit()

        # Update to NULL
        with Session(engine) as session:
            comment = session.query(Comment).first()
            assert comment is not None
            assert comment.author_id == user_id

            comment.author_id = None
            session.commit()

            retrieved = session.query(Comment).first()
            assert retrieved is not None
            assert retrieved.author_id is None

    def test_update_non_fk_field_with_valid_fk_succeeds(self, engine: Engine) -> None:
        """UPDATE non-FK field when FK is valid should succeed."""
        with Session(engine, expire_on_commit=False) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()
            user_id = user.id

            post = Post(title="Original Title", author_id=user_id)
            session.add(post)
            session.commit()

        # Update title only (FK stays valid)
        with Session(engine) as session:
            post = session.query(Post).filter_by(title="Original Title").first()
            assert post is not None

            post.title = "Updated Title"
            session.commit()

            retrieved = session.query(Post).filter_by(title="Updated Title").first()
            assert retrieved is not None
            assert retrieved.author_id == user_id


class TestFKIntegrityEdgeCases:
    """Test edge cases for FK integrity validation."""

    def test_fk_to_zero_id_works_if_exists(self, engine: Engine) -> None:
        """FK value of 0 should work if a record with id=0 exists."""
        with Session(engine) as session:
            # Manually insert user with id=0 using raw SQL through BearBase
            user = User(name="Zero User")
            session.add(user)
            session.flush()

            # If auto-increment gives us 0 (unlikely), use it; otherwise skip test
            if user.id == 0:
                post = Post(title="Zero FK Post", author_id=0)
                session.add(post)
                session.commit()

                retrieved = session.query(Post).first()
                assert retrieved is not None
                assert retrieved.author_id == 0

    def test_string_pk_fk_integrity(self, tmp_path: Path) -> None:
        """FK integrity should work with string primary keys."""

        class StringBase(DeclarativeBase):
            """Base for string PK models."""

        class Account(StringBase):
            __tablename__ = "accounts"

            email: Mapped[str] = mapped_column(primary_key=True)
            name: Mapped[str]

        class Order(StringBase):
            __tablename__ = "orders"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            description: Mapped[str]
            account_email: Mapped[str] = mapped_column(ForeignKey("accounts.email"))

        db_file = tmp_path / "string_pk_fk_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        StringBase.metadata.create_all(engine)

        # Test invalid FK
        with Session(engine) as session:
            order = Order(description="Test Order", account_email="nonexistent@example.com")
            session.add(order)

            with pytest.raises(IntegrityError, match="Foreign key constraint failed"):
                session.commit()

        # Test valid FK
        with Session(engine) as session:
            account = Account(email="bear@example.com", name="Bear")
            session.add(account)
            session.commit()

        with Session(engine) as session:
            order = Order(description="Valid Order", account_email="bear@example.com")
            session.add(order)
            session.commit()

            retrieved = session.query(Order).first()
            assert retrieved is not None
            assert retrieved.account_email == "bear@example.com"

    def test_error_message_contains_useful_info(self, engine: Engine) -> None:
        """IntegrityError message should contain table, column, and value info."""
        with Session(engine) as session:
            post = Post(title="Test", author_id=123)
            session.add(post)

            with pytest.raises(
                IntegrityError,
                match=r"Foreign key constraint failed on column 'author_id'.*value 123.*users\.id",
            ):
                session.commit()


class TestFKIntegrityDelete:
    """Test FK integrity validation on DELETE operations."""

    def test_delete_parent_with_children_raises_restrict_error(self, engine: Engine) -> None:
        """DELETE parent record with children should raise IntegrityError (RESTRICT)."""
        with Session(engine, expire_on_commit=False) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()
            user_id = user.id

            post = Post(title="Test Post", author_id=user_id)
            session.add(post)
            session.commit()

        # Try to delete the parent user
        with Session(engine) as session:
            user = session.query(User).filter_by(name="Bear").first()
            assert user is not None

            session.delete(user)

            with pytest.raises(IntegrityError, match=r"Cannot delete.*posts.*reference it"):
                session.commit()

    def test_delete_parent_without_children_succeeds(self, engine: Engine) -> None:
        """DELETE parent record without children should succeed."""
        with Session(engine) as session:
            user = User(name="Bear")
            session.add(user)
            session.commit()

        # Delete the user (no posts reference it)
        with Session(engine) as session:
            user = session.query(User).filter_by(name="Bear").first()
            assert user is not None

            session.delete(user)
            session.commit()

            # Verify deletion
            user = session.query(User).filter_by(name="Bear").first()
            assert user is None

    def test_delete_parent_with_multiple_children_raises_error(self, engine: Engine) -> None:
        """DELETE parent with multiple child records should raise IntegrityError."""
        with Session(engine, expire_on_commit=False) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()
            user_id = user.id

            post1 = Post(title="Post 1", author_id=user_id)
            post2 = Post(title="Post 2", author_id=user_id)
            post3 = Post(title="Post 3", author_id=user_id)
            session.add_all([post1, post2, post3])
            session.commit()

        # Try to delete the parent
        with Session(engine) as session:
            user = session.query(User).filter_by(name="Bear").first()
            assert user is not None

            session.delete(user)

            with pytest.raises(IntegrityError, match=r"3 record.*posts"):
                session.commit()

    def test_delete_child_record_succeeds(self, engine: Engine) -> None:
        """DELETE child record should succeed (doesn't affect parent)."""
        with Session(engine, expire_on_commit=False) as session:
            user = User(name="Bear")
            session.add(user)
            session.flush()
            user_id = user.id

            post = Post(title="Test Post", author_id=user_id)
            session.add(post)
            session.commit()

        # Delete the child post
        with Session(engine) as session:
            post = session.query(Post).filter_by(title="Test Post").first()
            assert post is not None

            session.delete(post)
            session.commit()

            # Parent should still exist
            user = session.query(User).filter_by(name="Bear").first()
            assert user is not None


class TestFKOnDeleteSetNull:
    """Test ON DELETE SET NULL behavior."""

    def test_delete_parent_with_set_null_updates_children_to_null(self, tmp_path: Path) -> None:
        """DELETE parent with ondelete='SET NULL' should set child FKs to NULL."""

        class SetNullBase(DeclarativeBase):
            """Base for SET NULL FK models."""

        class Author(SetNullBase):
            __tablename__ = "authors"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class BlogPost(SetNullBase):
            __tablename__ = "blog_posts"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            title: Mapped[str]
            author_id: Mapped[int | None] = mapped_column(ForeignKey("authors.id", ondelete="SET NULL"), nullable=True)

        db_file = tmp_path / "set_null_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        SetNullBase.metadata.create_all(engine)

        # Insert parent and children
        with Session(engine, expire_on_commit=False) as session:
            author = Author(name="Bear")
            session.add(author)
            session.flush()
            author_id = author.id

            post1 = BlogPost(title="Post 1", author_id=author_id)
            post2 = BlogPost(title="Post 2", author_id=author_id)
            session.add_all([post1, post2])
            session.commit()

        # Delete the parent
        with Session(engine) as session:
            author = session.query(Author).filter_by(name="Bear").first()
            assert author is not None

            session.delete(author)
            session.commit()

        # Verify children's FKs are set to NULL
        with Session(engine) as session:
            posts = session.query(BlogPost).all()
            assert len(posts) == 2
            for post in posts:
                assert post.author_id is None

    def test_delete_parent_with_set_null_on_non_nullable_raises_error(self, tmp_path: Path) -> None:
        """DELETE parent with ondelete='SET NULL' on non-nullable FK should raise IntegrityError."""

        class SetNullBase(DeclarativeBase):
            """Base for SET NULL FK models."""

        class Category(SetNullBase):
            __tablename__ = "categories"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Product(SetNullBase):
            __tablename__ = "products"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            # Non-nullable FK with SET NULL - should fail!
            category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=False)

        db_file = tmp_path / "set_null_nonnullable_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        SetNullBase.metadata.create_all(engine)

        # Insert parent and child
        with Session(engine, expire_on_commit=False) as session:
            category = Category(name="Electronics")
            session.add(category)
            session.flush()
            category_id = category.id

            product = Product(name="Laptop", category_id=category_id)
            session.add(product)
            session.commit()

        # Try to delete parent - should fail because FK is non-nullable
        with Session(engine) as session:
            category = session.query(Category).filter_by(name="Electronics").first()
            assert category is not None

            session.delete(category)

            with pytest.raises(IntegrityError, match="Cannot SET NULL on non-nullable column"):
                session.commit()

    def test_delete_multiple_parents_with_set_null(self, tmp_path: Path) -> None:
        """DELETE multiple parents with SET NULL should update all affected children."""

        class SetNullBase(DeclarativeBase):
            """Base for SET NULL FK models."""

        class Department(SetNullBase):
            __tablename__ = "departments"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Employee(SetNullBase):
            __tablename__ = "employees"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            dept_id: Mapped[int | None] = mapped_column(
                ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
            )

        db_file = tmp_path / "multi_set_null_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        SetNullBase.metadata.create_all(engine)

        # Insert multiple parents and children
        with Session(engine, expire_on_commit=False) as session:
            dept1 = Department(name="Engineering")
            dept2 = Department(name="Sales")
            session.add_all([dept1, dept2])
            session.flush()
            dept1_id = dept1.id
            dept2_id = dept2.id

            emp1 = Employee(name="Alice", dept_id=dept1_id)
            emp2 = Employee(name="Bob", dept_id=dept1_id)
            emp3 = Employee(name="Charlie", dept_id=dept2_id)
            session.add_all([emp1, emp2, emp3])
            session.commit()

        # Delete dept1 only
        with Session(engine) as session:
            dept = session.query(Department).filter_by(name="Engineering").first()
            assert dept is not None

            session.delete(dept)
            session.commit()

        # Verify only dept1's employees have NULL, dept2's employee is unchanged
        with Session(engine, expire_on_commit=False) as session:
            alice: Employee | None = session.query(Employee).filter_by(name="Alice").first()
            bob: Employee | None = session.query(Employee).filter_by(name="Bob").first()
            charlie: Employee | None = session.query(Employee).filter_by(name="Charlie").first()

            assert alice is not None
            assert alice.dept_id is None
            assert bob is not None
            assert bob.dept_id is None
            assert charlie is not None
            assert charlie.dept_id == dept2_id

    def test_set_null_with_string_primary_key(self, tmp_path: Path) -> None:
        """ON DELETE SET NULL should work with string primary keys."""

        class SetNullBase(DeclarativeBase):
            """Base for SET NULL FK models."""

        class Country(SetNullBase):
            __tablename__ = "countries"

            code: Mapped[str] = mapped_column(primary_key=True)
            name: Mapped[str]

        class City(SetNullBase):
            __tablename__ = "cities"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            country_code: Mapped[str | None] = mapped_column(
                ForeignKey("countries.code", ondelete="SET NULL"), nullable=True
            )

        db_file = tmp_path / "set_null_string_pk_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        SetNullBase.metadata.create_all(engine)

        # Insert parent and children
        with Session(engine) as session:
            country = Country(code="US", name="United States")
            session.add(country)
            session.commit()

        with Session(engine) as session:
            city1 = City(name="New York", country_code="US")
            city2 = City(name="Los Angeles", country_code="US")
            session.add_all([city1, city2])
            session.commit()

        # Delete the parent
        with Session(engine) as session:
            country = session.query(Country).filter_by(code="US").first()
            assert country is not None

            session.delete(country)
            session.commit()

        # Verify children's FKs are set to NULL
        with Session(engine) as session:
            cities = session.query(City).all()
            assert len(cities) == 2
            for city in cities:
                assert city.country_code is None


class TestFKOnDeleteCascade:
    """Test ON DELETE CASCADE behavior."""

    def test_delete_parent_with_cascade_deletes_children(self, tmp_path: Path) -> None:
        """DELETE parent with CASCADE should delete all child records."""

        class CascadeBase(DeclarativeBase):
            """Base for CASCADE FK models."""

        class Organization(CascadeBase):
            __tablename__ = "organizations"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Team(CascadeBase):
            __tablename__ = "teams"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))

        db_file = tmp_path / "cascade_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        CascadeBase.metadata.create_all(engine)

        # Insert parent and children
        with Session(engine, expire_on_commit=False) as session:
            org = Organization(name="Acme Corp")
            session.add(org)
            session.flush()
            org_id = org.id

            team1 = Team(name="Engineering", org_id=org_id)
            team2 = Team(name="Sales", org_id=org_id)
            session.add_all([team1, team2])
            session.commit()

        # Delete the parent
        with Session(engine) as session:
            org = session.query(Organization).filter_by(name="Acme Corp").first()
            assert org is not None

            session.delete(org)
            session.commit()

        # Verify children are deleted
        with Session(engine) as session:
            teams = session.query(Team).all()
            assert len(teams) == 0

            orgs = session.query(Organization).all()
            assert len(orgs) == 0

    def test_cascade_with_multiple_levels(self, tmp_path: Path) -> None:
        """CASCADE should work recursively through multiple FK levels."""

        class CascadeBase(DeclarativeBase):
            """Base for CASCADE FK models."""

        class Company(CascadeBase):
            __tablename__ = "companies"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Department(CascadeBase):
            __tablename__ = "departments"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))

        class Employee(CascadeBase):
            __tablename__ = "employees"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            dept_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"))

        db_file = tmp_path / "cascade_multilevel_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        CascadeBase.metadata.create_all(engine)

        # Insert 3-level hierarchy
        with Session(engine, expire_on_commit=False) as session:
            company = Company(name="TechCorp")
            session.add(company)
            session.flush()
            company_id = company.id

            dept1 = Department(name="Engineering", company_id=company_id)
            dept2 = Department(name="Sales", company_id=company_id)
            session.add_all([dept1, dept2])
            session.flush()
            dept1_id = dept1.id
            dept2_id = dept2.id

            emp1 = Employee(name="Alice", dept_id=dept1_id)
            emp2 = Employee(name="Bob", dept_id=dept1_id)
            emp3 = Employee(name="Charlie", dept_id=dept2_id)
            session.add_all([emp1, emp2, emp3])
            session.commit()

        # Delete the top-level parent
        with Session(engine) as session:
            company = session.query(Company).filter_by(name="TechCorp").first()
            assert company is not None

            session.delete(company)
            session.commit()

        # Verify entire hierarchy is deleted
        with Session(engine) as session:
            assert len(session.query(Employee).all()) == 0
            assert len(session.query(Department).all()) == 0
            assert len(session.query(Company).all()) == 0

    def test_cascade_preserves_unrelated_records(self, tmp_path: Path) -> None:
        """CASCADE should only delete related children, not unrelated records."""

        class CascadeBase(DeclarativeBase):
            """Base for CASCADE FK models."""

        class Project(CascadeBase):
            __tablename__ = "projects"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Task(CascadeBase):
            __tablename__ = "tasks"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            description: Mapped[str]
            project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

        db_file = tmp_path / "cascade_selective_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        CascadeBase.metadata.create_all(engine)

        # Insert multiple parents with children
        with Session(engine, expire_on_commit=False) as session:
            project1 = Project(name="Project Alpha")
            project2 = Project(name="Project Beta")
            session.add_all([project1, project2])
            session.flush()
            p1_id = project1.id
            p2_id = project2.id

            task1 = Task(description="Alpha Task 1", project_id=p1_id)
            task2 = Task(description="Alpha Task 2", project_id=p1_id)
            task3 = Task(description="Beta Task 1", project_id=p2_id)
            session.add_all([task1, task2, task3])
            session.commit()

        # Delete only project1
        with Session(engine) as session:
            project = session.query(Project).filter_by(name="Project Alpha").first()
            assert project is not None

            session.delete(project)
            session.commit()

        # Verify only project1's tasks are deleted
        with Session(engine) as session:
            projects = session.query(Project).all()
            assert len(projects) == 1
            assert projects[0].name == "Project Beta"

            tasks = session.query(Task).all()
            assert len(tasks) == 1
            assert tasks[0].description == "Beta Task 1"

    def test_cascade_with_string_primary_key(self, tmp_path: Path) -> None:
        """CASCADE should work with string primary keys."""

        class CascadeBase(DeclarativeBase):
            """Base for CASCADE FK models."""

        class Account(CascadeBase):
            __tablename__ = "accounts"

            username: Mapped[str] = mapped_column(primary_key=True)
            email: Mapped[str]

        class UserSession(CascadeBase):
            __tablename__ = "sessions"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            token: Mapped[str]
            username: Mapped[str] = mapped_column(ForeignKey("accounts.username", ondelete="CASCADE"))

        db_file = tmp_path / "cascade_string_pk_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        CascadeBase.metadata.create_all(engine)

        # Insert parent and children
        with Session(engine) as session:
            account = Account(username="bear", email="bear@example.com")
            session.add(account)
            session.commit()

        with Session(engine) as session:
            sess1 = UserSession(token="token1", username="bear")  # noqa: S106
            sess2 = UserSession(token="token2", username="bear")  # noqa: S106
            session.add_all([sess1, sess2])
            session.commit()

        # Delete the parent
        with Session(engine) as session:
            account = session.query(Account).filter_by(username="bear").first()
            assert account is not None

            session.delete(account)
            session.commit()

        # Verify children are deleted
        with Session(engine) as session:
            sessions = session.query(UserSession).all()
            assert len(sessions) == 0


class TestFKOnDeleteNoAction:
    """Test ON DELETE NO ACTION behavior."""

    def test_delete_parent_with_no_action_creates_orphans(self, tmp_path: Path) -> None:
        """DELETE parent with NO_ACTION should allow orphaned records."""

        class NoActionBase(DeclarativeBase):
            """Base for NO_ACTION FK models."""

        class Vendor(NoActionBase):
            __tablename__ = "vendors"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]

        class Product(NoActionBase):
            __tablename__ = "products"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="NO ACTION"))

        db_file = tmp_path / "no_action_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        NoActionBase.metadata.create_all(engine)

        # Insert parent and children
        with Session(engine, expire_on_commit=False) as session:
            vendor = Vendor(name="Acme Corp")
            session.add(vendor)
            session.flush()
            vendor_id = vendor.id

            prod1 = Product(name="Widget", vendor_id=vendor_id)
            prod2 = Product(name="Gadget", vendor_id=vendor_id)
            session.add_all([prod1, prod2])
            session.commit()

        # Delete the parent (should succeed with NO_ACTION)
        with Session(engine) as session:
            vendor = session.query(Vendor).filter_by(name="Acme Corp").first()
            assert vendor is not None

            session.delete(vendor)
            session.commit()

        # Verify children still exist (orphaned)
        with Session(engine, expire_on_commit=False) as session:
            products = session.query(Product).all()
            assert len(products) == 2
            # Products now reference non-existent vendor_id (orphans)
            assert all(p.vendor_id == vendor_id for p in products)


class TestFKOnUpdateCascade:
    """Test ON UPDATE CASCADE behavior."""

    def test_update_parent_pk_with_cascade_updates_children(self, tmp_path: Path) -> None:
        """UPDATE parent PK with CASCADE should update all child FK references."""

        class UpdateBase(DeclarativeBase):
            """Base for ON UPDATE CASCADE models."""

        class Region(UpdateBase):
            __tablename__ = "regions"

            code: Mapped[str] = mapped_column(primary_key=True)
            name: Mapped[str]

        class Store(UpdateBase):
            __tablename__ = "stores"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            region_code: Mapped[str] = mapped_column(ForeignKey("regions.code", onupdate="CASCADE"))

        db_file = tmp_path / "update_cascade_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        UpdateBase.metadata.create_all(engine)

        # Insert parent and children
        with Session(engine) as session:
            region = Region(code="US-WEST", name="Western Region")
            session.add(region)
            session.commit()

        with Session(engine) as session:
            store1 = Store(name="Store 1", region_code="US-WEST")
            store2 = Store(name="Store 2", region_code="US-WEST")
            session.add_all([store1, store2])
            session.commit()

        with Session(engine) as session:
            stmt: Update = update(Region).where(Region.code == "US-WEST").values(code="US-W")
            session.execute(stmt)
            session.commit()

        with Session(engine) as session:
            stores: list[Store] = session.query(Store).all()
            assert len(stores) == 2
            for store in stores:
                assert store.region_code == "US-W"

    def test_update_parent_pk_with_set_null_nullifies_children(self, tmp_path: Path) -> None:
        """UPDATE parent PK with SET NULL should set child FKs to NULL."""

        class UpdateBase(DeclarativeBase):
            """Base for ON UPDATE SET NULL models."""

        class Manufacturer(UpdateBase):
            __tablename__ = "manufacturers"

            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        class Device(UpdateBase):
            __tablename__ = "devices"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            manufacturer_id: Mapped[int | None] = mapped_column(
                ForeignKey("manufacturers.id", onupdate="SET NULL"), nullable=True
            )

        db_file = tmp_path / "update_set_null_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        UpdateBase.metadata.create_all(engine)

        # Insert parent and children
        with Session(engine, expire_on_commit=False) as session:
            mfg = Manufacturer(id=100, name="TechCorp")
            session.add(mfg)
            session.commit()

        with Session(engine) as session:
            device1 = Device(name="Device 1", manufacturer_id=100)
            device2 = Device(name="Device 2", manufacturer_id=100)
            session.add_all([device1, device2])
            session.commit()

        with Session(engine) as session:
            stmt: Update = update(Manufacturer).where(Manufacturer.id == 100).values(id=200)
            session.execute(stmt)
            session.commit()

        # Verify children's FKs are set to NULL
        with Session(engine) as session:
            devices = session.query(Device).all()
            assert len(devices) == 2
            for device in devices:
                assert device.manufacturer_id is None

    def test_update_parent_pk_with_restrict_raises_error(self, tmp_path: Path) -> None:
        """UPDATE parent PK with RESTRICT should raise IntegrityError if children exist."""

        class UpdateBase(DeclarativeBase):
            """Base for ON UPDATE RESTRICT models."""

        class License(UpdateBase):
            __tablename__ = "licenses"

            key: Mapped[str] = mapped_column(primary_key=True)
            product: Mapped[str]

        class Activation(UpdateBase):
            __tablename__ = "activations"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            device: Mapped[str]
            license_key: Mapped[str] = mapped_column(ForeignKey("licenses.key", onupdate="RESTRICT"))

        db_file = tmp_path / "update_restrict_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        UpdateBase.metadata.create_all(engine)

        # Insert parent and child
        with Session(engine) as session:
            lic = License(key="ABC-123", product="Software")
            session.add(lic)
            session.commit()

        with Session(engine) as session:
            activation = Activation(device="Device1", license_key="ABC-123")
            session.add(activation)
            session.commit()

        # Try to update parent PK - should fail
        with Session(engine) as session:
            stmt = update(License).where(License.key == "ABC-123").values(key="XYZ-789")

            with pytest.raises(IntegrityError, match=r"Cannot update PK.*activations.*reference it"):  # noqa: PT012
                session.execute(stmt)
                session.commit()


class TestFKSelfReferential:
    """Test self-referential foreign keys (tree structures)."""

    def test_self_referential_fk_with_cascade_delete(self, tmp_path: Path) -> None:
        """Self-referential FK with CASCADE should delete entire subtree."""

        class TreeBase(DeclarativeBase):
            """Base for tree structure models."""

        class Category(TreeBase):
            __tablename__ = "categories"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            parent_id: Mapped[int | None] = mapped_column(
                ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
            )

        db_file = tmp_path / "self_ref_cascade_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        TreeBase.metadata.create_all(engine)

        # Build tree: Root -> Child1 -> Grandchild1
        #                  -> Child2
        with Session(engine, expire_on_commit=False) as session:
            root = Category(name="Root")
            session.add(root)
            session.flush()
            root_id = root.id

            child1 = Category(name="Child1", parent_id=root_id)
            child2 = Category(name="Child2", parent_id=root_id)
            session.add_all([child1, child2])
            session.flush()
            child1_id = child1.id

            grandchild = Category(name="Grandchild1", parent_id=child1_id)
            session.add(grandchild)
            session.commit()

        # Delete root - should cascade delete entire tree
        with Session(engine) as session:
            root = session.query(Category).filter_by(name="Root").first()
            assert root is not None

            session.delete(root)
            session.commit()

        # Verify all categories deleted
        with Session(engine) as session:
            assert len(session.query(Category).all()) == 0

    def test_self_referential_fk_allows_null_parent(self, tmp_path: Path) -> None:
        """Self-referential FK should allow NULL parent (root nodes)."""

        class TreeBase(DeclarativeBase):
            """Base for tree structure models."""

        class Node(TreeBase):
            __tablename__ = "nodes"

            id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
            name: Mapped[str]
            parent_id: Mapped[int | None] = mapped_column(ForeignKey("nodes.id"), nullable=True)

        db_file = tmp_path / "self_ref_null_test.jsonl"
        engine = create_engine(f"bearshelf:///{db_file}")
        TreeBase.metadata.create_all(engine)

        # Insert root node with NULL parent
        with Session(engine) as session:
            root = Node(name="Root", parent_id=None)
            session.add(root)
            session.commit()

        # Verify root exists with NULL parent
        with Session(engine) as session:
            root = session.query(Node).filter_by(name="Root").first()
            assert root is not None
            assert root.parent_id is None
