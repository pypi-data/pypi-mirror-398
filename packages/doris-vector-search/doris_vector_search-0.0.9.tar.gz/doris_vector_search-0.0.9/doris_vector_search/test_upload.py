import io
import logging
import math
import concurrent.futures
from typing import Any, Dict, Iterable, List, Optional, Union

import pandas as pd
import pyarrow as pa
import requests
from requests.auth import HTTPBasicAuth
import mysql.connector

# All supported data types for create_table/add
Block = Union[List[dict], pd.DataFrame, pa.Table, Iterable[pa.RecordBatch]]

logger = logging.getLogger(__name__)


class AuthOptions:
    """Options for login into doris database."""

    def __init__(
        self,
        host: str = "localhost",
        query_port: int = 9030,
        http_port: int = 8030,
        user: str = "root",
        password: str = "",
    ):
        self.host = host
        self.query_port = query_port
        self.http_port = http_port
        self.user = user
        self.password = password


class LoadOptions:
    """Options for data loading."""

    def __init__(self, format: str = "arrow", batch_size: int = 10000):
        """Load options.

        Args:
            format: Format for stream loading ('csv' or 'arrow')
        """
        format = format.lower()
        if format not in ["csv", "arrow"]:
            raise ValueError(
                f"Unsupported format '{format}'. Supported formats: 'csv', 'arrow'"
            )
        self.format = format

        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.batch_size = batch_size


class TableSchema:
    """Schema information for a Doris table."""

    def __init__(
        self,
        columns: Dict[str, Dict[str, Any]],
        key_column: Optional[str] = None,
        vector_column: Optional[str] = None,
        vector_dim: int = 0,
    ):
        """Initialize TableSchema.

        Args:
            columns: Dictionary mapping column names to their schema info
            key_column: Name of the key column
            vector_column: Name of the vector column
            vector_dim: Dimension of the vector column
        """
        self.columns = columns
        self.key_column = key_column
        self.vector_column = vector_column
        self.vector_dim = vector_dim


class StreamLoadFormat:
    """Abstract base class for stream load data formats."""

    @property
    def content_type(self) -> str:
        """Return the content type for HTTP headers."""
        raise NotImplementedError

    @property
    def format_name(self) -> str:
        """Return the format name for Doris stream load."""
        raise NotImplementedError

    def serialize_data(self, data: pa.Table, schema_info: TableSchema) -> bytes:
        """Serialize Arrow Table to bytes in the specific format."""
        raise NotImplementedError

    def get_headers(self) -> Dict[str, str]:
        """Return format-specific headers for stream load."""
        raise NotImplementedError


class ArrowStreamLoadFormat(StreamLoadFormat):
    """Apache Arrow format for stream load."""

    @property
    def content_type(self) -> str:
        return "application/octet-stream"

    @property
    def format_name(self) -> str:
        return "arrow"

    def serialize_data(self, data: pa.Table, schema_info: TableSchema) -> bytes:
        """Serialize Arrow Table to Arrow bytes."""
        # Data is already an Arrow Table, serialize directly
        table = data

        # Serialize to Arrow IPC format (streaming format)
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, table.schema) as writer:
            writer.write(table)

        return sink.getvalue().to_pybytes()

    def get_headers(self) -> Dict[str, str]:
        """Return Arrow-specific headers."""
        return {
            "format": "arrow",
        }


class StreamLoadFormatFactory:
    """Factory for creating stream load format handlers."""

    _formats = {
        "arrow": ArrowStreamLoadFormat,
    }

    @classmethod
    def get_format(cls, format_name: str) -> StreamLoadFormat:
        """Get a stream load format handler by name."""
        if format_name not in cls._formats:
            available_formats = list(cls._formats.keys())
            raise ValueError(
                f"Unsupported format '{format_name}'. Available formats: {available_formats}"
            )

        return cls._formats[format_name]()


