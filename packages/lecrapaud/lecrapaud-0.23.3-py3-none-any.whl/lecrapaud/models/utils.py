from sqlalchemy import Table, Column, BigInteger, ForeignKey

from lecrapaud.models.base import Base
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


def create_association_table(name, table1, column1, table2, column2):
    """Create an association table with the LECRAPAUD_TABLE_PREFIX.

    Args:
        name: The base name for the association table (will be prefixed)
        table1: First table name (without prefix)
        column1: First column name (will be used as f"{column1}_id")
        table2: Second table name (without prefix)
        column2: Second column name (will be used as f"{column2}_id")
    """
    return Table(
        f"{LECRAPAUD_TABLE_PREFIX}_{name}",
        Base.metadata,
        Column(
            f"{column1}_id",
            BigInteger,
            ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_{table1}.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        Column(
            f"{column2}_id",
            BigInteger,
            ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_{table2}.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
