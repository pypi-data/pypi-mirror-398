import logging
import os
from typing import List

import boto3
import pyspark.sql.functions as F
from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql.functions import col, lit
from pyspark.sql.window import Window
from sws_api_client import Tags
from sws_api_client.tags import BaseDisseminatedTagTable, DisseminatedTag

from .constants import DatasetDatatables, DomainFilters


def get_spark() -> SparkSession:
    session = boto3.session.Session()
    credentials = session.get_credentials()

    aws_access_key_id = credentials.access_key
    aws_secret_access_key = credentials.secret_key
    session_token = credentials.token

    # get EMR_BUCKET from environment variable
    emr_bucket = os.getenv("EMR_BUCKET")
    output_path = f"s3://{emr_bucket}"

    spark = (
        SparkSession.builder.appName("Spark-on-AWS-Lambda")
        .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id)
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key)
        .config("spark.hadoop.fs.s3a.session.token", session_token)
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider",
        )
        .config(
            "spark.hadoop.hive.metastore.client.factory.class",
            "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory",
        )
        .config("spark.jars.packages", "org.apache.iceberg")
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config(
            "spark.sql.catalog.AwsDataCatalog",
            "org.apache.iceberg.spark.SparkCatalog",
        )
        .config(
            "spark.sql.catalog.AwsDataCatalog.catalog-impl",
            "org.apache.iceberg.aws.glue.GlueCatalog",
        )
        .config("spark.sql.catalog.AwsDataCatalog.warehouse", output_path)
        .config("spark.sql.defaultCatalog", "AwsDataCatalog")
        .enableHiveSupport()
        .getOrCreate()
    )

    return spark


def col_is_null_or_empty(col_name: str) -> Column:
    return col(col_name).isNull() | (col(col_name) == lit(""))


def check_mappings(
    column_mappings: List[str], columns: List[str], table_name: str
) -> None:
    column_mappings_set = set(column_mappings)
    columns_set = set(columns)

    if not (columns_set <= column_mappings_set):
        missing_mappings = columns_set - column_mappings_set

        message = f'There mappings in the table "{table_name}" are not correct'
        message += f"\nThe following column mappings are missing: {missing_mappings}"

        raise ValueError(message)