def block_to_arrow_table(block: Block) -> pa.Table:
    """Convert various data types to PyArrow Table format.

    Args:
        data: Input data in supported formats

    Returns:
        PyArrow Table representation of the data

    Raises:
        TypeError: If data type is not supported
    """
    if isinstance(block, list):
        if not block:
            raise ValueError("Cannot create table from empty list")
        # Assume list of dicts
        table = pa.Table.from_pylist(block)
    elif isinstance(block, pd.DataFrame):
        table = pa.Table.from_pandas(block, preserve_index=False)
    elif isinstance(block, pa.Table):
        table = block
    elif isinstance(block, pa.RecordBatch):
        table = pa.Table.from_batches([block])
    elif isinstance(block, Iterable):
        # Assume iterable of RecordBatch
        batches = list(block)
        if not batches:
            raise ValueError("Cannot create table from empty iterable")
        table = pa.Table.from_batches(batches)
    else:
        raise TypeError(
            f"Unsupported data type {type(block)}. Supported types: list of dicts, pandas DataFrame, pyarrow Table, pyarrow RecordBatch, or iterable of RecordBatch."
        )


    # NOTE: Cast any list[double] columns to list[float32] to ensure consistency.
    # This fixes the issue where Python list[float] becomes list[double] in Arrow.
    # Any better way?

    new_columns = []
    for col_name in table.column_names:
        col = table.column(col_name)
        if pa.types.is_list(col.type) and pa.types.is_floating(col.type.value_type):
            if col.type.value_type == pa.float64():
                # Cast float64 to float32
                new_col = col.cast(pa.list_(pa.float32()))
                new_columns.append((col_name, new_col))
            else:
                new_columns.append((col_name, col))
        elif pa.types.is_int64(col.type):
            # Cast int64 to int32
            new_col = col.cast(pa.int32())
            new_columns.append((col_name, new_col))
        else:
            new_columns.append((col_name, col))

    if new_columns:
        table = pa.Table.from_arrays(
            [col for _, col in new_columns], names=[name for name, _ in new_columns]
        )

    import pdb; pdb.set_trace()
    return table


class DorisDDLCompiler:
    """Doris-specific DDL compiler for table creation with vector indexes."""

    def compile_create_table(self, table_options) -> str:
        """Compile CREATE TABLE statement for Doris with optional vector index."""

        # Build column definitions
        column_defs = []
        for col_name, col_type in table_options.columns.items():
            nullable = "NOT NULL" if col_name == table_options.vector_column else ""
            column_defs.append(f"`{col_name}` {col_type} {nullable}".strip())
        columns_sql = ",".join(column_defs)

        # Build index clause
        index_clause = ""
        if table_options.vector_column and table_options.vector_options:
            index_clause = f""",INDEX idx_{table_options.vector_column}(`{table_options.vector_column}`) USING ANN PROPERTIES("index_type"="{table_options.vector_options['index_type']}","metric_type"="{table_options.vector_options['metric_type']}","dim"={table_options.vector_options['dim']})"""

        # Build table properties
        properties_clause = ""
        if table_options.table_properties:
            props = []
            for key, value in table_options.table_properties.items():
                if isinstance(value, str):
                    props.append(f'"{key}"="{value}"')
                else:
                    props.append(f'"{key}"={value}')
            properties_clause = f" PROPERTIES({','.join(props)})"

        # Construct full DDL
        ddl = f"""CREATE TABLE `{table_options.table_name}`({columns_sql}{index_clause}) DUPLICATE KEY(`{table_options.key_column}`) DISTRIBUTED BY HASH(`{table_options.key_column}`) BUCKETS {table_options.num_buckets}{properties_clause};"""

        return ddl


