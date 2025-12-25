import json
import logging
import os
from typing import Dict, List, Tuple

import boto3
from botocore.exceptions import ClientError
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit

from .constants import (
    SPARK_POSTGRES_DRIVER,
    DatasetDatatables,
    DatasetTables,
    DomainFilters,
)
from .utils import (
    check_duplicates_in_df,
    check_mappings,
    check_sdmx_col_names_mappings,
    check_sdmx_uom_mappings,
    correct_domain_filter,
    get_spark,
)


def _get_db_secret() -> Dict[str, str]:
    session = boto3.session.Session()

    secret_name = os.getenv("DB_SECRET")

    if secret_name is not None:
        region_name = "eu-west-1"

        # Create a Secrets Manager client
        client = session.client(
            service_name="secretsmanager",
            region_name=region_name,
        )

        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            secret = get_secret_value_response["SecretString"]
            secret = json.loads(secret)  # Convert json string to dictionary
            logging.debug(secret)

        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            logging.error(e)
            raise e

    return secret


class SWSPostgresSparkReader:
    def __init__(
        self,
    ) -> None:
        self.spark: SparkSession = get_spark()
        self.jdbc_conn_properties: Dict[str, str] = _get_db_secret()
        self.jdbc_url = f"jdbc:postgresql://{self.jdbc_conn_properties['host']}:{self.jdbc_conn_properties['port']}/{self.jdbc_conn_properties['database']}"

    def read_pg_table(
        self,
        pg_table: str,
        custom_schema: str,
        partition_column: str = None,
        num_partitions: int = 1,
    ) -> DataFrame:
        logging.info(f"Reading PostgreSQL table: {pg_table}")

        if partition_column is not None and num_partitions > 1:
            df_min_max_id = (
                self.spark.read.format("jdbc")
                .option(
                    "query",
                    f"SELECT MIN(t.{partition_column}) AS min_id, MAX(t.{partition_column}) AS max_id FROM {pg_table} t",
                )
                .option("url", self.jdbc_url)
                .option("user", self.jdbc_conn_properties["user"])
                .option("password", self.jdbc_conn_properties["password"])
                .option("driver", SPARK_POSTGRES_DRIVER)
                .load()
            )

            obs_min_max_id = df_min_max_id.collect()
            min_id = obs_min_max_id[0][0]
            max_id = obs_min_max_id[0][1]

            logging.info(f"min_id: {min_id}")
            logging.info(f"max_id: {max_id}")
            logging.info(f"num_partitions: {num_partitions}")

            logging.info(f"{pg_table} read start")

            if min_id is None or max_id is None:
                df = (
                    self.spark.read.format("jdbc")
                    .option("customSchema", custom_schema)
                    .option("dbtable", pg_table)
                    .option("fetchsize", "1000")
                    .option("url", self.jdbc_url)
                    .option("user", self.jdbc_conn_properties["user"])
                    .option("password", self.jdbc_conn_properties["password"])
                    .option("driver", SPARK_POSTGRES_DRIVER)
                    .load()
                )
            else:
                df = (
                    self.spark.read.format("jdbc")
                    .option("customSchema", custom_schema)
                    .option("dbtable", pg_table)
                    .option("partitionColumn", partition_column)
                    .option("lowerBound", min_id)
                    .option("upperBound", max_id)
                    .option("numPartitions", num_partitions)
                    .option("fetchsize", "1000")
                    .option("url", self.jdbc_url)
                    .option("user", self.jdbc_conn_properties["user"])
                    .option("password", self.jdbc_conn_properties["password"])
                    .option("driver", SPARK_POSTGRES_DRIVER)
                    .load()
                    # .repartition(1024, partition_column)
                    # .sortWithinPartitions(partition_column)
                    # .cache()
                )
        else:
            df = (
                self.spark.read.format("jdbc")
                .option("customSchema", custom_schema)
                .option("dbtable", pg_table)
                .option("fetchsize", "1000")
                .option("url", self.jdbc_url)
                .option("user", self.jdbc_conn_properties["user"])
                .option("password", self.jdbc_conn_properties["password"])
                .option("driver", SPARK_POSTGRES_DRIVER)
                .load()
            )

        return df

    def read_pg_table_and_check_duplicates_for_domain(
        self,
        pg_table: str,
        table_name: str,
        custom_schema: str,
        domain_code: str,
        unique_columns: List[str],
    ) -> DataFrame:

        df = self.read_pg_table(
            pg_table=pg_table, custom_schema=custom_schema
        ).transform(
            correct_domain_filter, domain=domain_code, unique_columns=unique_columns
        )

        check_duplicates_in_df(
            df,
            table_name=table_name,
            unique_columns=unique_columns,
        )

        return df

    def import_pg_table_to_iceberg(
        self,
        pg_table: str,
        iceberg_table: str,
        custom_schema: str,
        partition_column: str = None,
        num_partitions: int = 1,
    ) -> DataFrame:

        df: DataFrame = self.read_pg_table(
            pg_table=pg_table,
            custom_schema=custom_schema,
            partition_column=partition_column,
            num_partitions=num_partitions,
        )

        # Write the dataframe to S3
        df.writeTo(iceberg_table).createOrReplace()

        logging.info(f"{pg_table} written to {iceberg_table}")

        return df

    def _import_tables(self, tables: List[Tuple[str, str, int]]) -> List[DataFrame]:
        # Helper function to import tables into Iceberg, load into Spark, and return as DataFrames
        dfs = []
        for table, partition_column, num_partitions in tables:
            self.import_pg_table_to_iceberg(
                pg_table=table.postgres_id,
                iceberg_table=table.iceberg_id,
                custom_schema=table.schema,
                partition_column=partition_column,
                num_partitions=num_partitions,
            )
            dfs.append(self.spark.table(table.iceberg_id))
        return dfs

    def import_data_tables(self, dataset_tables: DatasetTables) -> List[DataFrame]:
        # Define and import data tables with partitioning
        data_tables = [
            (dataset_tables.OBSERVATION, "id", 10),
            (dataset_tables.OBSERVATION_COORDINATE, "id", 10),
            (dataset_tables.METADATA, "id", 10),
            (dataset_tables.METADATA_ELEMENT, "metadata", 10),
            (dataset_tables.TAG_OBSERVATION, "tag", 10),
        ]
        return self._import_tables(data_tables)

    def import_reference_data_tables(
        self, dataset_tables: DatasetTables
    ) -> List[DataFrame]:
        # Define and import reference data tables without partitioning
        reference_data_tables = [
            dataset_tables.FLAG_METHOD,
            dataset_tables.FLAG_OBS_STATUS,
            dataset_tables.METADATA_TYPE,
            dataset_tables.METADATA_ELEMENT_TYPE,
            dataset_tables.LANGUAGE,
            dataset_tables.UNIT_OF_MEASURE,
            dataset_tables.DATASET,
            *dataset_tables.CODELISTS,
        ]
        logging.info(
            f"Importing reference data tables: {[(table.postgres_id, table.iceberg_id) for table in reference_data_tables]}"
        )
        return self._import_tables(
            [(table, None, 1) for table in reference_data_tables]
        )

    def import_operational_data_tables(
        self, dataset_tables: DatasetTables
    ) -> List[DataFrame]:
        # Define and import operational data table without partitioning
        operational_data_tables = [
            (dataset_tables.USER, None, 1),
            (dataset_tables.TAG, None, 1),
        ]
        return self._import_tables(operational_data_tables)

    def import_data_reference_data_operational_data(
        self, dataset_tables: DatasetTables
    ) -> Tuple[
        Tuple[DataFrame, DataFrame, DataFrame, DataFrame, DataFrame],
        Tuple[
            DataFrame,
            DataFrame,
            DataFrame,
            DataFrame,
            DataFrame,
            DataFrame,
            DataFrame,
            List[DataFrame],
        ],
        Tuple[DataFrame, DataFrame],
    ]:
        # Import and organize DataFrames into the desired output structure
        data_dfs = self.import_data_tables(dataset_tables)
        reference_data_dfs = self.import_reference_data_tables(dataset_tables)
        operational_data_dfs = self.import_operational_data_tables(dataset_tables)

        return (
            tuple(data_dfs),
            (
                *reference_data_dfs[:7],
                reference_data_dfs[7:],
            ),
            tuple(operational_data_dfs),
        )

    def get_codelist_type_mapping(
        self,
        domain_code: str,
        dimension_flag_columns: List[str],
    ) -> Dict[str, str]:

        df = (
            self.read_pg_table(
                pg_table=DatasetDatatables.MAPPING_CODELIST_TYPE.id,
                custom_schema=DatasetDatatables.MAPPING_CODELIST_TYPE.schema,
            )
            .transform(
                correct_domain_filter, domain=domain_code, unique_columns=["col_name"]
            )
            .filter(col("col_name").isin(dimension_flag_columns))
        )

        check_duplicates_in_df(
            df,
            table_name=DatasetDatatables.MAPPING_CODELIST_TYPE.name,
            unique_columns=["col_name"],
        )

        check_mappings(
            column_mappings=[row[0] for row in df.select("col_name").collect()],
            columns=dimension_flag_columns,
            table_name=DatasetDatatables.MAPPING_CODELIST_TYPE.name,
        )

        return {
            row["col_name"]: row["col_type"]
            for row in df.select("col_name", "col_type").collect()
        }

    def get_mapping_code_correction_datatable(
        self,
        domain_code: str,
    ) -> DataFrame:
        df = self.read_pg_table(
            pg_table=DatasetDatatables.MAPPING_CODE_CORRECTION.id,
            custom_schema=DatasetDatatables.MAPPING_CODE_CORRECTION.schema,
        )
        df.filter(
            col("mapping_type").isNull() | (col("mapping_type") == lit(""))
        ).transform(
            correct_domain_filter, domain=domain_code, unique_columns=["old_code"]
        )

        return df

    def get_domain_code_source_datasets_ids_dest_dataset_id(
        self, dataset_id: str, domain_code: str = None
    ) -> Tuple[str, List[str], str]:
        mapping_domains_id_df = self.read_pg_table(
            pg_table=DatasetDatatables.MAPPING_DOMAINS_ID.id,
            custom_schema=DatasetDatatables.MAPPING_DOMAINS_ID.schema,
        )

        if domain_code is None:
            domain_code_df = mapping_domains_id_df.filter(
                col("sws_source_id") == lit(dataset_id)
            ).select("domain")

            if domain_code_df.count() == 0:
                raise ValueError(
                    f'There is no row connecting the current source dataset id ({dataset_id}) to any domain in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}"'
                )

            if domain_code_df.count() > 1:
                raise ValueError(
                    f'There is more than one domain referencing the current source dataset id ({dataset_id}) in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}", please specify the domain code you want to process in the parameters'
                )

            domain_code = domain_code_df.collect()[0][0]

        source_datasets_ids = [
            row[0]
            for row in (
                mapping_domains_id_df.filter(col("domain") == lit(domain_code))
                .select("sws_source_id")
                .collect()
            )
        ]
        dest_datasets_id_df = (
            mapping_domains_id_df.filter(col("domain") == lit(domain_code))
            .select("sws_destination_id")
            .distinct()
        )

        if dest_datasets_id_df.count() == 0:
            raise ValueError(
                f'There is no row connecting the current source dataset id and domain pair ({dataset_id}, {domain_code}) to any destination dataset id in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}"'
            )
        if dest_datasets_id_df.count() > 1:
            raise ValueError(
                f'The source dataset id and domain pair ({dataset_id}, {domain_code}) must point only to one destination dataset in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}"'
            )

        dest_datasets_id = dest_datasets_id_df.collect()[0][0]

        logging.info(f"domain code: {domain_code}")
        logging.info(f"source datasets ids: {source_datasets_ids}")
        logging.info(f"dest datasets ids: {dest_datasets_id}")

        return (domain_code, source_datasets_ids, dest_datasets_id)

    def get_dest_dataset_id(self, domain_code: str, dataset_id: str) -> Tuple[str, str]:

        df = self.read_pg_table(
            pg_table=DatasetDatatables.MAPPING_DOMAINS_ID.id,
            custom_schema=DatasetDatatables.MAPPING_DOMAINS_ID.schema,
        ).filter(
            (col("domain") == lit(domain_code))
            & (col("sws_source_id") == lit(dataset_id))
        )

        if df.count() == 0:
            raise ValueError(
                f'There is no row connecting the current sws_source_id ({dataset_id}) to the domain {domain_code} in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}"'
            )
        if df.count() > 1:
            raise ValueError(
                f'The sws_source_id and domain pair ({dataset_id}, {domain_code}) must appear in only one row in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}" (must be unique)'
            )

        domain_code, destination_dataset_id = df.select(
            "domain", "sws_destination_id"
        ).collect()[0]

        return destination_dataset_id

    def get_domain_code_dest_dataset_id(self, dataset_id: str) -> Tuple[str, str]:

        df = self.read_pg_table(
            pg_table=DatasetDatatables.MAPPING_DOMAINS_ID.id,
            custom_schema=DatasetDatatables.MAPPING_DOMAINS_ID.schema,
        ).filter(col("sws_source_id") == lit(dataset_id))

        if df.count() == 0:
            raise ValueError(
                f'There is no row connecting the current sws_source_id ({dataset_id}) to a domain in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}"'
            )
        if df.count() > 1:
            raise ValueError(
                f'The sws_source_id ({dataset_id}) must appear in only one row in the table "{DatasetDatatables.MAPPING_DOMAINS_ID.name}" (must be unique)'
            )

        domain_code, destination_dataset_id = df.select(
            "domain", "sws_destination_id"
        ).collect()[0]

        return (domain_code, destination_dataset_id)

    def import_sdmx_mapping_datatables(
        self, domain_code: str
    ) -> Tuple[DataFrame, DataFrame, DataFrame]:

        df_mapping_sdmx_codes = self.read_pg_table_and_check_duplicates_for_domain(
            pg_table=DatasetDatatables.MAPPING_SDMX_CODES.id,
            table_name=DatasetDatatables.MAPPING_SDMX_CODES.name,
            custom_schema=DatasetDatatables.MAPPING_SDMX_CODES.schema,
            domain_code=domain_code,
            unique_columns=["internal_code"],
        )
        df_mapping_sdmx_uom = self.read_pg_table_and_check_duplicates_for_domain(
            pg_table=DatasetDatatables.MAPPING_UNITS_OF_MEASURE.id,
            table_name=DatasetDatatables.MAPPING_UNITS_OF_MEASURE.name,
            custom_schema=DatasetDatatables.MAPPING_UNITS_OF_MEASURE.schema,
            domain_code=domain_code,
            unique_columns=["sws_code", "sws_multiplier"],
        ).transform(check_sdmx_uom_mappings)

        df_mapping_sdmx_col_names = self.read_pg_table(
            pg_table=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.id,
            custom_schema=DatasetDatatables.MAPPING_SDMX_COLUMN_NAMES.schema,
        ).transform(check_sdmx_col_names_mappings, domain_code=domain_code)

        return (df_mapping_sdmx_codes, df_mapping_sdmx_uom, df_mapping_sdmx_col_names)

    def import_diss_filter_datatables(
        self,
        domain_code: str,
        mapping_dim_col_name_type: Dict[str, str],
    ) -> Dict[str, DataFrame]:

        # General rules per dimension
        return {
            col_type: self.read_pg_table(
                pg_table=DatasetDatatables.DISSEMINATION_TYPE_LIST.id.format(
                    type=col_type
                ),
                custom_schema=DatasetDatatables.DISSEMINATION_TYPE_LIST.schema,
            ).transform(
                correct_domain_filter, domain=domain_code, unique_columns=["code"]
            )
            for col_type in mapping_dim_col_name_type.values()
            if col_type != "other"
        }

    def import_diss_exceptions_datatable(
        self,
        domain_code: str,
    ) -> DataFrame:
        # Dissemination exception
        return self.read_pg_table(
            pg_table=DatasetDatatables.DISSEMINATION_EXCEPTIONS.id,
            custom_schema=DatasetDatatables.DISSEMINATION_EXCEPTIONS.schema,
        ).transform(
            correct_domain_filter,
            domain=domain_code,
            unique_columns=[
                "domain",
                "dim1_code",
                "dim2_code",
                "dim3_code",
                "dim4_code",
                "dim5_code",
                "dim6_code",
                "dim7_code",
                "status_flag",
                "method_flag",
                "dissemination",
                "aggregation",
            ],
        )

    def get_display_decimals_datatable(
        self,
        domain_code: str,
    ) -> DataFrame:
        df = self.read_pg_table(
            pg_table=DatasetDatatables.DISPLAY_DECIMALS.id,
            custom_schema=DatasetDatatables.DISPLAY_DECIMALS.schema,
        ).filter(col("domain") == lit(domain_code))

        pairs = df.select("column_1_name", "column_2_name").distinct().collect()

        # If no config exists for this domain, fail early
        if not pairs:
            msg = (
                f'No display-decimals configuration found for domain "{domain_code}". '
                f'Please add an entry in table "{DatasetDatatables.DISPLAY_DECIMALS.id}".'
            )
            logging.error(msg)
            # raise ValueError(msg)

        # If more than one mapping exists, it's invalid
        if len(pairs) > 1:
            formatted_pairs = [(p["column_1_name"], p["column_2_name"]) for p in pairs]

            msg = (
                f'Invalid configuration for domain "{domain_code}". '
                f"Expected exactly one (column_1_name, column_2_name) pair, but found {len(pairs)}: "
                f"{formatted_pairs}. "
                f'Please correct the table "{DatasetDatatables.DISPLAY_DECIMALS.id}".'
            )

            logging.error(
                "Multiple display-decimals column pairs detected",
                extra={
                    "domain": domain_code,
                    "pairs_found": formatted_pairs,
                },
            )
            raise ValueError(msg)

        return df
