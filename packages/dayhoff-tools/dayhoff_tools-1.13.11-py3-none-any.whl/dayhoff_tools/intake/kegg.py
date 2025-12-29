import sqlite3
from typing import List

import pandas as pd


def get_ko2gene_df(db: str, ko: str | list[str] | None = None) -> pd.DataFrame:
    """Specialized function that extracts KO-to-gene mappings from a SQLite database,
    and returns them as a dataframe.

    Args:
        db: Path to an SQLite database file that contains a table called `gene_to_ko`.
        ko: KO or list of KOs to query. If None, all KOs will be queried.


    Returns:
        pd.DataFrame: KO to gene mappings.
    """
    if type(ko) == str:
        ko = [ko]

    conn = sqlite3.connect(db)

    if ko is not None:
        query = (
            f"SELECT gene,ko FROM gene_to_ko WHERE ko IN ({','.join('?' * len(ko))})"
        )
        result_df = pd.read_sql_query(
            query, conn, params=ko  # type:ignore
        )
    else:
        query = f"SELECT gene,ko FROM gene_to_ko"
        result_df = pd.read_sql_query(query, conn)

    conn.close()

    return result_df
