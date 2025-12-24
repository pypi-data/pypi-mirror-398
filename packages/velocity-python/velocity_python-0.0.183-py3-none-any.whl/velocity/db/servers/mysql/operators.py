from ..base.operators import BaseOperators


class MySQLOperators(BaseOperators):
    """
    MySQL-specific operator mappings.
    """

    @classmethod
    def get_operators(cls):
        """Returns MySQL-specific operator mappings."""
        return OPERATORS

    @classmethod
    def supports_case_insensitive_like(cls):
        """MySQL LIKE is case-insensitive by default on case-insensitive collations."""
        return False  # Depends on collation, but generally need to use LOWER()

    @classmethod
    def supports_regex(cls):
        """MySQL supports REGEXP/RLIKE operators."""
        return True

    @classmethod
    def get_regex_operators(cls):
        """Returns MySQL regex operators."""
        return {
            "REGEXP": "REGEXP",
            "RLIKE": "RLIKE",
            "NOT REGEXP": "NOT REGEXP",
        }


OPERATORS = {
    "<>": "<>",
    "!=": "<>",
    "!><": "NOT BETWEEN",
    ">!<": "NOT BETWEEN",
    "><": "BETWEEN",
    "%%": "LIKE",  # MySQL doesn't have ILIKE, use LIKE with LOWER()
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
    "REGEXP": "REGEXP",
    "!REGEXP": "NOT REGEXP",
    "RLIKE": "RLIKE",
}
