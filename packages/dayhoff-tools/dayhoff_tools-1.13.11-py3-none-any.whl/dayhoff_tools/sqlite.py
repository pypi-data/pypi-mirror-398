import os
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Literal, Optional, Tuple, Union

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from tqdm import tqdm
from typing_extensions import Literal


def sql_query(db_file: str, query: str, params: tuple[Any, ...] = ()) -> list[Any]:
    """Perform a SQL query on the specified SQLite file.

    Args:
        db_file (str): Path to the SQLite file.
        query (str): SQL query to perform.
        params (tuple[Any, ...], optional): Query parameters. Defaults to ().

    Returns:
        list[Any]: Results of the query.

    Raises:
        sqlite3.DatabaseError: If the query fails.
    """
    with sqlite3.connect(db_file) as conn:
        try:
            return conn.execute(query, params).fetchall()
        except sqlite3.Error as e:
            raise sqlite3.DatabaseError(f"Query: {query}\n failed with error:\n {e}")


def sql_check_columns(
    db_file: str,
    table_name: str,
    columns: str | Iterable[str] | None = None,
) -> list[str]:
    """Check that the table and columns exist in the specified SQLite file.
    Returns a list of verified columns.

    Args:
        db_file (str): Path to the SQLite file.
        table_name (str): Name of the table in the database that contains the data.
        columns (str | list[str] | tuple[str, ...] | None, optional): Names of the
            columns in the database that will be returned as features. If None then
            all columns will be returned.

    Returns:
        list[str]: List of verified columns.

    Raises:
        sqlite3.DatabaseError: If the table, or columns do not exist.
    """
    tables = [
        table[0]
        for table in sql_query(
            db_file, "SELECT name FROM sqlite_master WHERE type='table'"
        )
    ]
    if table_name not in tables:
        raise sqlite3.DatabaseError(f"Table {table_name} does not exist.")

    existing_columns = [
        row[1] for row in sql_query(db_file, f"PRAGMA table_info({table_name})")
    ]
    if columns is not None:
        columns = [columns] if isinstance(columns, str) else list(columns)
        missing_columns = set(columns) - set(existing_columns)
        if missing_columns:
            raise sqlite3.DatabaseError(
                "One or more specified columns does not exist.\n"
                + f"Missing columns: {missing_columns}\n"
                + f"Existing columns: {existing_columns}"
            )
        return columns
    else:
        return existing_columns