def check_sdmx_uom_mappings(df_mapping_sdmx_uom: DataFrame) -> DataFrame:
    """
    Validates the SDMX unit of measure (UOM) mappings DataFrame to ensure compliance with defined rules.

    Args:
        df_mapping_sdmx_uom (DataFrame): DataFrame containing SDMX UOM mappings.

    Returns:
        DataFrame: The input DataFrame if all checks pass without errors.

    Raises:
        ValueError: If any of the validation checks fail.
    """

    # 1. If 'delete' is TRUE, 'sws_code' must exist, and 'sdmx_code', 'sdmx_multiplier', and 'value_multiplier' must be empty or null.
    delete_mismatch_rows = df_mapping_sdmx_uom.filter(
        (
            # Check if 'sws_code' is missing when 'delete' is TRUE.
            col_is_null_or_empty("sws_code")
            | ~col_is_null_or_empty("sdmx_code")
            | col("sdmx_multiplier").isNotNull()
            | col("value_multiplier").isNotNull()
        )
        & col("delete")
    ).collect()

    # 2. If 'delete' is FALSE, both 'sws_code' and 'sdmx_code' must exist (cannot be null or empty).
    missing_code_rows = df_mapping_sdmx_uom.filter(
        (col_is_null_or_empty("sws_code") | col_is_null_or_empty("sdmx_code"))
        & ~col("delete")
    ).collect()

    # 3. 'value_multiplier' cannot be null when 'delete' is FALSE.
    null_value_multiplier_rows = df_mapping_sdmx_uom.filter(
        col("value_multiplier").isNull() & ~col("delete")
    ).collect()

    # 4. For generic mappings, 'value_multiplier' must be 0 when both 'sws_multiplier' and 'sdmx_multiplier' are unspecified.
    generic_value_multiplier_mismatch_rows = df_mapping_sdmx_uom.filter(
        col("sws_multiplier").isNull()
        & col("sdmx_multiplier").isNull()
        & (col("value_multiplier") != lit(0))
        & ~col("delete")
    ).collect()

    # 5. 'sws_multiplier' and 'sdmx_multiplier' must either both be populated or both be empty.
    multiplier_consistency_error_rows = df_mapping_sdmx_uom.filter(
        (col("sws_multiplier").isNotNull() & col("sdmx_multiplier").isNull())
        | (col("sws_multiplier").isNull() & col("sdmx_multiplier").isNotNull())
        & ~col("delete")
    ).collect()

    # Initialize error flag and list to collect error messages.
    has_errors = False
    error_messages: List[str] = []

    # Log errors for each rule violation if applicable.
    if len(delete_mismatch_rows) > 0:
        has_errors = True
        error_message = f"Rule 1: When 'delete' is TRUE, 'sws_code' must exist, and 'sdmx_code', 'sdmx_multiplier', and 'value_multiplier' must be empty or null. Violating rows: {delete_mismatch_rows}"
        logging.error(error_message)
        error_messages.append(error_message)

    if len(missing_code_rows) > 0:
        has_errors = True
        error_message = f"Rule 2: When 'delete' is FALSE, both 'sws_code' and 'sdmx_code' must be populated. Violating rows: {missing_code_rows}"
        logging.error(error_message)
        error_messages.append(error_message)

    if len(null_value_multiplier_rows) > 0:
        has_errors = True
        error_message = f"Rule 3: Column 'value_multiplier' cannot be null when 'delete' is FALSE. Violating rows: {null_value_multiplier_rows}"
        logging.error(error_message)
        error_messages.append(error_message)

    if len(generic_value_multiplier_mismatch_rows) > 0:
        has_errors = True
        error_message = f"Rule 4: For generic mappings, 'value_multiplier' must be 0 when 'sws_multiplier' and 'sdmx_multiplier' are unspecified. Violating rows: {generic_value_multiplier_mismatch_rows}"
        logging.error(error_message)
        error_messages.append(error_message)

    if len(multiplier_consistency_error_rows) > 0:
        has_errors = True
        error_message = f"Rule 5: 'sws_multiplier' and 'sdmx_multiplier' must both be populated or both be empty. Violating rows: {multiplier_consistency_error_rows}"
        logging.error(error_message)
        error_messages.append(error_message)

    # Raise a ValueError if any validation errors were found.
    if has_errors:
        raise ValueError("Validation errors found:\n" + "\n".join(error_messages))

    return df_mapping_sdmx_uom


def check_sdmx_col_names_mappings(
    df_mapping_sdmx_column_names: DataFrame, domain_code: str
) -> DataFrame:
    # Get the correct columns to delete and check the duplicates
    df_mapping_sdmx_column_names_to_delete = (
        df_mapping_sdmx_column_names.filter(col("delete") == lit(True))
        .transform(
            correct_domain_filter,
            domain=domain_code,
            unique_columns=["internal_name"],
        )
        .transform(
            check_duplicates_in_df,
            table_name=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.name,
            unique_columns=["internal_name"],
        )
    )

    # Get the correct columns to add and check the duplicates
    df_mapping_sdmx_column_names_to_add = (
        df_mapping_sdmx_column_names.filter(col("add") == lit(True))
        .transform(
            correct_domain_filter,
            domain=domain_code,
            unique_columns=["external_name"],
        )
        .transform(
            check_duplicates_in_df,
            table_name=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.name,
            unique_columns=["external_name"],
        )
    )

    # Get the columns to rename and check for duplicates
    df_mapping_sdmx_column_names_mappings = (
        df_mapping_sdmx_column_names.filter(
            (col("delete") == lit(False)) & (col("add") == lit(False))
        )
        .transform(
            correct_domain_filter,
            domain=domain_code,
            unique_columns=["internal_name"],
        )
        .transform(
            correct_domain_filter,
            domain=domain_code,
            unique_columns=["external_name"],
        )
        .transform(
            check_duplicates_in_df,
            table_name=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.name,
            unique_columns=["internal_name"],
        )
        .transform(
            check_duplicates_in_df,
            table_name=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.name,
            unique_columns=["external_name"],
        )
    )

    # Check for duplicates in the external names in general
    df_mapping_sdmx_column_names_unique_ext = (
        df_mapping_sdmx_column_names_mappings.union(
            df_mapping_sdmx_column_names_to_delete
        )
        .transform(
            correct_domain_filter,
            domain=domain_code,
            unique_columns=["external_name"],
        )
        .transform(
            check_duplicates_in_df,
            table_name=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.name,
            unique_columns=["external_name"],
        )
    )

    # Check for duplicates in the internal names in general
    df_mapping_sdmx_column_names_unique_int = (
        df_mapping_sdmx_column_names_mappings.union(df_mapping_sdmx_column_names_to_add)
        .transform(
            correct_domain_filter,
            domain=domain_code,
            unique_columns=["internal_name"],
        )
        .transform(
            check_duplicates_in_df,
            table_name=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.name,
            unique_columns=["internal_name"],
        )
    )

    # Merge both the tables above to get only one table without repetitions
    df_mapping_sdmx_column_names_unique = df_mapping_sdmx_column_names_unique_ext.union(
        df_mapping_sdmx_column_names_unique_int
    ).dropDuplicates(["internal_name", "external_name"])

    return df_mapping_sdmx_column_names_unique


