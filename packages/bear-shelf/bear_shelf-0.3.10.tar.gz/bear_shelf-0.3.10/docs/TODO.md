# Bear Shelf TODO - Road to Feature Completeness 🚀

This document outlines missing features to make Bear Shelf competitive with SQLite, PostgreSQL, and other production databases.

## 🔥 High Priority - Core Database Features

### Query Features
- [ ] **JOIN Operations** - INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN
  - Critical for multi-table queries
  - Most requested SQL feature
  - Example: `SELECT * FROM users JOIN posts ON users.id = posts.author_id`

- [x] **Aggregate Functions** - COUNT(), SUM(), AVG(), MIN(), MAX()
  - Essential for analytics and reporting
  - Example: `SELECT COUNT(*) FROM users WHERE age > 18`

- [ ] **GROUP BY / HAVING** - Grouped aggregations
  - Required for meaningful aggregate queries
  - Example: `SELECT author_id, COUNT(*) FROM posts GROUP BY author_id HAVING COUNT(*) > 5`

- [ ] **Subqueries** - Nested SELECT statements
  - IN subqueries: `SELECT * FROM users WHERE id IN (SELECT author_id FROM posts)`
  - Scalar subqueries: `SELECT (SELECT COUNT(*) FROM posts) as post_count`
  - Correlated subqueries for complex filtering

- [ ] **Indexes** - B-tree indexes for performance
  - Single-column indexes: `CREATE INDEX idx_email ON users(email)`
  - Composite indexes: `CREATE INDEX idx_name_age ON users(name, age)`
  - Unique indexes (beyond unique constraints)
  - Dramatic performance improvement for large datasets

### Constraints & Validation
- [ ] **CHECK Constraints** - Column-level validation rules
  - Example: `age INTEGER CHECK(age >= 0 AND age <= 120)`
  - Example: `email TEXT CHECK(email LIKE '%@%')`
  - Enforce business rules at database level

- [ ] **Composite Primary Keys** - Multi-column PKs
  - Example: `PRIMARY KEY (user_id, project_id)` for junction tables
  - Critical for many-to-many relationships

- [ ] **Composite Foreign Keys** - Multi-column FK relationships
  - Example: `FOREIGN KEY (dept_id, location_id) REFERENCES departments(id, location)`

- [ ] **Deferred Constraints** - Check constraints at transaction end
  - Allows temporary constraint violations within transactions
  - Critical for circular dependencies

### Transaction Management
- [ ] **Transactions** - BEGIN/COMMIT/ROLLBACK
  - Atomic multi-statement operations
  - Currently WAL exists but no explicit transaction control
  - Example:
    ```python
    with transaction:
        session.execute("INSERT INTO accounts ...")
        session.execute("UPDATE balance ...")
        # Both succeed or both rollback
    ```

- [ ] **Savepoints** - Nested transaction rollback points
  - `SAVE POINT sp1; ... ROLLBACK TO sp1;`
  - Partial rollback within larger transaction

- [ ] **Isolation Levels** - READ COMMITTED, SERIALIZABLE, etc.
  - Control concurrent access behavior

### Schema Evolution
- [ ] **ALTER TABLE** - Modify existing table structure
  - ADD COLUMN: `ALTER TABLE users ADD COLUMN phone TEXT`
  - DROP COLUMN: `ALTER TABLE users DROP COLUMN deprecated_field`
  - RENAME COLUMN: `ALTER TABLE users RENAME COLUMN name TO full_name`
  - RENAME TABLE: `ALTER TABLE old_name RENAME TO new_name`

- [ ] **DROP COLUMN** - Remove specific columns
  - Currently can only drop entire tables
  - Must handle FK dependencies

## 🎯 Medium Priority - Advanced Features

### Query Operators
- [ ] **IN / NOT IN** - Set membership tests
  - Example: `SELECT * FROM users WHERE id IN (1, 2, 3)`
  - Example: `SELECT * FROM users WHERE id NOT IN (SELECT blocked_id FROM blocks)`

- [ ] **BETWEEN** - Range queries
  - Example: `SELECT * FROM products WHERE price BETWEEN 10 AND 100`

- [ ] **EXISTS / NOT EXISTS** - Existence checks
  - Example: `SELECT * FROM users WHERE EXISTS (SELECT 1 FROM posts WHERE author_id = users.id)`

