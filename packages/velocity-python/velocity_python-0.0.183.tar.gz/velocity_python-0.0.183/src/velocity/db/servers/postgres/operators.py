from ..base.operators import BaseOperators


class PostgreSQLOperators(BaseOperators):
    """
    PostgreSQL-specific operator mappings.
    """

    @classmethod
    def get_operators(cls):
        """Returns PostgreSQL-specific operator mappings."""
        return OPERATORS

    @classmethod
    def supports_case_insensitive_like(cls):
        """PostgreSQL supports ILIKE for case-insensitive matching."""
        return True

    @classmethod
    def supports_regex(cls):
        """PostgreSQL supports regex operators."""
        return True

    @classmethod
    def get_regex_operators(cls):
        """Returns PostgreSQL regex operators."""
        return {
            "~": "~",
            "!~": "!~",
            "~*": "~*",
            "!~*": "!~*",
        }


OPERATORS = {
    "<>": "<>",
    "!=": "<>",
    "!><": "NOT BETWEEN",
    ">!<": "NOT BETWEEN",
    "><": "BETWEEN",
    "%%": "ILIKE",
    "!%%": "NOT ILIKE",
    "==": "=",
    "<=": "<=",
    ">=": ">=",
    "<": "<",
    ">": ">",
    "!~*": "!~*",
    "~*": "~*",
    "!~": "!~",
    "%": "LIKE",
    "!%": "NOT LIKE",
    "~": "~",
    "=": "=",
    "!": "<>",
    "#": "ILIKE",
}
