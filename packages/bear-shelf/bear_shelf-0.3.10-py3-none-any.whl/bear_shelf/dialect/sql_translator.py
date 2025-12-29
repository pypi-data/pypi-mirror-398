"""Translate SQLAlchemy expressions to bear-dereth QueryMapping queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from sqlalchemy import and_, not_, or_
    from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, ColumnElement, UnaryExpression
    from sqlalchemy.sql.operators import is_, is_not

    from bear_shelf.dialect.helpers._translate import translate_op
    from funcy_bear.query import QueryInstance, QueryMapping
else:
    QueryMapping, QueryInstance = lazy("funcy_bear.query", "QueryMapping", "QueryInstance")
    is_, is_not = lazy("sqlalchemy.sql.operators", "is_", "is_not")
    and_, not_, or_ = lazy("sqlalchemy", "and_", "not_", "or_")
    translate_op = lazy("bear_shelf.dialect.helpers._translate", "translate_op")


def translate_where_clause(
    where_clause: ColumnElement | None,
    parameters: dict[str, Any] | None = None,
) -> QueryInstance | None:
    """Translate SQLAlchemy WHERE clause to QueryMapping query.

    Args:
        where_clause: SQLAlchemy WHERE clause expression
        parameters: Dictionary of bind parameter values

    Returns:
        QueryMapping query instance or None if no WHERE clause
    """
    if where_clause is None:
        return None
    return _translate_expression(where_clause, parameters)


def _translate_expression(
    expr: ColumnElement,
    parameters: dict[str, Any] | None = None,
) -> QueryInstance:
    """Recursively translate a SQLAlchemy expression to QueryMapping.

    Args:
        expr: SQLAlchemy expression to translate
        parameters: Dictionary of bind parameter values

    Returns:
        QueryMapping query instance
    """
    from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, UnaryExpression  # noqa: PLC0415

    if isinstance(expr, BinaryExpression):  # Handle binary expressions (column op value)
        return _translate_binary(expr, parameters)

    if isinstance(expr, BooleanClauseList):  # Handle boolean clause lists (AND, OR)
        return _translate_boolean_clause_list(expr, parameters)

    if isinstance(expr, UnaryExpression):  # Handle unary expressions (NOT)
        return _translate_unary(expr, parameters)

    raise NotImplementedError(f"Expression type {type(expr)} not supported yet")


def _translate_binary[T](
    expr: BinaryExpression,
    parameters: dict[str, Any] | None = None,
) -> QueryInstance:
    """Translate binary expression like 'column == value' to QueryMapping.

    Args:
        expr: Binary expression to translate
        parameters: Dictionary of bind parameter values

    Returns:
        QueryMapping query instance
    """
    column_name: str | None = expr.left.key
    if column_name is None:
        raise ValueError("Left side of expression must be a column with a name/key")
    value: T = extract_value(expr.right, parameters)
    query_path: Any = getattr(QueryMapping(), column_name)
    return translate_op(expr.operator, query_path, value)


def _translate_boolean_clause_list(
    expr: BooleanClauseList,
    parameters: dict[str, Any] | None = None,
) -> QueryInstance:
    """Translate boolean clause list (AND/OR) to QueryMapping.

    Args:
        expr: Boolean clause list (AND/OR expressions)
        parameters: Dictionary of bind parameter values

    Returns:
        QueryMapping query instance with combined conditions
    """
    translated: list[QueryInstance] = [_translate_expression(clause, parameters) for clause in expr.clauses]

    op_name: Any | None = getattr(expr.operator, "__name__", None)
    if op_name is None:
        op_name = str(expr.operator)
    if op_name == "and_" or expr.operator is and_:
        result: QueryInstance = translated[0]
        for query in translated[1:]:
            result = result & query
        return result
    if op_name == "or_" or expr.operator is or_:
        result: QueryInstance = translated[0]
        for query in translated[1:]:
            result = result | query
        return result
    raise NotImplementedError(f"Boolean operator {expr.operator} (name: {op_name}) not supported")


def _translate_unary(
    expr: UnaryExpression,
    parameters: dict[str, Any] | None = None,
) -> QueryInstance:
    """Translate unary expression (like NOT) to QueryMapping.

    Args:
        expr: Unary expression to translate
        parameters: Dictionary of bind parameter values

    Returns:
        QueryMapping query instance with NOT applied
    """
    if expr.operator == not_:
        inner_query: QueryInstance = _translate_expression(expr.element, parameters)
        return ~inner_query
    if expr.operator == is_:
        inner_query: QueryInstance = _translate_expression(expr.element, parameters)
        return inner_query == None  # pyright: ignore[reportReturnType] # noqa: E711
    if expr.operator == is_not:
        inner_query: QueryInstance = _translate_expression(expr.element, parameters)
        return inner_query != None  # pyright: ignore[reportReturnType] # noqa: E711
    raise NotImplementedError(f"Unary operator {expr.operator} not supported")


def extract_value(
    element: ColumnElement,
    parameters: dict[str, Any] | None = None,
) -> Any:
    """Extract the actual value from a SQLAlchemy element.

    When statement caching is enabled, bind parameters contain stale cached values.
    Runtime parameters dict contains fresh values, so prioritize it. This involves
    matching bind parameters by key, original key, or effective value.

    Args:
        element: SQLAlchemy value element (BindParameter, literal, etc.)
        parameters: Dictionary of bind parameter values to resolve bind parameters

    Returns:
        The actual Python value
    """
    from bear_shelf.dialect import protocols as pro  # noqa: PLC0415

    if element.__visit_name__ == "null":
        return None

    if parameters:
        if isinstance(element, pro.BindParameterKey) and element.key in parameters:
            return parameters[element.key]

        # SQLAlchemy anonymizes keys during compilation, so we match by value instead
        if isinstance(element, pro.BindParameterWithEffectiveValue):
            cached_value: Any = element.effective_value
            for param_value in parameters.values():
                if param_value == cached_value:
                    return param_value

        # SQLAlchemy adds numeric suffixes to prevent collisions (e.g., "name" becomes "name_1", "name_2")
        if isinstance(element, pro.BindParameterOrigKey):
            orig_key: str = element._orig_key
            for param_key in parameters:
                if param_key == orig_key or param_key.startswith(f"{orig_key}_"):
                    return parameters[param_key]

    if isinstance(element, pro.BindParameterWithEffectiveValue):
        return element.effective_value

    if isinstance(element, pro.BindParameterWithValue):
        return element.value

    return element
