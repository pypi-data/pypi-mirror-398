import logging
from pyspark.sql import SparkSession, DataFrame

logger = logging.getLogger("KeplerSDK")

def update_kepler(
    spark: SparkSession,
    usecase_id: str,
    updates, # NOW ACCEPTS a DataFrame or a dict
    join_key: str = "id_kepler",
    transaction_date: str = None,
    database: str = "kepler"
):
    """
    Updates a Kepler table using a DataFrame (for bulk) or a dictionary (for single row).
    If transaction_date is provided, it's used for partition pruning.

    Args:
        spark (SparkSession): The active SparkSession.
        usecase_id (str): The identifier for the use case table to update.
        updates (DataFrame or dict): The update payload.
                                     - For bulk: A DataFrame with the join_key and columns to update.
                                     - For single: A dict with the join_key and key-value pairs to update.
        join_key (str): The primary key to join on.
        transaction_date (str): Optional. The specific date ('YYYY-MM-DD') to optimize the update.
        database (str): The Spark catalog database name.
    """
    table_name = f"{database}.uc_{usecase_id}"
    updates_view_name = f"updates_{usecase_id}_{join_key}"
    
    logger.info(f"Starting MERGE INTO for table '{table_name}'.")

    # --- NEW: Intelligently handle dict or DataFrame input ---
    updates_df = None
    if isinstance(updates, DataFrame):
        logger.info("Processing update with a Spark DataFrame.")
        updates_df = updates
    elif isinstance(updates, dict):
        logger.info("Processing update with a Python dictionary, creating a single-row DataFrame.")
        if join_key not in updates:
            raise ValueError(f"The update dictionary must contain the join key '{join_key}'.")
        
        # Separate the key from the values to be updated
        key_value = updates[join_key]
        update_values = {k: v for k, v in updates.items() if k != join_key}
        
        # Create a single-row DataFrame
        data_row = (key_value, *update_values.values())
        columns = [join_key, *update_values.keys()]
        updates_df = spark.createDataFrame([data_row], columns)
    else:
        raise TypeError("The 'updates' parameter must be a Spark DataFrame or a Python dictionary.")

    # The rest of the function proceeds as before, using the generated updates_df
    if join_key not in updates_df.columns:
        raise ValueError(f"The join key '{join_key}' must be a column in the updates payload.")

    updates_df.createOrReplaceTempView(updates_view_name)

    on_clause = f"target.{join_key} = source.{join_key}"
    if transaction_date:
        on_clause += f" AND target.date_transaction = '{transaction_date}'"
        logger.info(f"Applying partition pruning for date: {transaction_date}")

    update_cols = [col for col in updates_df.columns if col != join_key]
    set_clause = ", ".join([f"target.{col} = source.{col}" for col in update_cols])
    
    if not set_clause:
        raise ValueError("The updates payload must contain at least one column to update besides the join key.")

    merge_sql = f"MERGE INTO {table_name} AS target USING {updates_view_name} AS source ON {on_clause} WHEN MATCHED THEN UPDATE SET {set_clause}"
    spark.sql(merge_sql)
    logger.info(f"MERGE operation on '{table_name}' completed successfully.")