def map_codes_and_remove_null_duplicates(
    df: DataFrame,
    df_mapping: DataFrame,
    domain_code: str,
    col_name: str,
    col_type: str,
    src_column: str,
    dest_column: str,
    dimension_columns: List[str],
    flag_columns: List[str],
) -> DataFrame:

    lower_col_name = col_name.lower()
    lower_flag_columns = [column.lower() for column in flag_columns]
    lower_dimension_columns = [column.lower() for column in dimension_columns]

    # Define partitioning columns
    if lower_col_name in lower_flag_columns:
        partition_columns = dimension_columns
    else:
        partition_columns = [
            column for column in lower_dimension_columns if column != lower_col_name
        ] + ["partition_column"]

    partitioning_window = Window.partitionBy(*partition_columns)

    standard_mapping_df = df_mapping.filter(
        (col("domain").isNull() | (col("domain") == lit("")))
        & (col("var_type") == lit(col_type))
        & (col("mapping_type").isNull() | (col("mapping_type") == lit("")))
    )
    domain_mapping_df = df_mapping.filter(
        (col("domain") == lit(domain_code))
        & (col("var_type") == lit(col_type))
        & (col("mapping_type").isNull() | (col("mapping_type") == lit("")))
    )

    count_all = df.count()

    df_no_nulls = (
        df.alias("d")
        # Join the data with the standard mapping for the specific dimension
        .join(
            F.broadcast(standard_mapping_df).alias("m_standard"),
            col(f"d.{col_name}") == col(f"m_standard.{src_column}"),
            "left",
        )
        # Join the data with the domain specific mapping for the specific dimension
        .join(
            F.broadcast(domain_mapping_df).alias("m_domain"),
            col(f"d.{col_name}") == col(f"m_domain.{src_column}"),
            "left",
        )
        .select(
            "d.*",
            # Evaluate the domain specific rule first and then the general rule
            F.coalesce(
                col(f"m_domain.{dest_column}"), col(f"m_standard.{dest_column}")
            ).alias("new_dim_code"),
            F.coalesce(
                col("m_domain.delete"),
                col("m_standard.delete"),
                lit(False),
            ).alias("delete"),
            F.coalesce(col("m_standard.multiplier"), col("m_domain.multiplier")).alias(
                "multiplier"
            ),
        )
        .withColumn("partition_column", F.coalesce(col("new_dim_code"), col(col_name)))
        .withColumn("count_obs_per_point", F.count(lit(1)).over(partitioning_window))
        .withColumn("is_duplicate", col("count_obs_per_point") > lit(1))
        # Filter out all the rows that are duplicates with null value
        .filter(~(col("is_duplicate") & col("value").isNull()))
    )

    count_no_null_dupes = df_no_nulls.count()
    null_dupes_removed = count_all - count_no_null_dupes

    logging.info(f"{null_dupes_removed} duplicates with null value removed")

    df_mapped = (
        df_no_nulls
        # Count again the observations per coordinate after removing the null duplicates
        .withColumn("count_obs_per_point", F.count(lit(1)).over(partitioning_window))
        .withColumn("is_duplicate", col("count_obs_per_point") > lit(1))
        # Update the diss_flag to false for records to delete
        .withColumn(
            "diss_flag", F.when(col("delete"), lit(False)).otherwise(col("diss_flag"))
        )
        .withColumn(
            "diss_note",
            F.when(
                col("delete"),
                F.array_append(
                    col("diss_note"),
                    lit(
                        f"The observation is not disseminated according to the Mapping - Code correction table"
                    ),
                ),
            ).otherwise(col("diss_note")),
        )
        # Add mapping message to notes
        .withColumn(
            "diss_note",
            F.when(
                ~col("is_duplicate")
                & col("new_dim_code").isNotNull()
                & (col("new_dim_code") != lit("")),
                F.array_append(
                    col("diss_note"),
                    F.concat(
                        lit(f"Dimension {col_name} code was changed from "),
                        col(col_name),
                        lit(" to "),
                        col("new_dim_code"),
                    ),
                ),
            ).otherwise(col("diss_note")),
        )
        .withColumn(
            col_name,
            F.when(
                ~col("is_duplicate"),
                F.coalesce(col("new_dim_code"), col(col_name)),
            ).otherwise(col(col_name)),
        )
        .withColumn(
            "diss_flag",
            F.when(
                col("is_duplicate")
                & col("new_dim_code").isNotNull()
                & (col("new_dim_code") != lit("")),
                lit(False),
            ).otherwise(col("diss_flag")),
        )
        .withColumn(
            "diss_note",
            F.when(
                col("is_duplicate")
                & col("new_dim_code").isNotNull()
                & (col("new_dim_code") != lit("")),
                F.array_append(
                    col("diss_note"),
                    lit(
                        f"The code correction was not applied to avoid observation duplications"
                    ),
                ),
            ).otherwise(col("diss_note")),
        )
        # Check the domain specific multiplier first and then the standard multiplier
        .withColumn("value", col("value") * F.coalesce(col("multiplier"), lit(1)))
        # Remove the columns that were not in the original dataset
        .drop(
            "new_dim_code",
            "delete",
            "multiplier",
            "partition_column",
            "count_obs_per_point",
            "is_duplicate",
        )
    )

    return df_mapped