def sql_check_index(db_file: str, table_name: str, column_name: str) -> bool:
    """Verify that an index exists for the given column in the specified table."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    query = f"PRAGMA index_list('{table_name}')"
    cursor.execute(query)
    indexes = cursor.fetchall()

    # Collect all indexed columns from the retrieved indexes
    indexed_columns = []
    for index in indexes:
        index_name = index[1]  # Adjust according to the structure returned
        index_info_query = f"PRAGMA index_info('{index_name}')"
        cursor.execute(index_info_query)
        columns = cursor.fetchall()
        indexed_columns.extend(col[2] for col in columns if col[2] == column_name)

    conn.close()
    if column_name not in indexed_columns:
        raise Exception(
            f"Column '{column_name}' is not indexed in table '{table_name}'."
        )

    return True


def sql_check_primary_key(db_file: str, table_name: str, expected_primary_key: str):
    """Check that the expected primary key is set for the specified table."""
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = cursor.fetchall()
        # Look for the primary key in the results
        for col in columns:
            if col[1] == expected_primary_key and col[5] == 1:  # Check the pk flag
                return True
        return False


def write_to_sqlite(
    input_data: Union[str, pd.DataFrame],
    sql_filepath: str,
    table_name: str,
    columns: list[Tuple[str, Any]],
    primary_key: str,
    indexes: list[Tuple[str, str]],
    if_table_exists: Literal["fail", "replace", "append"] = "append",
    delete_file_if_exists: bool = True,
    chunksize: int = 1000,
) -> None:
    """
    Write data from a TSV file or DataFrame to a SQLite database file in a memory-efficient way.

    Args:
        input_data (Union[str, pd.DataFrame]): The input data, either a file path of the TSV file or a DataFrame.
        sql_filepath (str): The file path of the SQLite database file.
        table_name (str): The name of the table to be created in the database.
        columns (list[Tuple[str, Any]]): A list of tuples representing the column names and their data types.
            Each tuple should be in the format (column_name, data_type), where the data_type is an sqlite data type.
            Example: [("id", "INTEGER"), ("name", "TEXT"), ("age", "INTEGER")]
        primary_key (str): The name of the column to be used as the primary key.
        indexes (list[Tuple[str, str]]): A list of tuples representing the indexes to be created.
            Each tuple should be in the format (index_name, column_name).
            Example: [("idx_name", "name"), ("idx_age", "age")]
        if_table_exists (Literal['fail', 'replace', 'append']): What to do if the table exists already.
        delete_file_if_exists (bool): Whether to delete the database file itself, if it exists.
        chunksize (int): Number of lines to read from the TSV file at a time if input_data is a TSV file.

    Examples:
        columns = [
            ("pr_id", "INTEGER"),
            ("reaction_id", "TEXT"),
            ("protein_id", "TEXT"),
            ("db_source", "TEXT"),
        ]
        primary_key = "pr_id"
        indexes = [
            ("idx_on_protein_id", "protein_id"),
            ("idx_on_reaction_id", "reaction_id"),
        ]
        write_to_sqlite(
            input_data="path/to/data.tsv",
            sql_filepath="path/to/database.db",
            table_name="protein_to_reaction",
            columns=columns,
            primary_key=primary_key,
            indexes=indexes,
            if_table_exists="append",
            delete_file_if_exists=True,
            chunksize=1000
        )

        # or

        df = pd.DataFrame([...])
        write_to_sqlite(
            input_data=df,
            sql_filepath="path/to/database.db",
            table_name="protein_to_reaction",
            columns=columns,
            primary_key=primary_key,
            indexes=indexes,
            if_table_exists="append",
            delete_file_if_exists=True,
        )
    """

    # Optionally delete the database file itself
    if delete_file_if_exists and os.path.exists(sql_filepath):
        os.remove(sql_filepath)

    with sqlite3.connect(sql_filepath) as conn:
        cursor = conn.cursor()

        # Determine action if table exists
        if if_table_exists == "replace":
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        elif if_table_exists == "append":
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,),
            )
            if cursor.fetchone() is None:
                if_table_exists = "replace"
        else:  # if_table_exists == 'fail'
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table_name,),
            )
            if cursor.fetchone():
                raise ValueError(f"Table {table_name} already exists.")

        # Create table if 'replace' or not exists
        if if_table_exists == "replace":
            col_defs = [f"{name} {dtype}" for name, dtype in columns]
            col_defs.append(f"PRIMARY KEY ({primary_key})")
            cursor.execute(f"CREATE TABLE {table_name} ({', '.join(col_defs)})")

        # Convert columns to list of column names
        column_names = [col[0] for col in columns]
        placeholders = ", ".join("?" * len(column_names))

        if isinstance(input_data, str):
            # Read TSV file in chunks and insert into the table
            for chunk in pd.read_csv(
                input_data, sep="\t", usecols=column_names, chunksize=chunksize
            ):
                data = chunk.values.tolist()
                cursor.executemany(
                    f"INSERT INTO {table_name} VALUES ({placeholders})", data
                )
        elif isinstance(input_data, pd.DataFrame):
            # Insert DataFrame data into the table
            data = input_data[column_names].values.tolist()
            cursor.executemany(
                f"INSERT INTO {table_name} VALUES ({placeholders})", data
            )
        else:
            raise ValueError(
                "input_data must be either a file path to a TSV file or a DataFrame."
            )

        # Create indexes if specified
        for index_name, column_name in indexes:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})"
            )

        conn.commit()


def inspect_sqlite_db(db_path: str) -> None:
    """
    Inspect the contents of a SQLite database file.

    This function connects to the specified SQLite database, retrieves information
    about its tables, columns, and sample data, and prints this information to
    the console.

    Args:
        db_path (str): The file path to the SQLite database.

    Returns:
        None

    Raises:
        sqlite3.Error: If there's an error connecting to or querying the database.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            print("Columns:", ", ".join(columns))

            # Get sample data (first 5 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()

            print("\nSample data:")
            for row in rows:
                print(row)

        conn.close()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")


def read_sql_table_to_df(
    db_path: str, table_name: Optional[str] = None, chunksize: int = 10000
) -> pd.DataFrame:
    """
    Read an SQL table into a pandas DataFrame with a progress bar.

    This function connects to a SQLite database using the provided file path,
    reads the specified table (or the only table if not specified) in chunks,
    and displays a progress bar during the reading process.

    Args:
        db_path (str): The file path to the SQLite database.
        table_name (Optional[str], optional): The name of the table to read from the database.
                                              If None, assumes there's only one table. Defaults to None.
        chunksize (int, optional): The number of rows to read per chunk. Defaults to 10000.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the data from the SQL table.

    Raises:
        ValueError: If the table_name is not provided and there are multiple tables,
                    or if the specified table doesn't exist.
        SQLAlchemyError: If there's an issue connecting to the database or reading the table.
    """

    engine_url = f"sqlite:///{db_path}"
    engine = create_engine(engine_url)

    # Get all table names
    with engine.connect() as connection:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

    # Handle table selection
    if table_name is None:
        if len(table_names) == 1:
            table_name = table_names[0]
        elif len(table_names) == 0:
            raise ValueError("No tables found in the database.")
        else:
            raise ValueError(
                f"Multiple tables found. Please specify a table_name. Options are: {', '.join(table_names)}"
            )
    elif table_name not in table_names:
        raise ValueError(f"Table '{table_name}' not found in the database.")

    # Get the number of rows in the table
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        row_count = result.scalar()

    # Create a tqdm progress bar
    pbar = tqdm(total=row_count, desc=f"Reading {table_name}", unit="rows")

    # Read the SQL table in chunks with progress updates
    chunks = []
    for chunk in pd.read_sql(
        f"SELECT * FROM {table_name}", engine, chunksize=chunksize
    ):
        chunks.append(chunk)
        pbar.update(len(chunk))

    # Close the progress bar
    pbar.close()

    # Combine all chunks into a single DataFrame
    df = pd.concat(chunks, ignore_index=True)

    return df


