import logging
from pyspark.sql import functions as F, SparkSession, DataFrame

logger = logging.getLogger("KeplerSDK")

def read_from_kepler(
    spark: SparkSession,
    usecase_id: str,
    database: str = "kepler",
    start_date: str = None,
    end_date: str = None,
    columns: list = None,
    filter_expression: str = None
) -> DataFrame:
    """
    Reads data from a use-case-specific Iceberg table into a Spark DataFrame.

    Args:
        spark (SparkSession): The active SparkSession.
        usecase_id (str): The identifier for the use case table to read from.
        database (str): The Spark catalog database name.
        start_date (str): The start date for filtering (inclusive, format 'YYYY-MM-DD').
        end_date (str): The end date for filtering (inclusive, format 'YYYY-MM-DD').
        columns (list): A list of column names to select. If None, all columns are selected.
        filter_expression (str): A SQL-style WHERE clause for custom filtering.

    Returns:
        DataFrame: A Spark DataFrame containing the requested data.
    """
    table_name = f"{database}.uc_{usecase_id}"
    logger.info(f"Starting read for usecase '{usecase_id}' from table '{table_name}'.")

    if not spark.catalog.tableExists(table_name):
        raise ValueError(f"Table '{table_name}' does not exist.")

    try:
        reader = spark.table(table_name)
        if start_date:
            reader = reader.filter(F.col("date_transaction") >= F.lit(start_date))
        if end_date:
            reader = reader.filter(F.col("date_transaction") <= F.lit(end_date))

        if filter_expression:
            reader = reader.where(filter_expression)
        if columns and isinstance(columns, list) and len(columns) > 0:
            reader = reader.select(*columns)

        return reader
    except Exception as e:
        logger.error(f"Data read for usecase '{usecase_id}' failed: {e}", exc_info=True)
        raise
