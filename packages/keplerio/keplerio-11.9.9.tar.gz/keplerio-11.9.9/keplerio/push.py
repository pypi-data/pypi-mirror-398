import logging
from pyspark.sql import functions as F, SparkSession, DataFrame
from pyspark.sql.types import StringType, LongType, DateType

logger = logging.getLogger("KeplerSDK")

# --- Constants ---
REQUIRED_COLUMNS = {"id_kepler", "id_client", "id_transaction", "pourcentage", "date_transaction"}

def push_to_kepler(
    df: DataFrame,
    usecase_id: str,
    spark: SparkSession,
    mode: str = "append",
    write_strategy: str = "merge-on-read",
    database: str = "kepler",
    hdfs_base_path: str = "/kepler-SQL",
    zorder_columns: list = None
):
    """
    Push a DataFrame into an Iceberg table with full schema evolution support.
    Auto-creates the table if missing, merges schemas if new columns appear.
    Optimized for Apache Drill and Spark Connect.

    Args:
        df: Spark DataFrame to push
        usecase_id: Unique usecase identifier
        spark: SparkSession instance
        mode: "append" or "overwrite"
        write_strategy: "merge-on-read" (recommended) or "copy-on-write"
        database: Iceberg catalog/database name
        hdfs_base_path: Base path for storage
        zorder_columns: List of columns to optimize Z-ordering
    """
    if zorder_columns is None:
        zorder_columns = ["id_kepler", "id_transaction"]

    table_name = f"{database}.uc_{usecase_id}"
    table_path = f"{hdfs_base_path}/uc_{usecase_id}"

    logger.info(f"[KeplerSDK] Pushing to {table_name} (strategy={write_strategy}, mode={mode})")

    try:
        if df.isEmpty():
            logger.warning("DataFrame is empty. Nothing to push.")
            return

        # --- Enable schema evolution ---
        spark.conf.set("spark.sql.iceberg.schema.autoMerge.enabled", "true")
        spark.conf.set("spark.sql.iceberg.handle-timestamp-without-timezone", "true")

        # --- Transformations ---
        final_df = _apply_essential_transformations(df)

        # --- Ensure table exists ---
        if not spark.catalog.tableExists(table_name):
            _create_iceberg_table(final_df, table_name, table_path, zorder_columns, write_strategy)
            logger.info(f"[KeplerSDK] Created new Iceberg table: {table_name}")
        else:
            _sync_schema(final_df, table_name, spark)

        # --- Write with schema evolution ---
        _write_with_schema_merge(final_df, table_name, mode)

        logger.info(f"[KeplerSDK] Push completed successfully for usecase '{usecase_id}'")

    except Exception as e:
        logger.error(f"[KeplerSDK] Push failed for '{usecase_id}': {str(e)}", exc_info=True)
        raise


# -----------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------

def _apply_essential_transformations(df: DataFrame) -> DataFrame:
    """Apply core transformations: partition columns + type fixes."""
    df = df \
        .withColumn("year", F.year(F.col("date_transaction"))) \
        .withColumn("month", F.month(F.col("date_transaction"))) \
        .withColumn("day", F.dayofmonth(F.col("date_transaction")))

    if "date_scoring" not in df.columns:
        df = df.withColumn("date_scoring", F.current_date())

    return _apply_drill_optimized_types(df)


def _apply_drill_optimized_types(df: DataFrame) -> DataFrame:
    """Cast key fields for Drill-friendly query performance."""
    select_exprs = []
    for col_name in df.columns:
        if col_name == "id_kepler":
            select_exprs.append(F.col(col_name).cast(LongType()).alias(col_name))
        elif col_name in ["date_transaction", "date_scoring"]:
            select_exprs.append(F.to_date(F.col(col_name)).alias(col_name))
        elif col_name in ["id_client", "id_transaction", "pourcentage"]:
            select_exprs.append(F.col(col_name).cast(StringType()).alias(col_name))
        else:
            select_exprs.append(F.col(col_name))
    return df.select(*select_exprs)


def _create_iceberg_table(df: DataFrame, table_name: str, path: str, zorder_columns: list, strategy: str):
    """Create Iceberg table with partitioning and M.O.R strategy."""
    writer = df.writeTo(table_name) \
        .tableProperty("location", path) \
        .tableProperty("format-version", "2") \
        .tableProperty("write.zorder.column-names", ",".join(zorder_columns)) \
        .partitionedBy("year", "month", "day")

    if strategy == "merge-on-read":
        writer.tableProperty("write.update.mode", "merge-on-read") \
              .tableProperty("write.delete.mode", "merge-on-read") \
              .tableProperty("write.merge.mode", "merge-on-read")
    else:
        writer.tableProperty("write.update.mode", "copy-on-write") \
              .tableProperty("write.delete.mode", "copy-on-write") \
              .tableProperty("write.merge.mode", "copy-on-write")

    writer.create()


def _sync_schema(df: DataFrame, table_name: str, spark: SparkSession):
    """
    Detects schema differences and logs new columns automatically.
    Iceberg handles actual schema evolution on write.
    """
    try:
        existing_cols = set(spark.table(table_name).columns)
        new_cols = set(df.columns) - existing_cols
        removed_cols = existing_cols - set(df.columns)

        if new_cols:
            logger.info(f"[KeplerSDK] Schema evolution detected — new columns: {list(new_cols)}")
        if removed_cols:
            logger.info(f"[KeplerSDK] Columns missing in new DataFrame: {list(removed_cols)}")

    except Exception as e:
        logger.warning(f"[KeplerSDK] Could not compare schema for {table_name}: {str(e)}")


def _write_with_schema_merge(df: DataFrame, table_name: str, mode: str):
    """Write with automatic schema merge (evolutive)."""
    if mode.lower() == "append":
        df.writeTo(table_name).append()
    elif mode.lower() == "overwrite":
        df.writeTo(table_name).overwritePartitions()
    else:
        raise ValueError(f"Invalid mode '{mode}'. Use 'append' or 'overwrite'.")


# -----------------------------------------------------------
# Optional Drill Optimization Configuration
# -----------------------------------------------------------

def configure_drill_optimized_table(usecase_id: str, spark: SparkSession, database: str = "kepler"):
    """One-time optimization for Apache Drill reads."""
    table_name = f"{database}.uc_{usecase_id}"

    props = {
        "read.split.target-size": "134217728",  # 128 MB
        "read.split.metadata-target-size": "33554432",  # 32 MB
        "commit.retry.num-retries": "5",
        "format-version": "2"
    }

    for k, v in props.items():
        spark.sql(f"ALTER TABLE {table_name} SET TBLPROPERTIES ('{k}'='{v}')")

    logger.info(f"[KeplerSDK] Applied Drill optimizations to {table_name}")
