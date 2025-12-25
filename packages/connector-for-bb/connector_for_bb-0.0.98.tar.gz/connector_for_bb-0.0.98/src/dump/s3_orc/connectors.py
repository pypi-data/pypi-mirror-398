import logging
import os
import warnings
from typing import Dict, Optional

import pyarrow as pa
import pyarrow.orc as orc
from pandas import DataFrame as PandasDataFrame

from dump.files.tmp_util import TemporaryFileSystem
from dump.postgres.types_util import cast_df_by_schema
from dump.s3.connectors import S3Upload


TABLE_SCHEMA_TO_ORC_MAPPER = {
    # Integer types
    "Int8": pa.int8(),
    "Int16": pa.int16(),
    "Int32": pa.int32(),
    "Int64": pa.int64(),
    # "UInt8": pa.uint8(),
    # "UInt16": pa.uint16(),
    # "UInt32": pa.uint32(),
    # "UInt64": pa.uint64(),
    # Float types
    "float16": pa.float16(),
    "float32": pa.float32(),
    "float64": pa.float64(),
    "float": pa.float64(),
    # Text types
    "str": pa.string(),
    "string": pa.string(),
    "object": pa.string(),
    # Boolean
    "bool": pa.bool_(),
    "boolean": pa.bool_(),
    # Temporal types
    "timestamp": pa.timestamp("ns", tz="+00:00"),
    # "timestamp": pa.timestamp('ns'),
    # "timestamp[ns]": pa.timestamp('ns'),
    # "timestamp[us]": pa.timestamp('us'),
    # "datetime64[ns]": pa.timestamp('ns'),
    # "date": pa.date32(),
    # "timedelta": pa.duration('ns'),
}


class S3UploadDFORC(S3Upload):
    def __init__(
        self,
        bucket_name,
        object_folder="",
        compession_engine: str = "ZLIB",
        compression_strategy: str = "COMPRESSION",
        creds_section="test",
    ):
        super().__init__(bucket_name, object_folder, creds_section)
        self.compession_engine = compession_engine
        self.compression_strategy = compression_strategy

        # for backward compatibility
        self.df_compression_format = "orc"
        self._tmp_file_system = TemporaryFileSystem(file_format="orc")

    @staticmethod
    def __get_columns_right_order(table_schema: Dict[str, str]) -> list:
        """
        Return list of columns sorted by order in destination table
        """
        column_positions = {
            column: meta_info["position"] for column, meta_info in table_schema.items()
        }
        columns_sorted_by_position = sorted(column_positions, key=column_positions.get)
        return columns_sorted_by_position

    def cast_df_by_schema(
        self, df: PandasDataFrame, table_schema: Dict[str, Dict[str, str]]
    ) -> pa.Table:
        df_cols = set(df.columns)
        schema_cols = set(table_schema)
        for del_col in schema_cols - df_cols:
            logging.info(
                f"removing column {del_col} from table_schema, cause its undefiend in df."
            )
            table_schema.pop(del_col)
        df = cast_df_by_schema(df, table_schema, cast_timestamp=True)

        arrow_schema = {}
        for col, setings in table_schema.items():
            arrow_schema[col] = TABLE_SCHEMA_TO_ORC_MAPPER.get(
                setings["data_type"], pa.string()
            )
        arrow_schema = pa.schema(arrow_schema.items())
        df_arrow = pa.Table.from_pandas(df, schema=arrow_schema)

        columns_right_order = self.__get_columns_right_order(table_schema)
        df_arrow = df_arrow.select(columns_right_order)
        return df_arrow

    def upload_to_s3_df(
        self,
        df: PandasDataFrame,
        file_name: str,
        table_schema: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> PandasDataFrame:
        if table_schema:
            df_arrow = self.cast_df_by_schema(df, table_schema)
        else:
            df_arrow = pa.Table.from_pandas(df)

        save_path = self._tmp_file_system.save_path()
        orc.write_table(
            df_arrow,
            save_path,
            compression=self.compession_engine,
            compression_strategy=self.compression_strategy,
        )
        logging.info(f"orc DF meta: {df_arrow}")
        logging.info(f"uploading to s3, object folder: {self.object_folder}")
        logging.info(f"uploading to s3, filename: {file_name}")
        self.upload_to_s3(save_path, file_name)