def apply_code_correction(
    df: DataFrame,
    df_mapping_code_correction: DataFrame,
    domain_code: str,
    col_name: str,
    col_type: str,
) -> DataFrame:
    logging.info(f"correcting codes for column {col_name} of type {col_type}")
    return map_codes_and_remove_null_duplicates(
        df,
        df_mapping_code_correction,
        domain_code,
        col_name,
        col_type,
        src_column="old_code",
        dest_column="new_code",
    )


def copy_cache_csv_dataset_to_tag(
    bucket: str,
    prefix: str,
    tag_name: str,
) -> None:

    logging.info(
        f"Copying the source folder '{prefix}latest/' to '{prefix}{tag_name}/'"
    )

    s3 = boto3.client("s3")

    source_prefix = f"{prefix}latest/"

    response = s3.list_objects_v2(Bucket=bucket, Prefix=source_prefix)

    s3_paths = [content["Key"] for content in response.get("Contents", {})]

    logging.debug("list_objects_v2 response:")
    logging.debug(response)
    logging.debug("objects to copy:")
    logging.debug(s3_paths)

    for s3_path in s3_paths:
        result = s3.copy(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": s3_path},
            Key=f"{s3_path.replace('latest', tag_name)}",
        )
        logging.info(result)


def save_cache_csv(
    df: DataFrame, bucket: str, prefix: str, tag_name: str, separator: str = ","
) -> None:

    s3 = boto3.client("s3")

    latest_path = f"s3://{bucket}/{prefix}/latest"
    tag_path = f"s3://{bucket}/{prefix}/{tag_name}"

    latest_prefix = f"{prefix}/latest"
    tag_prefix = f"{prefix}/{tag_name}"

    s3.delete_object(Bucket=bucket, Key=f"{latest_prefix}.csv")
    df.coalesce(1).write.csv(
        path=latest_path, mode="overwrite", sep=separator, header=True
    )

    response = s3.list_objects_v2(Bucket=bucket, Prefix=latest_prefix)

    s3_path_objects_keys = [content["Key"] for content in response.get("Contents", {})]
    s3_path_csv = [
        s3_object for s3_object in s3_path_objects_keys if s3_object.endswith(".csv")
    ][0]

    # Extract the csv from the folder and delete the folder
    result_latest = s3.copy(
        CopySource={"Bucket": bucket, "Key": s3_path_csv},
        Bucket=bucket,
        Key=f"{latest_prefix}.csv",
    )
    logging.info(f"Updated latest version of cached csv at {latest_path}.csv")

    result_tag = s3.copy(
        CopySource={"Bucket": bucket, "Key": s3_path_csv},
        Bucket=bucket,
        Key=f"{tag_prefix}.csv",
    )
    logging.info(f"Wrote the tag version of cached csv at {tag_path}.csv")

    for object in s3_path_objects_keys:
        s3.delete_object(Bucket=bucket, Key=object)
    logging.debug("Cleaning the temporary folder of the csv files")


