import logging
from copy import copy
from typing import List, Tuple

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit
from sws_api_client import Tags
from sws_api_client.tags import BaseDisseminatedTagTable, TableLayer, TableType

from .constants import IcebergDatabases, IcebergTables, DatasetDatatables
from .SWSPostgresSparkReader import SWSPostgresSparkReader
from .utils import get_or_create_tag, save_cache_csv, upsert_disseminated_table


class SWSGoldIcebergSparkHelper:
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

            self.cols_to_keep_sws = (
                self.dim_columns_w_time + ["value"] + self.flag_columns
            )

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

            self.display_decimals = (
                self.sws_postgres_spark_reader.get_display_decimals_datatable(
                    domain_code=domain_code
                )
            )

    def _get_dim_time_flag_columns(self) -> Tuple[List[str], List[str], str, List[str]]:
        """Extract the dimension columns with time, without time, the time column and the flag columns names."""
        dim_columns_w_time = [
            dimension["id"] for dimension in self.dataset_details.get("dimensions", [])
        ]
        time_column = next(
            dimension["id"]
            for dimension in self.dataset_details.get("dimensions", [])
            if dimension["codelist"]["type"] == "time"
        )
        dim_columns = copy(dim_columns_w_time)
        dim_columns.remove(time_column)

        flag_columns = [flag["id"] for flag in self.dataset_details.get("flags", [])]

        return dim_columns_w_time, dim_columns, time_column, flag_columns

    def apply_diss_flag_filter(self, df: DataFrame) -> DataFrame:
        return df.filter(col("diss_flag"))

    def keep_dim_val_attr_columns(
        self, df: DataFrame, additional_columns: List[str] = []
    ):
        cols_to_keep_sws = self.cols_to_keep_sws
        for additional_column in additional_columns:
            if additional_column in df.columns:
                cols_to_keep_sws = cols_to_keep_sws + [additional_column]
        if "unit_of_measure_symbol" in df.columns:
            cols_to_keep_sws = cols_to_keep_sws + ["unit_of_measure_symbol"]
        return df.select(*cols_to_keep_sws)

    def round_to_display_decimals(self, df: DataFrame):
        col1_name, col2_name = (
            self.display_decimals.select("column_1_name", "column_2_name")
            .distinct()
            .collect()[0]
        )
        if col1_name.lower() not in [column.lower() for column in df.columns]:
            raise ValueError(
                f"{col1_name} is not part of the columns available for this dataset ({df.columns})"
            )
        if col2_name.lower() not in [column.lower() for column in df.columns]:
            raise ValueError(
                f"{col2_name} is not part of the columns available for this dataset ({df.columns})"
            )

        df = (
            df.alias("d")
            .join(
                self.display_decimals.alias("dd"),
                on=(col(f"d.{col1_name}") == col("dd.column_1_value"))
                & (col(f"d.{col2_name}") == col("dd.column_2_value")),
                how="left",
            )
            .select("d.*", "dd.display_decimals")
        )

        df.filter(col("display_decimals").isNull()).select(
            col1_name, col2_name
        ).distinct()
        logging.warning(
            f"The following combinations of {col1_name} and {col2_name} are not available in the table {DatasetDatatables.DISPLAY_DECIMALS.name} and will be assigned to 0"
        )

        df = df.withColumn(
            "display_decimals",
            F.coalesce(col("display_decimals"), lit("0")).cast("INT"),
        ).withColumn(
            "value",
            F.round(
                F.col("value").cast("FLOAT") * F.pow(10, F.col("display_decimals")), 0
            )
            / F.pow(10, F.col("display_decimals")).cast("STRING"),
        )

        # F.round(
        #     col("value").cast("FLOAT"), col("display_decimals").cast("INT")
        # ).cast("STRING"),

        return df

    def read_bronze_data(self) -> DataFrame:
        return self.spark.read.option("tag", self.tag_name).table(
            self.iceberg_tables.BRONZE_DISS_TAG.iceberg_id
        )

    def read_silver_data(self) -> DataFrame:
        return self.spark.read.option("tag", self.tag_name).table(
            self.iceberg_tables.SILVER.iceberg_id
        )

    def gen_gold_sws_disseminated_data(
        self, additional_columns: List[str] = []
    ) -> DataFrame:
        return (
            self.read_silver_data()
            .transform(self.apply_diss_flag_filter)
            .transform(self.keep_dim_val_attr_columns, additional_columns)
        )

    def gen_gold_sws_data(self, additional_columns: List[str] = []) -> DataFrame:
        return self.read_bronze_data().transform(
            self.keep_dim_val_attr_columns, additional_columns
        )

    def gen_gold_sws_validated_data(
        self, additional_columns: List[str] = []
    ) -> DataFrame:
        return self.read_silver_data().transform(
            self.keep_dim_val_attr_columns, additional_columns
        )

    def write_gold_sws_validated_data_to_iceberg_and_csv(
        self, df: DataFrame
    ) -> DataFrame:
        df.writeTo(self.iceberg_tables.GOLD_SWS_VALIDATED.iceberg_id).createOrReplace()

        logging.info(
            f"Gold SWS validated table written to {self.iceberg_tables.GOLD_SWS_VALIDATED.iceberg_id}"
        )

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.GOLD_SWS_VALIDATED.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"gold SWS validated tag '{self.tag_name}' created")

        df_1 = df.coalesce(1)

        save_cache_csv(
            df=df_1,
            bucket=self.bucket,
            prefix=self.iceberg_tables.GOLD_SWS_VALIDATED.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def write_gold_sws_data_to_iceberg_and_csv(self, df: DataFrame) -> DataFrame:
        df.writeTo(self.iceberg_tables.GOLD_SWS.iceberg_id).createOrReplace()

        logging.info(
            f"Gold SWS table written to {self.iceberg_tables.GOLD_SWS.iceberg_id}"
        )

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.GOLD_SWS.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"gold SWS tag '{self.tag_name}' created")

        df_1 = df.coalesce(1)

        save_cache_csv(
            df=df_1,
            bucket=self.bucket,
            prefix=self.iceberg_tables.GOLD_SWS.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def gen_and_write_gold_sws_data_to_iceberg_and_csv(self) -> DataFrame:
        self.df_gold_sws = self.gen_gold_sws_data()

        self.write_gold_sws_data_to_iceberg_and_csv(self.df_gold_sws)

        return self.df_gold_sws

    def gen_and_write_gold_sws_validated_data_to_iceberg_and_csv(self) -> DataFrame:
        self.df_gold_sws_validated = self.gen_gold_sws_validated_data()

        self.write_gold_sws_validated_data_to_iceberg_and_csv(
            self.df_gold_sws_validated
        )

        return self.df_gold_sws_validated

    def write_gold_sws_disseminated_data_to_iceberg_and_csv(
        self, df: DataFrame
    ) -> DataFrame:
        df.writeTo(
            self.iceberg_tables.GOLD_SWS_DISSEMINATED.iceberg_id
        ).createOrReplace()

        logging.info(
            f"Gold SWS disseminated table written to {self.iceberg_tables.GOLD_SWS_DISSEMINATED.iceberg_id}"
        )

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.GOLD_SWS_DISSEMINATED.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"gold SWS disseminated tag '{self.tag_name}' created")

        df_1 = df.coalesce(1)

        save_cache_csv(
            df=df_1,
            bucket=self.bucket,
            prefix=self.iceberg_tables.GOLD_SWS_DISSEMINATED.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def gen_and_write_gold_sws_disseminated_data_to_iceberg_and_csv(self) -> DataFrame:
        self.df_gold_sws_disseminated = self.gen_gold_sws_disseminated_data()

        self.write_gold_sws_disseminated_data_to_iceberg_and_csv(
            self.df_gold_sws_disseminated
        )

        return self.df_gold_sws_disseminated

    def write_gold_sdmx_data_to_iceberg_and_csv(self, df: DataFrame) -> DataFrame:
        df.writeTo(self.iceberg_tables.GOLD_SDMX.iceberg_id).createOrReplace()

        logging.info(
            f"Gold SDMX table written to {self.iceberg_tables.GOLD_SDMX.iceberg_id}"
        )

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.GOLD_SDMX.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"gold SDMX tag '{self.tag_name}' created")

        df_1 = df.coalesce(1)

        save_cache_csv(
            df=df_1,
            bucket=self.bucket,
            prefix=self.iceberg_tables.GOLD_SDMX.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def write_gold_pre_sdmx_data_to_iceberg_and_csv(self, df: DataFrame) -> DataFrame:
        """The expected input to this function is the output of the sws disseminated function"""
        for column in self.dim_columns:
            df = df.withColumn(
                column, F.regexp_replace(col(column), lit("\."), lit("_"))
            )
        df = df.withColumnRenamed("value", "OBS_VALUE").withColumnsRenamed(
            {column: column.upper() for column in df.columns}
        )
        df.writeTo(self.iceberg_tables.GOLD_PRE_SDMX.iceberg_id).createOrReplace()

        logging.info(
            f"Gold pre-SDMX table written to {self.iceberg_tables.GOLD_PRE_SDMX.iceberg_id}"
        )

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.GOLD_PRE_SDMX.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"gold pre-SDMX tag '{self.tag_name}' created")

        df_1 = df.coalesce(1)

        save_cache_csv(
            df=df_1,
            bucket=self.bucket,
            prefix=self.iceberg_tables.GOLD_PRE_SDMX.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def write_gold_faostat_data_to_iceberg_and_csv(self, df: DataFrame) -> DataFrame:
        """The expected input to this function is the output of the sws disseminated function"""
        df.writeTo(self.iceberg_tables.GOLD_FAOSTAT.iceberg_id).createOrReplace()

        logging.info(
            f"Gold FAOSTAT table written to {self.iceberg_tables.GOLD_FAOSTAT.iceberg_id}"
        )

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.GOLD_FAOSTAT.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"gold FAOSTAT tag '{self.tag_name}' created")

        df_1 = df.coalesce(1)

        save_cache_csv(
            df=df_1,
            bucket=self.bucket,
            prefix=self.iceberg_tables.GOLD_FAOSTAT.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def write_gold_faostat_unfiltered_data_to_iceberg_and_csv(
        self, df: DataFrame
    ) -> DataFrame:
        """The expected input to this function is the output of the sws disseminated function"""
        df.writeTo(
            self.iceberg_tables.GOLD_FAOSTAT_UNFILTERED.iceberg_id
        ).createOrReplace()

        logging.info(
            f"Gold FAOSTAT unfiltered table written to {self.iceberg_tables.GOLD_FAOSTAT.iceberg_id}"
        )

        self.spark.sql(
            f"ALTER TABLE {self.iceberg_tables.GOLD_FAOSTAT_UNFILTERED.iceberg_id} CREATE OR REPLACE TAG `{self.tag_name}`"
        )

        logging.info(f"gold FAOSTAT unfiltered tag '{self.tag_name}' created")

        df_1 = df.coalesce(1)

        save_cache_csv(
            df=df_1,
            bucket=self.bucket,
            prefix=self.iceberg_tables.GOLD_FAOSTAT_UNFILTERED.csv_prefix,
            tag_name=self.tag_name,
        )

        return df

    def write_gold_sws_validated_sws_dissemination_tag(
        self, df: DataFrame, tags: Tags
    ) -> DataFrame:
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sws_validated_iceberg",
            name=f"{self.domain_code} gold SWS validated Iceberg",
            description="Gold table containing all the unfiltered tag data, with code correction appplied, in SWS compatible format",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.GOLD_DATABASE,
            table=self.iceberg_tables.GOLD_SWS_VALIDATED.table,
            path=self.iceberg_tables.GOLD_SWS_VALIDATED.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_diss_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sws_validated_csv",
            name=f"{self.domain_code} gold SWS validated csv",
            description="Gold table containing all the unfiltered tag data, with code correction appplied, in SWS compatible format, cached in csv",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.CSV,
            path=self.iceberg_tables.GOLD_SWS_VALIDATED.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_diss_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df

    def write_gold_sws_disseminated_sws_dissemination_tag(
        self, df: DataFrame, tags: Tags
    ) -> DataFrame:
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sws_disseminated_iceberg",
            name=f"{self.domain_code} gold SWS disseminated Iceberg",
            description="Gold table containing only the filtered tag data, with code correction appplied, in SWS compatible format",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.GOLD_DATABASE,
            table=self.iceberg_tables.GOLD_SWS_DISSEMINATED.table,
            path=self.iceberg_tables.GOLD_SWS_DISSEMINATED.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_diss_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sws_disseminated_csv",
            name=f"{self.domain_code} gold SWS disseminated csv",
            description="Gold table containing only the filtered tag data, with code correction appplied, in SWS compatible format, cached in csv",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.CSV,
            path=self.iceberg_tables.GOLD_SWS_DISSEMINATED.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_diss_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df

    def write_gold_sdmx_sws_dissemination_tag(
        self, df: DataFrame, tags: Tags
    ) -> DataFrame:
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sdmx_iceberg",
            name=f"{self.domain_code} gold SDMX Iceberg",
            description="Gold table containing all the cleaned data in SDMX compatible format",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.GOLD_DATABASE,
            table=self.iceberg_tables.GOLD_SDMX.table,
            path=self.iceberg_tables.GOLD_SDMX.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_diss_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sdmx_csv",
            name=f"{self.domain_code} gold SDMX csv",
            description="Gold table containing all the cleaned data in SDMX compatible format cached in csv",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.CSV,
            path=self.iceberg_tables.GOLD_SDMX.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_diss_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df

    def write_gold_pre_sdmx_sws_dissemination_tag(
        self, df: DataFrame, tags: Tags
    ) -> DataFrame:
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_pre_sdmx_iceberg",
            name=f"{self.domain_code} gold pre-SDMX Iceberg",
            description="Gold table containing all the cleaned data in SDMX compatible format, ready to be mapped using FMR",
            layer=TableLayer.GOLD,
            private=True,
            debug=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.GOLD_DATABASE,
            table=self.iceberg_tables.GOLD_PRE_SDMX.table,
            path=self.iceberg_tables.GOLD_PRE_SDMX.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_diss_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_pre_sdmx_csv",
            name=f"{self.domain_code} gold pre-SDMX csv",
            description="Gold table containing all the cleaned data in SDMX compatible format, ready to be mapped using FMR and cached in csv",
            layer=TableLayer.GOLD,
            private=True,
            debug=True,
            type=TableType.CSV,
            path=self.iceberg_tables.GOLD_PRE_SDMX.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_diss_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df

    def write_gold_sws_dissemination_tag(self, df: DataFrame, tags: Tags) -> DataFrame:
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sws_iceberg",
            name=f"{self.domain_code} gold SWS Iceberg",
            description="Gold table containing the tag data without any processing",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.GOLD_DATABASE,
            table=self.iceberg_tables.GOLD_SWS.table,
            path=self.iceberg_tables.GOLD_SWS.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_diss_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_sws_csv",
            name=f"{self.domain_code} gold SWS csv",
            description="Gold table containing the tag data without any processing cached in csv",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.CSV,
            path=self.iceberg_tables.GOLD_SWS.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_diss_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df

    def write_gold_faostat_dissemination_tag(
        self, df: DataFrame, tags: Tags
    ) -> DataFrame:
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_faostat_iceberg",
            name=f"{self.domain_code} gold FAOSTAT Iceberg",
            description="Gold table containing the tag data in FAOSTAT format",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.GOLD_DATABASE,
            table=self.iceberg_tables.GOLD_FAOSTAT.table,
            path=self.iceberg_tables.GOLD_FAOSTAT.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_diss_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_faostat_csv",
            name=f"{self.domain_code} gold FAOSTAT csv",
            description="Gold table containing the tag data in FAOSTAT format in csv",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.CSV,
            path=self.iceberg_tables.GOLD_FAOSTAT.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_diss_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df

    def write_gold_faostat_unfiltered_dissemination_tag(
        self, df: DataFrame, tags: Tags
    ) -> DataFrame:
        # Get or create a new tag
        tag = get_or_create_tag(tags, self.dataset_id, self.tag_name, self.tag_name)
        logging.debug(f"Tag: {tag}")

        new_iceberg_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_faostat_unfiltered_iceberg",
            name=f"{self.domain_code} gold FAOSTAT unfiltered Iceberg",
            description="Gold table containing all the tag data in FAOSTAT format",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.ICEBERG,
            database=IcebergDatabases.GOLD_DATABASE,
            table=self.iceberg_tables.GOLD_FAOSTAT_UNFILTERED.table,
            path=self.iceberg_tables.GOLD_FAOSTAT_UNFILTERED.path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_iceberg_table,
        )
        logging.debug(f"Tag with Added Iceberg Table: {tag}")

        new_diss_table = BaseDisseminatedTagTable(
            id=f"{self.domain_code.lower()}_gold_faostat_unfiltered_csv",
            name=f"{self.domain_code} gold FAOSTAT unfiltered csv",
            description="Gold table containing the tag data in FAOSTAT format in csv",
            layer=TableLayer.GOLD,
            private=True,
            type=TableType.CSV,
            path=self.iceberg_tables.GOLD_FAOSTAT_UNFILTERED.csv_path,
            structure={"columns": df.schema.jsonValue()["fields"]},
        )
        tag = upsert_disseminated_table(
            sws_tags=tags,
            tag=tag,
            dataset_id=self.dataset_id,
            tag_name=self.tag_name,
            table=new_diss_table,
        )
        logging.debug(f"Tag with Added csv Table: {tag}")

        return df
