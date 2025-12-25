import csv
from typing import Dict, Optional

import pandas as pd
from pandas import DataFrame as PandasDataFrame

from dump.files.tmp_util import TemporaryFileSystem

from .connectors import ConnectorMySQL


class GetDataManipulatorMySQL(ConnectorMySQL):
    def __init__(
        self,
        encoding="utf-8",
        size: Optional[int] = 8388608,
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
        fetching data from mysql/mariaDB using query
        and saving into csv locating in temporary directory
        """
        if path is None:
            path = self._tmp_file_system.save_path()

        if query not in self.__query_history:
            results = self.fetchall(query, auto_close=False)
            with open(path, "w", encoding=self.encoding) as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(
                    [i[0] for i in self.cursor.description]
                )  # Write headers
                csvwriter.writerows(results)  # Write data

                self.__query_history[query] = self._tmp_file_system._last_path

        path = self.__query_history[query]
        self.close()
        return path

    def get_df(self, query: str) -> PandasDataFrame:
        path = self.get_data(query)
        return pd.read_csv(path, encoding=self.encoding, low_memory=False)