class DorisVectorClient:
    """Client for Doris Vector Search operations."""

    def __init__(
        self,
        database: str = "default",
        auth_options: Optional[AuthOptions] = None,
        load_options: Optional[LoadOptions] = None,
    ):
        self.database = database
        self.auth_options = auth_options if auth_options else AuthOptions()
        self.load_options = load_options if load_options else LoadOptions()

        # Create direct mysql.connector connection
        self.connection = mysql.connector.connect(
            host=self.auth_options.host,
            port=self.auth_options.query_port,
            user=self.auth_options.user,
            password=self.auth_options.password,
            database=self.database
        )

        self.ddl_compiler = DorisDDLCompiler()

        # Set default session variables
        self.with_sessions({
            "enable_profile": "false",
            "parallel_pipeline_task_num": "1",
            "num_scanner_threads": "1",
        })

    def _get_stream_load_url(self, table_name: str) -> str:
        """Get the Stream Load URL for the given table."""
        return f"http://{self.auth_options.host}:{self.auth_options.http_port}/api/{self.database}/{table_name}/_stream_load"

    def _send_stream_load_request(
        self,
        table_name: str,
        data: pa.Table,
        schema_info: TableSchema,
        load_format: StreamLoadFormat,
        max_retry: int = 3,
    ):
        """Send data via Stream Load API."""
        # Serialize data
        serialized_data = load_format.serialize_data(data, schema_info)

        url = self._get_stream_load_url(table_name)
        logger.debug(
            f"Stream load to {url}, data size {len(serialized_data) / 1024 / 1024:.2f} MB, format: {load_format.format_name}"
        )

        # Build Basic Auth
        auth = HTTPBasicAuth(self.auth_options.user, self.auth_options.password)

        # Build headers
        headers = {
            "Content-Type": load_format.content_type,
            "Expect": "100-continue",
        }

        # Add format-specific headers
        headers.update(load_format.get_headers())

        # Send request with retry logic
        for attempt in range(max_retry):
            response = None
            try:
                session = requests.Session()
                session.should_strip_auth = (
                    lambda old_url, new_url: False
                )  # Don't strip auth

                response = session.put(
                    url,
                    data=serialized_data,
                    headers=headers,
                    timeout=36000,
                    auth=auth,
                )
                response.raise_for_status()

                result = response.json()
                if result.get("Status") != "Success":
                    logger.error(f"Stream load failed: {result}")
                    if result.get("Status") != "Publish Timeout":
                        raise Exception(f"Stream load failed: {result}")
                return

            except requests.exceptions.HTTPError as e:
                if response and response.status_code == 307:  # Redirect
                    url = response.headers.get("Location", url)
                    logger.debug(f"Redirect to {url}")
                    continue

                try:
                    error_result = response.json() if response else {}
                except Exception:
                    error_result = response.text if response else ""

                status_code = response.status_code if response else "unknown"
                logger.error(f"Stream load HTTP error {status_code}: {error_result}")
                raise

            except Exception as e:
                logger.exception(
                    f"Stream load request failed (attempt {attempt + 1}): {e}"
                )

        raise Exception(f"Stream load failed after {max_retry} attempts")

    def _insert_data_stream_load(
        self,
        table_name: str,
        data: pa.Table,
        schema_info: TableSchema,
        load_options: LoadOptions,
    ):
        """Insert data using Stream Load for better performance with large datasets."""
        # Get the format handler
        load_stream = StreamLoadFormatFactory.get_format(load_options.format)

        # If data is small, use single request
        if data.num_rows <= self.load_options.batch_size:
            self._send_stream_load_request(table_name, data, schema_info, load_stream)
        else:
            # Split into batches for large datasets
            self._insert_data_stream_load_batch(
                table_name, data, schema_info, load_options
            )

        logger.debug(
            f"Successfully inserted {data.num_rows} rows into {table_name} using Stream Load ({load_options.format} format)"
        )

    def _insert_data_stream_load_batch(
        self,
        table_name: str,
        data: pa.Table,
        schema_info: TableSchema,
        load_options: LoadOptions,
        num_parallel: int = 8,
    ):
        """Insert data in batches using concurrent Stream Load."""
        # Get the format handler
        load_format = StreamLoadFormatFactory.get_format(load_options.format)

        batch_size = self.load_options.batch_size
        num_batches = math.ceil(data.num_rows / batch_size)

        logger.debug(
            f"Inserting {data.num_rows} rows in {num_batches} batches of size {batch_size} ({load_format.format_name} format)"
        )

        # Create batches
        batches = []
        for i in range(0, data.num_rows, batch_size):
            end_idx = min(i + batch_size, data.num_rows)
            batch_data = data.slice(i, end_idx - i)
            batches.append(batch_data)

        # Process batches concurrently
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(num_batches, num_parallel)
        ) as executor:
            futures = []
            for batch_idx, batch_data in enumerate(batches):
                future = executor.submit(
                    self._process_batch_stream_load,
                    table_name,
                    batch_data,
                    schema_info,
                    load_options,
                    batch_idx,
                )
                futures.append(future)

            # Wait for all batches to complete
            for future in concurrent.futures.as_completed(futures):
                future.result()

    def _process_batch_stream_load(
        self,
        table_name: str,
        batch_data: pa.Table,
        schema_info: TableSchema,
        load_options: LoadOptions,
        batch_idx: int,
    ):
        """Process a single batch for Stream Load."""
        # Get the format handler
        load_format = StreamLoadFormatFactory.get_format(load_options.format)

        self._send_stream_load_request(table_name, batch_data, schema_info, load_format)
        logger.debug(f"Batch {batch_idx} completed")

    def _validate_input_data(self, data: pa.Table):
        """Validate input Arrow Table has required structure."""
        if data.num_rows == 0:
            raise ValueError("Input Arrow Table cannot be empty")

        # Check for exactly one vector column
        vector_columns = []
        non_vector_columns = []

        for col_name in data.column_names:
            col = data.column(col_name)
            # Get first non-null value for type checking
            sample_value = None
            for i in range(min(10, data.num_rows)):  # Check first 10 rows
                val = col[i]
                if val is not None:
                    try:
                        py_val = val.as_py()
                        if py_val is not None:
                            sample_value = py_val
                            break
                    except:
                        continue

            # Check if it's a list/array type (vector)
            if (
                isinstance(sample_value, list)
                and sample_value
                and isinstance(sample_value[0], (int, float))
            ):
                vector_columns.append(col_name)
            else:
                non_vector_columns.append(col_name)

        if len(vector_columns) == 0:
            raise ValueError(
                "Input Arrow Table must have exactly one vector column (list of numbers)"
            )
        elif len(vector_columns) > 1:
            raise ValueError(
                f"Input Arrow Table can have only one vector column, found: {vector_columns}"
            )

        if len(non_vector_columns) == 0:
            raise ValueError(
                "Input Arrow Table must have at least one non-vector column for the key"
            )

        logger.debug(
            f"Validated input data: key column '{non_vector_columns[0]}', vector column '{vector_columns[0]}', {len(data.columns)} total columns"
        )

    def _infer_schema_from_data(self, data: pa.Table) -> TableSchema:
        """Infer Doris schema from Arrow Table."""
        columns: Dict[str, Dict[str, Any]] = {}
        vector_column: Optional[str] = None
        vector_dim: int = 0
        key_column: Optional[str] = None

        # First pass: identify vector and non-vector columns
        vector_columns = []
        non_vector_columns = []

        for col_name in data.column_names:
            col = data.column(col_name)
            # Get first non-null value for type checking
            sample_value = None
            for i in range(min(10, data.num_rows)):  # Check first 10 rows
                val = col[i]
                if val is not None:
                    try:
                        py_val = val.as_py()
                        if py_val is not None:
                            sample_value = py_val
                            break
                    except:
                        continue

            if (
                isinstance(sample_value, list)
                and sample_value
                and isinstance(sample_value[0], (int, float))
            ):
                vector_columns.append(col_name)
            else:
                non_vector_columns.append(col_name)

        # Set key column as the first non-vector column
        if non_vector_columns:
            key_column = non_vector_columns[0]

        # Second pass: infer schema for each column
        for col_name in data.column_names:
            col = data.column(col_name)
            # Sample first non-null value
            sample_value = None
            for i in range(min(10, data.num_rows)):  # Check first 10 rows
                val = col[i]
                if val is not None:
                    try:
                        py_val = val.as_py()
                        if py_val is not None:
                            sample_value = py_val
                            break
                    except:
                        continue

            if sample_value is None:
                # Default to TEXT for empty columns
                columns[col_name] = {"doris_type": "TEXT"}
                continue

            # Infer type from sample value
            if isinstance(sample_value, list):
                # Check if it's a vector (list of numbers)
                if sample_value and isinstance(sample_value[0], (int, float)):
                    columns[col_name] = {"doris_type": "ARRAY<FLOAT>"}
                    vector_column = col_name
                    vector_dim = len(sample_value)
                else:
                    raise ValueError(
                        f"Unsupported list type in column '{col_name}': {type(sample_value[0])}"
                    )
            elif isinstance(sample_value, int):
                columns[col_name] = {"doris_type": "INT"}
            elif isinstance(sample_value, float):
                columns[col_name] = {"doris_type": "FLOAT"}
            elif isinstance(sample_value, str):
                columns[col_name] = {"doris_type": "TEXT"}  # VARCHAR?
            else:
                # Default to TEXT for unknown types
                logger.warning(
                    f"Unknown type for column '{col_name}': {type(sample_value)}, defaulting to TEXT"
                )
                columns[col_name] = {"doris_type": "TEXT"}

        return TableSchema(
            columns=columns,
            vector_column=vector_column,
            vector_dim=vector_dim,
            key_column=key_column,
        )

    def _get_alive_be_count(self) -> int:
        """Get the count of alive backends."""
        try:
            cursor = self.connection.cursor()
            try:
                cursor.execute("SHOW BACKENDS")
                rows = cursor.fetchall()
                # Get column names from cursor.description
                col_names = [desc[0] for desc in cursor.description] if cursor.description else []
                alive_idx = None
                if col_names:
                    for i, n in enumerate(col_names):
                        if str(n).lower() == "alive":
                            alive_idx = i
                            break
                count = 0
                if alive_idx is None:
                    # Fallback: assume all rows are backends
                    count = len(rows) if rows else 0
                else:
                    for r in rows:
                        sval = str(r[alive_idx]).strip().lower()
                        if sval in ("true", "1", "yes", "y"):
                            count += 1
                return max(1, count)
            finally:
                cursor.close()
        except Exception as e:
            logger.warning(f"SHOW BACKENDS failed, fallback to 1 bucket: {e}")
            return 1

    def create_table(
        self,
        table_name: str,
        block: Block,
        create_index: bool = True,
        index_options: Optional[Dict[str, Any]] = None,
        load_options: Optional[LoadOptions] = None,
        overwrite: bool = False,
    ):
        """Create a new table from various data formats with dynamic schema inference.

        Args:
            table_name: Name of the table to create
            block: Input data in supported formats:
                - list of dicts
                - pandas DataFrame
                - pyarrow Table
                - pyarrow RecordBatch
                - iterable of pyarrow RecordBatch
            create_index: Whether to create ANN vector index (default: True)
            index_options: Configuration options for the vector index (default: None, uses defaults)
            load_options: Options for data loading (default: None, uses arrow format)
            overwrite: Whether to drop the table if it already exists (default: False)
        """
        # Set default load options if not provided
        if not load_options:
            load_options = self.load_options or LoadOptions()
        if not self.load_options:
            self.load_options = load_options

        # Convert data to Arrow Table format
        arrow_table = block_to_arrow_table(block)

        # Validate input data
        self._validate_input_data(arrow_table)

        # Check if table already exists
        try:
            cursor = self.connection.cursor()
            try:
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if cursor.fetchone():
                    if overwrite:
                        logger.debug(
                            f"Table '{table_name}' already exists. Dropping it as requested."
                        )
                        self.drop_table(table_name)
                    else:
                        logger.debug(
                            f"Table '{table_name}' already exists. Skipping creation."
                        )
                        return
            finally:
                cursor.close()
        except Exception as e:
            if "detailMessage = Unknown table" in f"{e}":
                pass
            else:
                raise e

        # Infer schema from data
        schema_info = self._infer_schema_from_data(arrow_table)

        # Prepare column definitions
        columns = {}
        key_column = schema_info.key_column
        vector_column = schema_info.vector_column

        if not key_column:
            raise ValueError("No suitable key column found in data")

        for col_name, col_info in schema_info.columns.items():
            columns[col_name] = col_info["doris_type"]

        # Prepare vector options
        vector_options = None
        if create_index:
            if index_options is None:
                index_options = {"index_type": "hnsw", "metric_type": "l2_distance", "dim": schema_info.vector_dim}

            vector_options = {
                "index_type": index_options["index_type"],
                "metric_type": index_options["metric_type"],
                "dim": schema_info.vector_dim,
            }

        # Determine buckets by counting alive backends
        num_buckets = self._get_alive_be_count()
        logger.debug(f"Using {num_buckets} BUCKETS according to alive backends")

        # Create TableOptions object (simplified)
        class TableOptions:
            def __init__(self, table_name, columns, key_column, vector_column, vector_options, num_buckets):
                self.table_name = table_name
                self.columns = columns
                self.key_column = key_column
                self.vector_column = vector_column
                self.vector_options = vector_options
                self.table_properties = {"replication_num": "1"}
                self.num_buckets = num_buckets

        table_options = TableOptions(
            table_name=table_name,
            columns=columns,
            key_column=key_column,
            vector_column=vector_column if create_index else None,
            vector_options=vector_options,
            num_buckets=num_buckets,
        )

        # Compile DDL
        ddl = self.ddl_compiler.compile_create_table(table_options)

        logger.debug(f"Creating table with DDL: {ddl}")

        # Execute DDL
        cursor = self.connection.cursor()
        try:
            cursor.execute(ddl)

            # Insert data using stream load
            self._insert_data_stream_load(
                table_name, arrow_table, schema_info, load_options
            )
        finally:
            cursor.close()

    def drop_table(self, table_name: str):
        """Drop a table from the database.

        Args:
            table_name: Name of the table to drop

        Raises:
            Exception: If table drop fails
        """
        logger.debug(f"Dropping table '{table_name}'")

        try:
            ddl = f"DROP TABLE IF EXISTS `{table_name}`"

            logger.debug(f"Executing SQL: {ddl}")

            cursor = self.connection.cursor()
            try:
                cursor.execute(ddl)
            finally:
                cursor.close()
            logger.debug(f"Successfully dropped table '{table_name}'")
        except Exception as e:
            logger.error(f"Failed to drop table '{table_name}': {e}")
            raise

    def with_sessions(self, variables: Dict[str, Any]):
        """Set multiple session variables in Doris.

        Args:
            variables: Dictionary of variable names to values
        """
        for key, value in variables.items():
            self.with_session(key, value)

    def with_session(self, key: str, value: Any) -> None:
        """Set a session variable in Doris.

        Args:
            key: The session variable name
            value: The value to set for the variable
        """
        if isinstance(value, str):
            sql = f"SET SESSION {key} = '{value}'"
        else:
            sql = f"SET SESSION {key} = {value}"
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql)
        finally:
            cursor.close()
        logger.debug(f"Set session variable {key} = {value}")

    def close(self):
        """Close the client connection."""
        if self.connection:
            self.connection.close()


