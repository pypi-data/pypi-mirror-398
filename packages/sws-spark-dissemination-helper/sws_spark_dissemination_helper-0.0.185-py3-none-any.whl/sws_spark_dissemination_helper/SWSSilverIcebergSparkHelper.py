import logging
from copy import copy
from typing import List, Tuple

import pyspark.sql.functions as F
from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql.functions import col, lit
from pyspark.sql.types import ArrayType, StringType
from pyspark.sql.window import Window
from sws_api_client import Tags
from sws_api_client.tags import BaseDisseminatedTagTable, TableLayer, TableType

from .constants import IcebergDatabases, IcebergTables, DatasetDatatables
from .SWSPostgresSparkReader import SWSPostgresSparkReader
from .utils import (
    get_or_create_tag,
    map_codes_and_remove_null_duplicates,
    save_cache_csv,
    upsert_disseminated_table,
)


class SWSSilverIcebergSparkHelper:
    def __init__(
        self,
        spark: SparkSession,
        bucket: str,
        tag_name: str,
        dataset_id: str,
        sws_postgres_spark_reader: SWSPostgresSparkReader,
        iceberg_tables: IcebergTables,
        domain_code: str,
        dataset_details: dict = None,
    ) -> None:
        self.spark: SparkSession = spark
        self.dataset_details: dict = dataset_details
        self.bucket: str = bucket
        self.tag_name: str = tag_name
        self.dataset_id: str = dataset_id
        self.sws_postgres_spark_reader = sws_postgres_spark_reader
        self.iceberg_tables: IcebergTables = iceberg_tables
        self.domain_code = domain_code

        if dataset_details is not None:
            (
                self.dim_columns_w_time,
                self.dim_columns,
                self.time_column,
                self.flag_columns,
            ) = self._get_dim_time_flag_columns()

            # ----------------
            # Get the codelist -> type mapping (e.g. geographicAreaM49 -> area )
            # ----------------
            self.codelist_type_mapping = (
                self.sws_postgres_spark_reader.get_codelist_type_mapping(
                    self.domain_code,
                    dimension_flag_columns=self.dim_columns_w_time + self.flag_columns,
                )
            )

            self.mapping_dim_col_name_type = {
                col_name: col_type
                for col_name, col_type in self.codelist_type_mapping.items()
                if col_name in self.dim_columns
            }

            self.df_mapping_code_correction = (
                self.sws_postgres_spark_reader.get_mapping_code_correction_datatable(
                    self.domain_code
                )
            )

            self.dfs_diss_flags = (
                self.sws_postgres_spark_reader.import_diss_filter_datatables(
                    self.domain_code, self.mapping_dim_col_name_type
                )
            )

            self.df_diss_exception = (
                self.sws_postgres_spark_reader.import_diss_exceptions_datatable(
                    self.domain_code
                )
            )

            get_or_default = lambda l, i, default=None: (
                l[i] if 0 <= i < len(l) else default
            )

            self.mapping_dim_index_name = {
                "dim1_code": get_or_default(self.dim_columns_w_time, 0),
                "dim2_code": get_or_default(self.dim_columns_w_time, 1),
                "dim3_code": get_or_default(self.dim_columns_w_time, 2),
                "dim4_code": get_or_default(self.dim_columns_w_time, 3),
                "dim5_code": get_or_default(self.dim_columns_w_time, 4),
                "dim6_code": get_or_default(self.dim_columns_w_time, 5),
                "dim7_code": get_or_default(self.dim_columns_w_time, 6),
                "status_flag": self.flag_columns[0],
                "method_flag": self.flag_columns[1],
            }

    def initialize_condition_expression(self, df: DataFrame) -> DataFrame:
        # The diss_flag column is needed to initialize the condition expression
        # The note column will contain the eventual reasons why diss_flag has been set to false
        return df.withColumn("diss_flag", lit(True)).withColumn(
            "diss_note", lit([]).cast(ArrayType(StringType()))
        )

    def read_bronze_data(self) -> DataFrame:
        return self.spark.read.option("tag", self.tag_name).table(
            self.iceberg_tables.BRONZE.iceberg_id
        )

    def read_bronze_diss_tag_data(self) -> DataFrame:
        return self.spark.read.option("tag", self.tag_name).table(
            self.iceberg_tables.BRONZE_DISS_TAG.iceberg_id
        )

    def _get_dim_time_flag_columns(self) -> Tuple[List[str], List[str], str, List[str]]:
        """Extract the dimension columns with time, without time, the time column and the flag columns names."""
        dim_columns_w_time = [
            dimension["id"] for dimension in self.dataset_details["dimensions"]
        ]
        time_column = next(
            dimension["id"]
            for dimension in self.dataset_details["dimensions"]
            if dimension["codelist"]["type"] == "time"
        )
        dim_columns = copy(dim_columns_w_time)
        dim_columns.remove(time_column)

        flag_columns = [flag["id"] for flag in self.dataset_details["flags"]]

        return dim_columns_w_time, dim_columns, time_column, flag_columns

    def trim_flag_columns_strings(self, df: DataFrame) -> DataFrame:
        logging.info("Trimming the flag columns strings")

        for flag_column in self.flag_columns:
            df = df.withColumn(flag_column, F.trim(col=flag_column))

        return df

    def fill_observation_status_flag_with_A(self, df: DataFrame):
        logging.info('Replacing null in status_flag with "A"')

        return df.fillna(value="A", subset="flagObservationStatus")

    def replace_observation_status_flag_T_with_X(self, df: DataFrame):
        logging.info('Replacing flagObservationStatus "T" with "X"')

        return df.withColumn(
            "flagObservationStatus",
            F.regexp_replace("flagObservationStatus", lit("T"), lit("X")),
        )

    def _check_time_validity_single(
        self,
        df: DataFrame,
        col_name: str,
        col_type: str,
    ) -> DataFrame:

        logging.info(f"Checking time validity for {col_name} of type {col_type}")

        if col_type == "area":
            logging.info(
                f'Changing start and end year according to "{DatasetDatatables.MAPPING_CODE_CORRECTION.name}"'
            )
            df_start_year_correction = self.df_mapping_code_correction.filter(
                col("var_type") == lit("start_year")
            )
            df_end_year_correction = self.df_mapping_code_correction.filter(
                col("var_type") == lit("end_year")
            )

            original_col_order = df.columns
            cols_to_select = df.columns
            col_name_lower = col_name.lower()
            cols_to_select = [
                column
                for column in cols_to_select
                if column.lower()
                not in (
                    "diss_note",
                    f"{col_name_lower}_start_date",
                    f"{col_name_lower}_end_date",
                )
            ]

            df = (
                df.alias("d")
                .join(
                    F.broadcast(df_start_year_correction).alias("sy"),
                    on=col(f"d.{col_name}") == col("sy.mapping_type"),
                    how="left",
                )
                .join(
                    F.broadcast(df_end_year_correction).alias("ey"),
                    on=col(f"d.{col_name}") == col("ey.mapping_type"),
                    how="left",
                )
                .withColumn("valid_new_start_year", col("sy.new_code").isNotNull())
                .withColumn("valid_new_end_year", col("ey.new_code").isNotNull())
                .withColumn(
                    "new_diss_note",
                    F.when(
                        col("valid_new_start_year"),
                        F.array_append(
                            col("d.diss_note"),
                            F.concat(
                                col("sy.note"),
                                lit(" from "),
                                col("sy.old_code"),
                                lit(" to "),
                                col("sy.new_code"),
                            ),
                        ),
                    ).otherwise(col("d.diss_note")),
                )
                .withColumn(
                    "new_diss_note",
                    F.when(
                        col("valid_new_end_year"),
                        F.array_append(
                            col("new_diss_note"),
                            F.concat(
                                col("ey.note"),
                                lit(" from "),
                                col("ey.old_code"),
                                lit(" to "),
                                col("ey.new_code"),
                            ),
                        ),
                    ).otherwise(col("new_diss_note")),
                )
                .withColumn(
                    f"new_{col_name}_start_date",
                    F.when(
                        col("valid_new_start_year"), F.to_date(col("sy.new_code"))
                    ).otherwise(col(f"d.{col_name}_start_date")),
                )
                .withColumn(
                    f"new_{col_name}_end_date",
                    F.when(
                        col("valid_new_end_year"),
                        F.to_date(F.concat(col("ey.new_code"), lit("-12-31"))),
                    ).otherwise(col(f"d.{col_name}_end_date")),
                )
                .select(
                    *cols_to_select,
                    col("new_diss_note").alias("diss_note"),
                    col(f"new_{col_name}_start_date").alias(f"{col_name}_start_date"),
                    col(f"new_{col_name}_end_date").alias(f"{col_name}_end_date"),
                )
                .select(*original_col_order)
            )

        # Iterate through columns and build conditions dynamically
        start_date_condition = col(f"{col_name}_start_date").isNull() | (
            col(f"{col_name}_start_date") <= col(f"{self.time_column}_start_date")
        )
        end_date_condition = col(f"{col_name}_end_date").isNull() | (
            col(f"{self.time_column}_end_date") <= col((f"{col_name}_end_date"))
        )

        df = (
            df.withColumn(
                "condition_result",
                start_date_condition & end_date_condition,
            )
            .withColumn("diss_flag", col("diss_flag") & col("condition_result"))
            # In case the condition is satisfied update diss_flag accordingly and append a diss_note indicating the reason for the observation exclusion from the dissemination
            .withColumn(
                "diss_note",
                F.when(
                    ~col("condition_result"),
                    F.array_append(
                        col("diss_note"), lit(f"{col_type} out of time validity range")
                    ),
                ).otherwise(col("diss_note")),
            )
            .drop("condition_result")
        )

        return df

    def check_time_validity(self, df: DataFrame) -> DataFrame:
        logging.info("Checking the time validity for each dimension code")

        for col_name, col_type in self.mapping_dim_col_name_type.items():
            if col_type != "other":
                df = self._check_time_validity_single(df, col_name, col_type)

        return df

    def _apply_code_correction_single(
        self,
        df: DataFrame,
        col_name: str,
        col_type: str,
    ) -> DataFrame:
        logging.info(f"Correcting codes for column {col_name} of type {col_type}")

        return map_codes_and_remove_null_duplicates(
            df,
            self.df_mapping_code_correction,
            self.domain_code,
            col_name,
            col_type,
            src_column="old_code",
            dest_column="new_code",
            dimension_columns=[
                column
                for column in self.dim_columns_w_time
                if column not in self.flag_columns
            ],
            flag_columns=self.flag_columns,
        )

    def apply_code_correction(self, df: DataFrame) -> DataFrame:
        logging.info("Applying code correction")

        for col_name, col_type in self.codelist_type_mapping.items():
            df = self._apply_code_correction_single(df, col_name, col_type)

        return df

    def apply_indigenous_mapping(
        self,
        df: DataFrame,
        src_column: str = "old_code",
        dest_column: str = "new_code",
    ) -> DataFrame:

        return (
            df.alias("d")
            .join(
                F.broadcast(
                    self.df_mapping_code_correction.filter(
                        (col("var_type") == lit("element"))
                        & (col("mapping_type") == lit("indigenous"))
                    )
                ).alias("e"),
                col("d.measuredElement") == col(f"e.{src_column}"),
                "left",
            )
            .join(
                F.broadcast(
                    self.df_mapping_code_correction.filter(
                        (col("var_type") == lit("item"))
                        & (col("mapping_type") == lit("indigenous"))
                    )
                ).alias("i"),
                col("d.measuredItemCPC") == col(f"i.{src_column}"),
                "left",
            )
            .select(
                "d.*",
                col(f"e.{dest_column}").alias("indigenous_element"),
                col(f"i.{dest_column}").alias("indigenous_item"),
            )
            .withColumn(
                "measuredElement",
                F.when(
                    col("indigenous_element").isNotNull()
                    & col("indigenous_item").isNotNull(),
                    col("indigenous_element"),
                ).otherwise(col("measuredElement")),
            )
            .withColumn(
                "measuredItemCPC",
                F.when(
                    col("indigenous_element").isNotNull()
                    & col("indigenous_item").isNotNull(),
                    col("indigenous_item"),
                ).otherwise(col("measuredItemCPC")),
            )
            .drop("indigenous_element", "indigenous_item")
        )

    def _check_diss_dim_list(
        self, df: DataFrame, diss_flags_df: DataFrame, col_name: str, col_type: str
    ) -> DataFrame:
        """Filters the observations based on the general rule for a given dimension. If the code is absent the dissemination flag is supposed to be `false`

        Args:
            df (DataFrame): Spark DataFrame containing the observations data
            diss_flags_df (DataFrame): Spark DataFrame containing the dissemination rules for a given dimension
            col_name (str): The DataFrame column name on which to apply the filter

        Returns:
            DataFrame: The DataFrame with updated `diss_flag` and `diss_note` columns based on the check outcome
        """

        # Remove the duplicates that may be in the tables
        diss_flags_df = diss_flags_df.select(
            "domain", "code", "dissemination"
        ).distinct()

        duplicated_values = (
            diss_flags_df.groupBy("code")
            .count()
            .filter(col("count") > 1)
            .select("code")
            .collect()
        )

        if len(duplicated_values) > 0:
            raise RuntimeError(
                f"There are some duplicates in the datatable dissemination_{col_type}_list with discording dissemination flags for the following codes: {str(duplicated_values)}"
            )

        return (
            df.alias("d")
            .join(
                diss_flags_df.alias("f"),
                col(f"d.{col_name}") == col("f.code"),
                "left",
            )
            .withColumn(
                "condition_result",
                col("f.dissemination").isNotNull() & col("f.dissemination"),
            )
            .select("d.*", "condition_result")
            .withColumn(
                "diss_flag",
                col("diss_flag") & col("condition_result"),
            )
            .withColumn(
                "diss_note",
                F.when(
                    ~col("condition_result"),
                    F.array_append(
                        col("diss_note"),
                        lit(f"{col_type} not disseminated for this domain"),
                    ),
                ).otherwise(col("diss_note")),
            )
            .drop("condition_result")
        )

    def check_dissemination_flags(self, df: DataFrame) -> DataFrame:
        logging.info("Checking the dissemination flag for each dimension (except year)")

        for col_name, col_type in self.mapping_dim_col_name_type.items():
            if col_type != "other":
                df = self._check_diss_dim_list(
                    df,
                    self.dfs_diss_flags[col_type],
                    col_name,
                    col_type,
                )

        return df

    def _exception_condition(self, col_name: str, exception: str) -> Column:

        if col_name is None or col_name == "" or exception is None or exception == "":
            return lit(True)

        exception = exception.strip()

        if exception.startswith(">="):
            ge_val = exception.removeprefix(">=").strip()
            return col(col_name) >= lit(ge_val)

        elif exception.startswith("<="):
            le_val = exception.removeprefix("<=").strip()
            return col(col_name) <= lit(le_val)

        elif exception.startswith(">"):
            g_val = exception.removeprefix(">").strip()
            return col(col_name) > lit(g_val)

        elif exception.startswith("<"):
            l_val = exception.removeprefix("<").strip()
            return col(col_name) < lit(l_val)

        elif exception.startswith("!["):
            values = [
                value.strip()
                # Remove initial "![" and final "]"
                for value in exception[2:-1].strip().split(",")
            ]
            return ~col(col_name).isin(values)

        elif "," in exception:
            values = [value.strip() for value in exception.strip().split(",")]
            return col(col_name).isin(values)

        elif exception != "":
            return col(col_name) == lit(exception.strip())

    def check_dissemination_exceptions(
        self,
        df: DataFrame,
    ) -> DataFrame:

        logging.info("Checking the dissemination exceptions")

        diss_exceptions = self.df_diss_exception.collect()

        if len(diss_exceptions) > 0:
            for row_exception in diss_exceptions:
                logging.info(f"Processing exception with note: {row_exception['note']}")

                if row_exception["dissemination"] == False:
                    exception_condition = lit(True)
                    for col_exception, col_name in self.mapping_dim_index_name.items():
                        exception_condition &= self._exception_condition(
                            col_name=col_name, exception=row_exception[col_exception]
                        )

                    df = (
                        df.withColumn(
                            "condition_result",
                            ~exception_condition,
                        )
                        .withColumn(
                            "diss_flag",
                            col("diss_flag") & col("condition_result"),
                        )
                        .withColumn(
                            "diss_note",
                            F.when(
                                ~col("condition_result"),
                                F.array_append(
                                    col("diss_note"),
                                    lit(
                                        f"not disseminated according to exception with note: {row_exception['note']}"
                                    ),
                                ),
                            ).otherwise(col("diss_note")),
                        )
                        .drop("condition_result")
                    )

        return df

    def check_duplicates(
        self, df: DataFrame, partition_columns: List[str] = None
    ) -> DataFrame:
        """
        Removes rows from the DataFrame where the combination of specified dimension columns
        (e.g., 'area', 'element', 'product') is duplicated, and the 'value' column is null.

        This function does not remove rows where the 'value' is null if the combination of
        the specified dimension columns is unique. It only removes rows where:
        - The combination of dimension columns (specified in the `dimensions` argument)
        appears more than once (i.e., duplicates exist).
        - The 'value' column is null.

        Args:
            df (DataFrame): _description_
            dimensions (List[str]): _description_
            df (DataFrame): The input PySpark DataFrame that contains the data.
            dimensions (List[str]): A list of column names representing the dimensions (e.g., ['area', 'element', 'product']) that define the uniqueness of the rows.

        Returns:
            DataFrame: A PySpark DataFrame with rows removed where the combination of the specified dimension columns is duplicated and the 'value' column is null.

        Example:
            Given a DataFrame `df` with the following columns: 'area', 'element', 'product', 'value',
            you can remove null duplicates like so:

                result_df = _remove_null_duplicates(df, ['area', 'element', 'product'])

        Notes:
            - The function first partitions the DataFrame based on the specified dimensions to identify
            duplicates.
            - It counts the occurrences of each combination of dimension columns.
            - Rows where the combination is duplicated and 'value' is null are filtered out.
            - The intermediate 'count' column is dropped from the resulting DataFrame.
        """
        # Step 1: Define a window specification based on area, element, and product
        window_spec = Window.partitionBy(
            *(
                partition_columns
                or [
                    col
                    for col in self.dim_columns_w_time
                    if col not in self.flag_columns
                ]
            )
        )

        # Step 2: Count the occurrences of each combination of dimensions that is disseminated
        df_duplicates = (
            df.filter(col("diss_flag"))
            .withColumn("count", F.count(lit(1)).over(window_spec))
            .filter(col("count") > lit(1))
            .drop("count")
        )
        if df_duplicates.count() > 0:
            df_duplicates.writeTo(
                f"{self.iceberg_tables.SILVER.iceberg_id}_duplicates"
            ).createOrReplace()
            raise RuntimeError(
                f"There are some duplicates in the data that are flagged for dissemination they can be checked in the {self.iceberg_tables.SILVER.iceberg_id}_duplicates table"
            )

        return df

    def write_silver_data_to_iceberg_and_csv(self, df: DataFrame) -> DataFrame:

        df.writeTo(self.iceberg_tables.SILVER.iceberg_id).createOrReplace()

        logging.info(f"silver table written to {self.iceberg_tables.SILVER.iceberg_id}")

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.SILVER.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"silver tag '{self.tag_name}' created")

        df = (
            df.withColumn("metadata", F.to_json(col("metadata")))
            .withColumn("diss_note", F.to_json(col("diss_note")))
            .coalesce(1)
        )

        save_cache_csv(
            df=df,
            bucket=self.bucket,
            prefix=self.iceberg_tables.SILVER.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def write_silver_sws_dissemination_tag(self, df: DataFrame, tags: Tags):
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_silver_iceberg",
            name=f"{self.domain_code} silver Iceberg",
            description="Silver table containing all the data imported from the SWS with additional flags and information",
            layer=TableLayer.SILVER,
            private=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.SILVER_DATABASE,
            table=self.iceberg_tables.SILVER.table,
            path=self.iceberg_tables.SILVER.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
            pinned_columns=[
                *self.dim_columns_w_time,
                "value",
                *self.flag_columns,
                "diss_flag",
                "diss_note",
            ],
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_csv_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_silver_csv",
            name=f"{self.domain_code} silver csv",
            description="Silver table containing all the data imported from the SWS with additional flags and information cached in csv",
            layer=TableLayer.SILVER,
            private=True,
            type=TableType.CSV,
            path=self.iceberg_tables.SILVER.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_csv_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df