- [x] **IS NULL / IS NOT NULL** - Explicit NULL checks
  - Currently only supports `== None` in Python
  - Need SQL-standard NULL handling

- [ ] **CASE Expressions** - Conditional logic
  - Example:
    ```sql
    SELECT name,
           CASE
               WHEN age < 18 THEN 'minor'
               WHEN age < 65 THEN 'adult'
               ELSE 'senior'
           END as age_group
    FROM users
    ```

- [ ] **UNION / INTERSECT / EXCEPT** - Set operations
  - Combine results from multiple queries
  - Example: `(SELECT id FROM users) UNION (SELECT id FROM admins)`

### Functions & Expressions
- [ ] **String Functions**
  - UPPER(), LOWER(), TRIM(), LTRIM(), RTRIM()
  - SUBSTRING(), LENGTH(), CONCAT()
  - REPLACE(), INSTR(), SUBSTR()

- [ ] **Math Functions**
  - ROUND(), CEIL(), FLOOR(), ABS()
  - SQRT(), POWER(), MOD()
  - RANDOM(), MIN(), MAX()

- [ ] **Date/Time Functions**
  - NOW(), CURRENT_DATE, CURRENT_TIME, CURRENT_TIMESTAMP
  - DATE_ADD(), DATE_SUB(), DATEDIFF()
  - YEAR(), MONTH(), DAY(), HOUR(), MINUTE(), SECOND()
  - STRFTIME() for custom formatting

- [ ] **NULL Handling Functions**
  - COALESCE() - Return first non-NULL value
  - NULLIF() - Return NULL if values equal
  - IFNULL() / NVL() - NULL replacement

- [ ] **Type Conversion Functions**
  - CAST() - Explicit type conversion
  - Example: `CAST(age AS TEXT)`, `CAST('123' AS INTEGER)`

### Advanced Query Features
- [ ] **Window Functions** - Analytics without grouping
  - ROW_NUMBER(), RANK(), DENSE_RANK()
  - PARTITION BY for grouped window operations
  - LEAD(), LAG() for row comparisons
  - Example: `SELECT name, salary, RANK() OVER (ORDER BY salary DESC) FROM employees`

- [ ] **Common Table Expressions (CTEs)** - WITH clauses
  - Recursive CTEs for tree traversal
  - Example:
    ```sql
    WITH RECURSIVE tree AS (
        SELECT id, name, parent_id FROM categories WHERE parent_id IS NULL
        UNION ALL
        SELECT c.id, c.name, c.parent_id FROM categories c JOIN tree t ON c.parent_id = t.id
    )
    SELECT * FROM tree
    ```

- [ ] **RETURNING Clause** - Return affected rows
  - Example: `INSERT INTO users (name) VALUES ('Bear') RETURNING id`
  - Useful for getting auto-generated values

### Database Objects
- [ ] **Views** - Virtual tables based on queries
  - Example: `CREATE VIEW active_users AS SELECT * FROM users WHERE status = 'active'`
  - Updatable vs read-only views

- [ ] **Triggers** - Automatic actions on events
  - BEFORE/AFTER INSERT/UPDATE/DELETE
  - Example: Auto-update `updated_at` timestamp
  - Audit logging triggers

- [ ] **Sequences** - Independent auto-increment generators
  - Not tied to specific table
  - Example: `CREATE SEQUENCE order_numbers START 1000`

- [ ] **Computed/Generated Columns** - Derived values
  - VIRTUAL: Computed on read
  - STORED: Computed on write and stored
  - Example: `full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name)`

## 💡 Nice to Have - Polish & Optimization

### Performance & Optimization
- [ ] **EXPLAIN / ANALYZE** - Query plan inspection
  - Show how queries are executed
  - Identify performance bottlenecks
  - Example: `EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = 'bear@example.com'`

- [ ] **Partial Indexes** - Indexes with WHERE clauses
  - Example: `CREATE INDEX idx_active_users ON users(email) WHERE status = 'active'`
  - Smaller, faster indexes for specific use cases

- [ ] **Covering Indexes** - Include non-indexed columns
  - Avoid table lookups for included columns
  - Example: `CREATE INDEX idx_user_lookup ON users(id) INCLUDE (name, email)`