def upload_arrow_data(ids, texts, embeddings, table_name="my_table2", database="test", host="localhost", query_port=9030, http_port=8030, user="root", password=""):
    """
    Upload Arrow data to Doris table using streamload.
    
    Args:
        ids: List of integers for the id column
        embeddings: List of lists of floats for the embedding column
        table_name: Name of the table to create/upload to
        database: Database name
        host: Doris host
        query_port: Query port
        http_port: HTTP port
        user: Username
        password: Password
    """
    # Validate input
    if len(ids) != len(embeddings):
        raise ValueError("ids and embeddings must have the same length")
    
    if not ids:
        raise ValueError("No data to upload")
    
    # Create Arrow table
    data = {
        'id': ids,
        'text': texts,
        'embedding': embeddings
    }
    arrow_table = pa.table(data)
    
    # Create client
    auth_options = AuthOptions(
        host=host,
        query_port=query_port,
        http_port=http_port,
        user=user,
        password=password
    )
    
    load_options = LoadOptions(format="arrow", batch_size=10000)
    
    client = DorisVectorClient(
        database=database,
        auth_options=auth_options,
        load_options=load_options
    )
    
    try:
        # Create table and upload data using streamload
        client.create_table(
            table_name=table_name,
            block=arrow_table,
            create_index=True,
            overwrite=True  # Overwrite if table exists
        )
        print(f"Successfully uploaded {len(ids)} rows to table '{table_name}'")
    finally:
        client.close()

# Example usage with user input
if __name__ == "__main__":
    # User provides ids and embeddings
    ids = [1, 2, 3, 4, 5, 6]  # python int list
    texts = ["hello", "world", "loooooooooooooooooooooooooooooooooooooooong", "short", "?", "xxxxxxxxxxxxxxxxxxxxx"]
    embeddings = [  # list[float] for each row
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
        [1.0, 1.1, 1.2],
        [1.3, 1.4, 1.5],
        [6.3, 6.4, 6.5]
    ]
    
    upload_arrow_data(ids, texts, embeddings)