def _create_optimized_db(dst_path: Path) -> None:
    """Helper function to create an optimized database."""
    if dst_path.exists():
        dst_path.unlink()

    with sqlite3.connect(str(dst_path)) as conn:
        # Use default page size but optimize other settings
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute(
            "PRAGMA synchronous=FULL"
        )  # Start with FULL for safety during creation
        conn.commit()


def _verify_destination(dst_path: Path) -> None:
    """Helper function to verify destination path is writable."""
    # Convert to absolute path for consistent handling
    dst_path = dst_path.absolute()

    # Check if path is under root and we don't have root access
    if str(dst_path).startswith("/") and not os.access("/", os.W_OK):
        if any(not os.access(p, os.W_OK) for p in dst_path.parents):
            raise OSError(f"No write permission for path: {dst_path}")

    try:
        # Check if parent directory exists
        if not dst_path.parent.exists():
            try:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise OSError(
                    f"Cannot create parent directory: {dst_path.parent}"
                ) from e

        # Check if parent directory is writable
        if not os.access(str(dst_path.parent), os.W_OK):
            raise OSError(
                f"No write permission for parent directory: {dst_path.parent}"
            )

        # If file exists, check if it's writable
        if dst_path.exists():
            if not os.access(str(dst_path), os.W_OK):
                raise OSError(f"No write permission for destination: {dst_path}")
        else:
            # Try to create and write to the file
            try:
                dst_path.touch()
                dst_path.unlink()  # Clean up the test file
            except (OSError, PermissionError) as e:
                raise OSError(f"Cannot write to destination path: {dst_path}") from e

    except Exception as e:
        # Ensure we always raise OSError
        if not isinstance(e, OSError):
            raise OSError(f"Cannot create or write to destination: {dst_path}") from e
        raise


def optimize_protein_db(src_path: Union[str, Path], dst_path: Union[str, Path]):
    """
    Optimize SQLite database containing protein sequences.
    """
    src_path, dst_path = Path(src_path), Path(dst_path)

    # Check source file exists
    if not src_path.exists():
        raise FileNotFoundError(f"Source database not found: {src_path}")

    # Verify destination is writable
    _verify_destination(dst_path)

    # Create optimized database
    _create_optimized_db(dst_path)

    # Copy data from source to destination
    with sqlite3.connect(str(dst_path)) as dst_conn:
        with sqlite3.connect(src_path) as src_conn:
            src_conn.backup(dst_conn)

        # Apply conservative optimizations
        dst_conn.execute("PRAGMA journal_mode=WAL")
        dst_conn.execute("PRAGMA synchronous=FULL")  # Keep FULL for protein data
        dst_conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache
        dst_conn.execute("PRAGMA temp_store=FILE")
        dst_conn.commit()


def optimize_reaction_db(src_path: Union[str, Path], dst_path: Union[str, Path]):
    """
    Optimize SQLite database containing reaction data.
    """
    src_path, dst_path = Path(src_path), Path(dst_path)

    # Check source file exists
    if not src_path.exists():
        raise FileNotFoundError(f"Source database not found: {src_path}")

    # Verify destination is writable
    _verify_destination(dst_path)

    # Create optimized database
    _create_optimized_db(dst_path)

    # Copy data from source to destination
    with sqlite3.connect(str(dst_path)) as dst_conn:
        with sqlite3.connect(src_path) as src_conn:
            src_conn.backup(dst_conn)

        # Apply conservative optimizations
        dst_conn.execute("PRAGMA journal_mode=WAL")
        dst_conn.execute("PRAGMA synchronous=FULL")  # Keep FULL for safety
        dst_conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache
        dst_conn.execute("PRAGMA temp_store=FILE")  # Use FILE instead of MEMORY
        dst_conn.commit()


def optimize_pairs_db(src_path: Union[str, Path], dst_path: Union[str, Path]):
    """
    Optimize SQLite database containing protein-reaction pairs.
    """
    src_path, dst_path = Path(src_path), Path(dst_path)

    # Check source file exists
    if not src_path.exists():
        raise FileNotFoundError(f"Source database not found: {src_path}")

    # Verify destination is writable
    _verify_destination(dst_path)

    # Create optimized database
    _create_optimized_db(dst_path)

    # Copy data from source to destination
    with sqlite3.connect(str(dst_path)) as dst_conn:
        with sqlite3.connect(src_path) as src_conn:
            src_conn.backup(dst_conn)

        # Apply conservative optimizations
        dst_conn.execute("PRAGMA journal_mode=WAL")
        dst_conn.execute("PRAGMA synchronous=FULL")  # Keep FULL for safety
        dst_conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache
        dst_conn.execute("PRAGMA temp_store=FILE")  # Use FILE instead of MEMORY
        dst_conn.execute("PRAGMA mmap_size=30000000000")  # 30GB memory mapping
        dst_conn.commit()