- [ ] **Query Optimizer** - Cost-based query planning
  - Statistics gathering on tables
  - Choose optimal execution plans
  - Currently executes queries naively

- [ ] **VACUUM / OPTIMIZE** - Database cleanup
  - Reclaim space from deleted records
  - Rebuild indexes
  - Update statistics

### Data Types & Storage
- [ ] **BLOB Support** - Binary large objects
  - Store images, files, binary data
  - Already have MessagePack format, extend to BLOBs

- [ ] **JSON Data Type** - Native JSON column support
  - JSON operators: `->`, `->>`
  - JSON functions: `json_extract()`, `json_array()`, `json_object()`
  - Example: `SELECT metadata->>'city' FROM users`

- [ ] **Array Data Type** - Native array support
  - Example: `tags TEXT[]`
  - Array operators and functions

- [ ] **ENUM Type** - Enumerated types
  - Validated set of allowed values
  - Example: `status ENUM('pending', 'active', 'archived')`

- [ ] **UUID Type** - Native UUID support
  - Auto-generation: `id UUID DEFAULT gen_random_uuid()`

### Advanced Features
- [ ] **Full-Text Search (FTS)** - Text search capabilities
  - Create FTS indexes: `CREATE VIRTUAL TABLE docs_fts USING fts5(content)`
  - Match queries: `SELECT * FROM docs_fts WHERE docs_fts MATCH 'bear shelf'`
  - Ranking and snippets

- [ ] **Regular Expression Support** - REGEXP operator
  - Example: `SELECT * FROM users WHERE email REGEXP '^[a-z]+@[a-z]+\.com$'`

- [ ] **User-Defined Functions** - Custom SQL functions
  - Register Python functions callable from SQL
  - Example: `CREATE FUNCTION slugify(text) RETURNS text AS ...`

- [ ] **Stored Procedures** - Reusable SQL procedures
  - Example: `CREATE PROCEDURE update_user_stats() AS ...`

- [ ] **Collations** - Custom sort orders
  - Case-insensitive sorting
  - Locale-specific sorting
  - Example: `CREATE INDEX idx_name ON users(name COLLATE NOCASE)`

### Multi-Database & Schema Features
- [ ] **Multiple Databases** - Multiple DBs per engine
  - Example: `SELECT * FROM db1.users JOIN db2.orders ON ...`

- [ ] **Schemas / Namespaces** - Organize tables
  - Example: `CREATE SCHEMA analytics; CREATE TABLE analytics.reports (...)`

- [ ] **Cross-Database Queries** - Join across databases
  - Attach multiple databases
  - Query across attached DBs

### Concurrency & Reliability
- [ ] **Concurrent Access Control** - Multi-user locking
  - Row-level locking
  - Table-level locking
  - Optimistic concurrency control

- [ ] **Advisory Locks** - Application-level coordination
  - Example: `SELECT pg_advisory_lock(12345)`

- [ ] **Prepared Statements** - Parameterized query optimization
  - Parse once, execute many times
  - Better performance for repeated queries

- [ ] **Connection Pooling** - Reuse database connections
  - Reduce connection overhead
  - Handle concurrent requests efficiently

### Developer Experience
- [ ] **Better Error Messages** - More helpful diagnostics
  - Show query context where error occurred
  - Suggest fixes for common mistakes
  - Already pretty good, but can improve

- [ ] **Query Logging** - Log all executed queries
  - Debug mode with query timing
  - Slow query log

- [x] **Schema Introspection** - Inspect database metadata
  - List tables, columns, constraints
  - Get table DDL
  - Already partially supported, formalize it

- [ ] **Backup / Restore** - Built-in backup tools
  - `bear-shelf backup db.jsonl > backup.jsonl`
  - Point-in-time recovery

- [ ] **Import / Export** - Data migration tools
  - CSV import/export
  - SQL dump generation
  - Migration from SQLite/PostgreSQL/MySQL

## 🔬 Research & Exploration

### Experimental Features
- [ ] **Replication** - Master/replica setups
  - Streaming replication
  - Logical replication
  - Read replicas for scaling

- [ ] **Sharding** - Horizontal partitioning
  - Distribute data across multiple files
  - Partition by range, hash, or list

