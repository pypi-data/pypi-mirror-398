# Foreign Key Constraints

Bear Shelf provides comprehensive foreign key (FK) support with referential integrity enforcement, matching the behavior of production databases like PostgreSQL and MySQL.

## Overview

Foreign keys establish relationships between tables and ensure data consistency through referential integrity. Bear Shelf supports all standard SQL foreign key actions for both DELETE and UPDATE operations.

## Defining Foreign Keys

Use SQLAlchemy's `ForeignKey` to define relationships between tables:

```python
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

# Create database
engine = create_engine("bearshelf:///blog.jsonl")
Base.metadata.create_all(engine)
```

## Referential Integrity on INSERT/UPDATE

Bear Shelf automatically validates foreign key references on INSERT and UPDATE operations:

```python
with Session(engine) as session:
    # This raises IntegrityError - user 999 doesn't exist
    post = Post(title="Invalid Post", author_id=999)
    session.add(post)
    session.commit()  # ❌ IntegrityError!
```

**Valid insert:**
```python
with Session(engine) as session:
    # Create parent first
    user = User(name="Bear")
    session.add(user)
    session.flush()  # Get the ID

    # Now create child with valid FK
    post = Post(title="My First Post", author_id=user.id)
    session.add(post)
    session.commit()  # ✅ Success!
```

## ON DELETE Actions

Control what happens to child records when a parent is deleted using `ondelete` parameter.

### CASCADE - Delete Children

Automatically delete all child records when the parent is deleted:

```python
class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
```

```python
with Session(engine) as session:
    # Delete organization
    org = session.query(Organization).filter_by(name="Acme").first()
    session.delete(org)
    session.commit()

    # All teams in that organization are automatically deleted! 🔥
```

**Multi-level CASCADE** works recursively through entire hierarchies:
```
Company (deleted)
  └─> Department (CASCADE deleted)
        └─> Employee (CASCADE deleted)
```

### SET NULL - Nullify References

Set child foreign keys to NULL when parent is deleted (requires nullable FK):

```python
class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("authors.id", ondelete="SET NULL"),
        nullable=True  # ⚠️ Required for SET NULL!
    )
```

```python
with Session(engine) as session:
    # Delete author
    author = session.query(Author).filter_by(name="Bear").first()
    session.delete(author)
    session.commit()

    # Blog posts still exist, but author_id is now NULL
    posts = session.query(BlogPost).all()
    for post in posts:
        print(post.author_id)  # None
```

### RESTRICT - Prevent Deletion (Default)

Prevent parent deletion if children exist. This is the **default behavior**:

```python
class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    dept_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    # ondelete defaults to RESTRICT
```

```python
with Session(engine) as session:
    dept = session.query(Department).filter_by(name="Engineering").first()
    session.delete(dept)
    session.commit()  # ❌ IntegrityError if employees exist!
```

### NO ACTION - Allow Orphans

Allow deletion without checking children, creating orphaned records:

```python
class Vendor(Base):
    __tablename__ = "vendors"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id", ondelete="NO ACTION")
    )
```

```python
# Delete vendor - products become orphaned (vendor_id references non-existent record)
# ⚠️ Use with caution! This can lead to data inconsistency.
```

## ON UPDATE Actions

Control what happens to child records when a parent's **primary key** is updated using `onupdate` parameter.

### CASCADE - Update References

Automatically update child foreign keys when parent PK changes:

```python
class Region(Base):
    __tablename__ = "regions"
    code: Mapped[str] = mapped_column(primary_key=True)  # String PK
    name: Mapped[str]

class Store(Base):
    __tablename__ = "stores"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    region_code: Mapped[str] = mapped_column(
        ForeignKey("regions.code", onupdate="CASCADE")
    )
```

```python
from sqlalchemy import update

with Session(engine) as session:
    # Update parent PK from "US-WEST" to "US-W"
    stmt = update(Region).where(Region.code == "US-WEST").values(code="US-W")
    session.execute(stmt)
    session.commit()

    # All stores automatically updated to region_code="US-W" ✅
```

### SET NULL - Nullify on Update

Set child FKs to NULL when parent PK changes:

```python
class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("manufacturers.id", onupdate="SET NULL"),
        nullable=True
    )
```

### RESTRICT - Prevent PK Updates

Prevent parent PK updates if children exist:

```python
class License(Base):
    __tablename__ = "licenses"
    key: Mapped[str] = mapped_column(primary_key=True)
    product: Mapped[str]

class Activation(Base):
    __tablename__ = "activations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    license_key: Mapped[str] = mapped_column(
        ForeignKey("licenses.key", onupdate="RESTRICT")
    )
```

## Self-Referential Foreign Keys

Use FKs to the same table for tree structures and hierarchies:

```python
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True  # NULL for root nodes
    )
```

```python
# Build tree: Electronics -> Laptops -> Gaming Laptops
with Session(engine) as session:
    electronics = Category(name="Electronics", parent_id=None)  # Root
    session.add(electronics)
    session.flush()

    laptops = Category(name="Laptops", parent_id=electronics.id)
    session.add(laptops)
    session.flush()

    gaming = Category(name="Gaming Laptops", parent_id=laptops.id)
    session.add(gaming)
    session.commit()

# Delete Electronics -> CASCADE deletes entire subtree! 🌳
```

## String Primary Keys

Foreign keys work seamlessly with string primary keys:

```python
class Country(Base):
    __tablename__ = "countries"
    code: Mapped[str] = mapped_column(primary_key=True)  # "US", "CA", etc.
    name: Mapped[str]

class City(Base):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    country_code: Mapped[str | None] = mapped_column(
        ForeignKey("countries.code", ondelete="SET NULL"),
        nullable=True
    )
```

## Action Reference Table

| Action | ON DELETE | ON UPDATE |
|--------|-----------|-----------|
| **CASCADE** | Recursively delete children | Update child FKs to new PK value |
| **SET NULL** | Set child FKs to NULL | Set child FKs to NULL |
| **RESTRICT** | Prevent delete if children exist (default) | Prevent PK update if children exist |
| **NO ACTION** | Allow delete, creating orphans | Allow PK update, orphaning children |

## Best Practices

1. **Use RESTRICT by default** - Prevents accidental data loss
2. **CASCADE carefully** - Understand the full deletion scope
3. **SET NULL for optional relationships** - When child can exist without parent
4. **Avoid NO ACTION** - Unless you have a specific use case for orphaned records
5. **Test with hierarchies** - Ensure CASCADE works through multiple levels
6. **Use nullable=True with SET NULL** - Required for proper operation

## Error Messages

Bear Shelf provides detailed error messages for FK violations:

```
IntegrityError: Foreign key constraint failed on column 'author_id':
value 123 not found in users.id
```

```
IntegrityError: Cannot delete from 'departments': 5 record(s) in 'employees'
reference it via 'dept_id'
```

```
IntegrityError: Cannot SET NULL on non-nullable column 'category_id'
in table 'products'
```

## Storage Format Independence

Foreign key constraints work identically across all storage formats:
- JSONL
- JSON
- XML
- YAML
- TOML
- MessagePack

The constraint enforcement happens at the SQLAlchemy dialect layer, ensuring consistent behavior regardless of underlying storage.

## Performance Considerations

- **INSERT/UPDATE validation**: O(1) lookup to check parent exists
- **DELETE CASCADE**: O(n) where n = total children across all levels
- **DELETE RESTRICT**: O(n) where n = direct children (stops at first match)
- **UPDATE CASCADE**: O(n) where n = total children with FK reference

For large hierarchies with CASCADE, consider batch operations or background processing.

## Migration from Other Databases

Bear Shelf's FK implementation matches PostgreSQL/MySQL semantics, making migrations straightforward:

```python
# PostgreSQL/MySQL syntax
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    author_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);

# Bear Shelf equivalent (SQLAlchemy)
class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
```

## Complete Example

```python
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

class Base(DeclarativeBase):
    pass

# Parent table
class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]

# Child with CASCADE
class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )

# Grandchild with SET NULL
class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    dept_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True
    )

# Setup
engine = create_engine("bearshelf:///company.jsonl")
Base.metadata.create_all(engine)

# Usage
with Session(engine) as session:
    # Create hierarchy
    company = Company(name="TechCorp")
    session.add(company)
    session.flush()

    dept = Department(name="Engineering", company_id=company.id)
    session.add(dept)
    session.flush()

    emp = Employee(name="Alice", dept_id=dept.id)
    session.add(emp)
    session.commit()

# Delete company -> dept CASCADE deleted, emp has dept_id=NULL
with Session(engine) as session:
    company = session.query(Company).first()
    session.delete(company)
    session.commit()

    # Check results
    assert session.query(Department).count() == 0  # CASCADE deleted

    emp = session.query(Employee).first()
    assert emp.dept_id is None  # SET NULL worked
```
