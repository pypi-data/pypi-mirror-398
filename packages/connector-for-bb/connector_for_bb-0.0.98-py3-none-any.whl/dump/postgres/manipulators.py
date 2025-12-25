from typing import Dict, Optional

import pandas as pd
from pandas import DataFrame as PandasDataFrame

from dump.files.tmp_util import TemporaryFileSystem

from .connectors import ConnectorPG, DBUtilsPG


class GetDataManipulatorPG(ConnectorPG):
    def __init__(
        self,
        encoding="utf-8",
        size: int = 8388608,
        db_config_name: str = "postgres",
    ) -> None:
        super().__init__(db_config_name=db_config_name)
        self.encoding = encoding
        self.size = size

        # requires for not execute same query more than one time
        self.__query_history: Dict[str, str] = {}
        self._tmp_file_system = TemporaryFileSystem()

    def clear_query_history(self):
        self.__query_history: Dict[str, str] = {}

    def get_data(self, query: str, path: Optional[str] = None) -> str:
        """
        fetching data from pg using query
        and saving into csv locating in temporary directory
        """
        to_execute = f"""
            copy ( {query} )
            to stdout
            WITH
            CSV HEADER
        """
        if path is None:
            path = self._tmp_file_system.save_path()

        if query not in self.__query_history:
            with open(path, "w", encoding=self.encoding) as fp:
                self.cursor.copy_expert(to_execute, fp, size=self.size)
                self.close()
                self.__query_history[query] = self._tmp_file_system._last_path

        path = self.__query_history[query]
        return path

    def get_df(self, query: str) -> PandasDataFrame:
        path = self.get_data(query)
        return pd.read_csv(path, encoding=self.encoding, low_memory=False)


class SaveDataManipulatorPG(ConnectorPG):
    def __init__(
        self,
        table_name: str,
        db_schema: Optional[str] = None,
        encoding="utf-8",
        size: int = 262144,
        db_config_name: str = "postgres",
    ) -> None:
        super().__init__(db_config_name=db_config_name)
        self.table_name = table_name
        self.db_schema = db_schema
        self.encoding = encoding
        self.size = size

        self._tmp_file_system = TemporaryFileSystem()

        self.db_utils = DBUtilsPG(db_config_name)
        if self.db_schema is None:
            self.db_schema = self.db_utils.get_schema_by_table(self.table_name)

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

    def _validate_df_to_save(self, df) -> PandasDataFrame:
        """
        Check that DataFrame have all required columns
        """
        table_schemа = self.db_utils.get_table_structure(
            self.table_name, self.db_schema
        )
        columns_intersection = set(table_schemа).intersection(df.columns)
        columns_not_found = set(table_schemа) - columns_intersection

        if len(columns_not_found) != 0:
            raise Exception(f"Columns not found: {columns_not_found}")

        column_to_write = self.__get_columns_right_order(table_schemа)
        return df[column_to_write]

    def init_df(self, df: PandasDataFrame) -> str:
        """
        Validate df with pg table and save df as csv into temporary directory
        """
        df = self._validate_df_to_save(df)

        path = self._tmp_file_system.save_path()
        df.to_csv(path, encoding=self.encoding, index=False)
        return path

    def save_data(
        self,
        path: str,
    ):
        """
        reading file from path
        and saving file to self.table_save

        self.table_save: str - PG table where to save data
        path: str - path to file which should be copied into PG

        Using with combination self.init_data
        or set path manualy
        """

        to_execute = f"""
            copy {self.db_schema}.{self.table_name}
            from STDIN
            WITH
            CSV header
        """

        with open(path, "r", encoding=self.encoding) as fp:
            self.cursor.copy_expert(to_execute, fp, size=self.size)
            self.commit
            self.close()

    def save_df(self, df: PandasDataFrame):
        path = self.init_df(df)
        self.save_data(path)
