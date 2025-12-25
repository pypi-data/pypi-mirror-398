import logging
from pyspark.sql import functions as F, SparkSession

logger = logging.getLogger("KeplerSDK")

def archive_from_kepler(
    spark: SparkSession,
    usecase_id: str,
    archive_before_date: str,
    database: str = "kepler"
):
    """
    Archives data from a primary table to an archive table for records older than a specific date.

    Args:
        spark (SparkSession): The active SparkSession.
        usecase_id (str): The use case identifier.
        archive_before_date (str): The cutoff date (YYYY-MM-DD). Data before this date will be archived.
        database (str): The Spark catalog database name.
    """
    source_table_name = f"{database}.uc_{usecase_id}"
    archive_table_name = f"{database}.uc_{usecase_id}_archive"
    logger.info(f"Starting archival for '{source_table_name}' to '{archive_table_name}'.")

    if not spark.catalog.tableExists(source_table_name):
        raise ValueError(f"Source table '{source_table_name}' does not exist.")

    data_to_archive_df = None
    try:
        data_to_archive_df = spark.table(source_table_name) \
                                  .filter(F.col("date_transaction") < F.lit(archive_before_date))
        data_to_archive_df.cache()
        
        archive_count = data_to_archive_df.count()
        if archive_count == 0:
            logger.warning("No data found before the specified date. Nothing to archive.")
            return

        logger.info(f"Found {archive_count} records to archive.")

        # Append data to the archive table, creating it if it doesn't exist
        if not spark.catalog.tableExists(archive_table_name):
            logger.info(f"Archive table '{archive_table_name}' does not exist. Creating it.")
            source_props = spark.sql(f"SHOW TBLPROPERTIES {source_table_name}").collect()
            zorder_prop = next((p.value for p in source_props if p.key == "write.zorder.column-names"), None)
            
            writer = data_to_archive_df.writeTo(archive_table_name).partitionedBy("year", "month", "day")
            if zorder_prop:
                writer.tableProperty("write.zorder.column-names", zorder_prop)
            writer.create()
        else:
            logger.info(f"Appending {archive_count} records to '{archive_table_name}'.")
            data_to_archive_df.writeTo(archive_table_name).append()

        # Delete the archived data from the source table
        logger.info(f"Deleting {archive_count} archived records from source table '{source_table_name}'.")
        delete_statement = f"DELETE FROM {source_table_name} WHERE date_transaction < '{archive_before_date}'"
        spark.sql(delete_statement)
        
        logger.info("Archival process completed successfully.")

    except Exception as e:
        logger.error(f"Archival process for usecase '{usecase_id}' failed: {e}", exc_info=True)
        raise
    finally:
        if data_to_archive_df:
            data_to_archive_df.unpersist()
