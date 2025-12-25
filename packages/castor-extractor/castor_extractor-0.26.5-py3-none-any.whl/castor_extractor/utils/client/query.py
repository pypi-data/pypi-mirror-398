from dataclasses import dataclass

Params = dict[str, str]  # key: value


def values_to_params(prefix: str, values: list[str] | None) -> Params:
    """
    Convert a list of values to a dictionary.
    Each value is assigned a key based on the given prefix and its
    position in the list
    """
    if not values:
        return {}
    return {f"{prefix}_{i}": value for i, value in enumerate(values)}


@dataclass
class QueryFilter:
    """
    Represent a query filter, composed of:
    - The name of the {placeholder} that should be replaced in the query
    - The SQL expression or fragment to replace the placeholder with
    - Optional parameters used for value binding during query execution.

    Example:
    > SELECT ... FROM users WHERE {user_blocked}

    filter = QueryFilter(
        placeholder = "user_blocked",
        expression = "user_name NOT IN (user_1:, user_2:)",
        params = {"user_1:": "John", "user_2:": "Mary"}
    )
    """

    placeholder: str
    expression: str
    params: Params | None = None


class ExtractionQuery:
    """
    Contains useful context to run the query:
    - the sql statement itself
    - parameters { ... }
    - optionally, the target database (can be used to change the engine's URI)
    """

    def __init__(
        self,
        statement: str,
        params: dict,
        database: str | None = None,
    ):
        self.statement = statement
        self.params = params
        self.database = database

    def apply_filters(self, filters: list[QueryFilter]) -> None:
        """
        Apply a list of filters to this query.

        Each filter replaces a corresponding placeholder in the statement
        and updates the query's parameters with any additional filter-specific
        parameters.
        """
        placeholder_expressions = {f.placeholder: f.expression for f in filters}
        self.statement = self.statement.format(**placeholder_expressions)
        for f in filters:
            self.params.update(f.params or {})