def create_table_if_not_exists_otherwise_replace(
    spark: SparkSession, df: DataFrame, table_name: str
):
    table_exists = spark.catalog.tableExists(table_name)

    if not table_exists:
        df.writeTo(table_name).createOrReplace()
    else:
        spark.sql(f"DELETE FROM {table_name} WHERE true")
        df.writeTo(table_name).append()


def correct_domain_filter(
    df: DataFrame, domain: str, unique_columns: List[str]
) -> DataFrame:
    ordered_columns = df.columns

    # Filter for domain entries
    df_domain = df.filter(DomainFilters.MATCH(domain))

    # Filter for empty domain entries
    df_empty = df.filter(DomainFilters.EMPTY())

    # Get the difference: empty domains that are not in the domain entries
    df_empty_diff = df_empty.join(df_domain, unique_columns, "left_anti").select(
        *ordered_columns
    )

    # Combine the domain entries with the non-matching empty entries
    df_final = df_domain.union(df_empty_diff)

    return df_final


def check_duplicates_in_df(
    df: DataFrame,
    table_name: str,
    unique_columns: List[str],
) -> DataFrame:
    duplicated_values = (
        df.groupBy(*unique_columns)
        .count()
        .filter(col("count") > 1)
        .select(*unique_columns)
        .collect()
    )

    if len(duplicated_values) > 0:
        raise RuntimeError(
            f"There are the following duplicated values in the table {table_name} for the columns {str(unique_columns)}: {str(duplicated_values)}"
        )

    return df


# SWS metadata Tags management


# Function to get or create a tag
def get_or_create_tag(
    tags: Tags, dataset: str, tag_id: str, name: str, description: str = ""
):
    try:
        tag = tags.get_disseminated_tag(dataset, tag_id)
        if tag is None:
            raise Exception("Tag not found")
        logging.info(f"Tag found")
        logging.debug(f"Tag found: {tag}")
    except Exception as e:
        logging.info(f"Tag not found: {e}. Creating new tag.")
        tag = tags.create_disseminated_tag(dataset, name, tag_id, description)
    return tag


# Function to check if a table exists in the tag
def table_exists(tag: DisseminatedTag, table_id):
    for table in tag.get("tables"):
        if table.get("id") == table_id:
            return True
    return False


# Function to check if a dissemination step exists in the tag
def step_exists(tag, target, table_id):
    for step in tag["disseminationSteps"]:
        if step["target"] == target and step["table"] == table_id:
            return True
    return False


def upsert_disseminated_table(
    sws_tags: Tags,
    tag: DisseminatedTag,
    dataset_id,
    tag_name,
    table: BaseDisseminatedTagTable,
) -> DisseminatedTag:
    if table_exists(tag=tag, table_id=table.get("id")):
        return sws_tags.update_dissemination_table(
            dataset=dataset_id, tag_id=tag_name, table=table
        )
    else:
        return sws_tags.add_dissemination_table(
            dataset=dataset_id, tag_id=tag_name, table=table
        )
