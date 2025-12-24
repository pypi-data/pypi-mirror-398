from ..base.operators import BaseOperators


class SQLServerOperators(BaseOperators):
    """
    SQL Server-specific operator mappings.
    """

    @classmethod
    def get_operators(cls):
        """Returns SQL Server-specific operator mappings."""
        return OPERATORS

    @classmethod
    def supports_case_insensitive_like(cls):
        """SQL Server LIKE case sensitivity depends on collation."""
        return False  # Depends on database collation

    @classmethod
    def supports_regex(cls):
        """SQL Server doesn't have built-in regex operators (until recent versions)."""
        return False

    @classmethod
    def get_regex_operators(cls):
        """Returns SQL Server regex operators (none in older versions)."""
        return {}


OPERATORS = {
    "<>": "<>",
    "!=": "<>",
    "!><": "NOT BETWEEN",
    ">!<": "NOT BETWEEN",
    "><": "BETWEEN",
    "%%": "LIKE",  # SQL Server doesn't have ILIKE
    "!%%": "NOT LIKE",
    "==": "=",
    "<=": "<=",
    ">=": ">=",
    "<": "<",
    ">": ">",
    "%": "LIKE",
    "!%": "NOT LIKE",
    "=": "=",
    "!": "<>",
}
