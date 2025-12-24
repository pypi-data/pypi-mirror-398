from ..base.operators import BaseOperators


class SQLiteOperators(BaseOperators):
    """
    SQLite-specific operator mappings.
    """

    @classmethod
    def get_operators(cls):
        """Returns SQLite-specific operator mappings."""
        return OPERATORS

    @classmethod
    def supports_case_insensitive_like(cls):
        """SQLite LIKE is case-insensitive by default."""
        return True  # Sort of - depends on the text encoding

    @classmethod
    def supports_regex(cls):
        """SQLite supports REGEXP if the REGEXP function is defined."""
        return True  # But requires the REGEXP function to be defined

    @classmethod
    def get_regex_operators(cls):
        """Returns SQLite regex operators."""
        return {
            "REGEXP": "REGEXP",
            "GLOB": "GLOB",
        }


OPERATORS = {
    "<>": "<>",
    "!=": "<>",
    "!><": "NOT BETWEEN",
    ">!<": "NOT BETWEEN", 
    "><": "BETWEEN",
    "%%": "LIKE",  # SQLite LIKE is case-insensitive by default
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
    "GLOB": "GLOB",
}
