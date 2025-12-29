"""Real-world example: Blog system with FK integrity validation.

Demonstrates how FK constraints prevent data integrity issues in a blog application.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import ForeignKey, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from bear_shelf.database import BearShelfDB


class MockedDB3(BearShelfDB):
    """Mocked database class for testing."""


Base = MockedDB3.get_base()


class User(Base):
    """Blog user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    email: Mapped[str]


class Post(Base):
    """Blog post written by a user."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    content: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class Comment(Base):
    """Comment on a post, optionally by a user."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str]
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


def main() -> None:
    """Demonstrate FK integrity validation in action."""
    # Create database
    db_path = Path("blog.jsonl")
    db_path.unlink(missing_ok=True)  # Clean start

    engine = create_engine(f"bearshelf:///{db_path}")
    Base.metadata.create_all(engine)

    print("=== Blog System with FK Integrity Validation ===\n")

    # ==================== Valid Operations ====================
    print("✅ Creating valid data...")
    with Session(engine) as session:
        # Create users
        bear = User(username="bear", email="bear@example.com")
        shannon = User(username="shannon", email="shannon@example.com")
        session.add_all([bear, shannon])
        session.flush()
        bear_id = bear.id
        shannon_id = shannon.id

        # Create post by bear
        post = Post(
            title="Welcome to Bear Shelf!",
            content="A lightweight database for small-scale apps",
            author_id=bear_id,
        )
        session.add(post)
        session.flush()
        post_id = post.id

        # Add comments (one with author, one anonymous)
        comment1 = Comment(text="Great post!", post_id=post_id, author_id=shannon_id)
        comment2 = Comment(text="Anonymous feedback", post_id=post_id, author_id=None)
        session.add_all([comment1, comment2])

        session.commit()
        print(f"  Created user '{bear.username}' (id={bear_id})")
        print(f"  Created user '{shannon.username}' (id={shannon_id})")
        print(f"  Created post '{post.title}' by user {bear_id}")
        print(f"  Created 2 comments on post {post_id}")

    # ==================== FK Violation: Non-existent Author ====================
    print("\n❌ Attempting to create post with non-existent author...")
    with Session(engine) as session:
        try:
            fake_post = Post(
                title="Orphan Post",
                content="This should fail",
                author_id=999,  # User 999 doesn't exist!
            )
            session.add(fake_post)
            session.commit()
            print("  ERROR: Should have raised IntegrityError!")
        except IntegrityError as e:
            print(f"  ✓ Caught IntegrityError: {e.args[0]}")

    # ==================== FK Violation: Invalid Update ====================
    print("\n❌ Attempting to reassign post to non-existent user...")
    with Session(engine) as session:
        try:
            post = session.execute(select(Post).where(Post.title == "Welcome to Bear Shelf!")).scalar_one()
            post.author_id = 777  # User 777 doesn't exist!
            session.commit()
            print("  ERROR: Should have raised IntegrityError!")
        except IntegrityError as e:
            print(f"  ✓ Caught IntegrityError: {e.args[0]}")

    # ==================== Valid Update ====================
    print("\n✅ Reassigning post to different valid user...")
    with Session(engine) as session:
        post = session.execute(select(Post).where(Post.title == "Welcome to Bear Shelf!")).scalar_one()
        original_author = post.author_id

        # Transfer post from bear to shannon
        post.author_id = shannon_id
        session.commit()
        print(f"  ✓ Post transferred from user {original_author} to user {shannon_id}")

    # ==================== Nullable FK: Set to NULL ====================
    print("\n✅ Removing author from comment (nullable FK)...")
    with Session(engine) as session:
        comment = session.execute(select(Comment).where(Comment.text == "Great post!")).scalar_one()
        comment.author_id = None  # Allowed because author_id is nullable
        session.commit()
        print("  ✓ Comment author set to NULL (anonymous)")

    # ==================== Data Integrity Preserved ====================
    print("\n=== Final Database State ===")
    with Session(engine) as session:
        users = session.execute(select(User)).scalars().all()
        posts = session.execute(select(Post)).scalars().all()
        comments = session.execute(select(Comment)).scalars().all()

        print(f"Users ({len(users)}):")
        for user in users:
            print(f"  - {user.username} (id={user.id})")

        print(f"\nPosts ({len(posts)}):")
        for post in posts:
            print(f"  - '{post.title}' by user {post.author_id}")

        print(f"\nComments ({len(comments)}):")
        for comment in comments:
            author_str = f"user {comment.author_id}" if comment.author_id else "anonymous"
            print(f"  - '{comment.text[:30]}...' on post {comment.post_id} by {author_str}")

    print("\n✓ All foreign keys are valid!")
    print(f"✓ Database saved to: {db_path.absolute()}")


if __name__ == "__main__":
    main()