- [ ] **Time-Series Optimizations** - Specialized for time-series data
  - Efficient timestamp indexing
  - Automatic data retention policies
  - Downsampling and aggregation

- [ ] **Graph Query Support** - Recursive relationships
  - Shortest path queries
  - Graph traversal operations
  - Integration with graph algorithms

- [ ] **Vector Search** - Embeddings and similarity search
  - Store vector embeddings
  - Cosine similarity, L2 distance
  - Approximate nearest neighbor (ANN) search

- [ ] **Encryption at Rest** - Encrypted storage formats
  - Transparent encryption/decryption
  - Key management integration

## 📊 Priority Matrix

### Must Have (Next 6 Months)
1. JOIN operations (critical for real-world usage)
2. Aggregate functions (COUNT, SUM, AVG, MIN, MAX)
3. GROUP BY / HAVING
4. Indexes (B-tree, basic performance)
5. CHECK constraints
6. Transactions (BEGIN/COMMIT/ROLLBACK)

### Should Have (6-12 Months)
7. ALTER TABLE (add/drop columns)
8. Subqueries (IN, scalar, correlated)
9. Window functions (analytics)
10. CTEs (WITH clauses)
11. Views
12. Composite primary/foreign keys

### Nice to Have (12+ Months)
13. Full-text search
14. JSON data type
15. Triggers
16. User-defined functions
17. Query optimizer
18. Replication

## 🎯 Quick Wins

These are relatively easy to implement and provide immediate value:

1. **IN / NOT IN operators** - Simple set membership, high value
2. **BETWEEN operator** - Syntactic sugar for range queries
3. **IS NULL / IS NOT NULL** - Explicit NULL checks
4. **String functions (UPPER, LOWER, TRIM)** - Common operations
5. **Math functions (ROUND, ABS)** - Basic math support
6. **COALESCE() function** - NULL handling
7. **RETURNING clause** - Very useful for INSERTs
8. **Better LIKE patterns** - Case-insensitive ILIKE

## 💭 Design Questions

Before implementing, need to decide:

1. **Index Storage**: How to persist indexes across sessions?
   - Separate index files?
   - Embedded in main data file?
   - Rebuild on load (acceptable for small datasets)?

2. **Transaction Model**: How to handle multi-statement transactions?
   - Extend WAL to support rollback?
   - In-memory transaction buffer?
   - Copy-on-write for rollback?

3. **JOIN Implementation**: Hash join vs nested loop?
   - Hash join for large datasets
   - Nested loop for small datasets with indexes
   - Need query optimizer to choose

4. **Storage Format Impact**: Do new features work across all formats?
   - Some formats (TOML, XML) have limitations
   - May need to restrict features by format
   - Or normalize to internal representation

5. **Backward Compatibility**: How to version schema?
   - Schema version in metadata
   - Auto-migration on load?
   - Breaking changes policy?

## 🚀 Current Status

### ✅ Already Implemented (You're doing great!)
- Basic CRUD (INSERT, SELECT, UPDATE, DELETE)
- Foreign keys with full referential integrity (CASCADE, SET NULL, RESTRICT, NO ACTION)
- ON DELETE and ON UPDATE actions
- String and integer primary keys
- DISTINCT, LIMIT, OFFSET, ORDER BY
- WHERE clauses with comparisons (=, <, >, <=, >=, !=)
- LIKE operator (pattern matching)
- Multiple storage formats (JSON, JSONL, XML, YAML, TOML, MessagePack)
- Write-ahead logging (WAL)
- Unique constraints
- Nullable/non-nullable columns
- Default values and default factories
- Autoincrement
- Self-referential foreign keys (tree structures)
- SQLAlchemy dialect integration
- Type safety with Pydantic
- Comprehensive test suite (400+ tests)
- Excellent documentation

---

**Note**: This is an aspirational list. Bear Shelf is already incredibly useful for its target use case (lightweight, multi-format storage with SQL interface). Not every feature needs to be implemented - prioritize based on actual user needs and use cases!

**Philosophy**: Stay true to Bear Shelf's core value proposition: simplicity, multiple storage formats, and ease of use. Don't just copy SQLite - be better at what makes Bear Shelf unique! 🐻📚
