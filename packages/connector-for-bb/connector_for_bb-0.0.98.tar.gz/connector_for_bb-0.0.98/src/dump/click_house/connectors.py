from typing import Any, Dict

import clickhouse_connect
from pandas import DataFrame as PandasDataFrame

from dump.config_utils import load_config
from dump.postgres.types_util import cast_df_by_schema


CH_TO_PYTHON_TYPE_MAPPER = {
    # Boolean
    "bool": "bool",
    "nullable(bool)": "bool",
    # Integers (signed)
    "int8": "Int8",
    "int16": "Int16",
    "int32": "Int32",
    "nt64": "Int64",
    # Integers (unsigned)
    "uint8": "Int8",
    "uint16": "Int16",
    "uint32": "Int32",
    "uint64": "Int64",
    # Floating point
    "float32": "float32",
    "float64": "float64",
    # Temporal
    "timestamp": "timestamp",
    "date": "timestamp",
    "dateTime": "timestamp",
    # Strings
    "string": "str",
}


class ConnectorCH:
    def __init__(
        self,
        db_config_name: str = "click_house",
    ) -> None:
        self.db_config_name = db_config_name
        self.__config = load_config(section=self.db_config_name)

        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = clickhouse_connect.get_client(**self.__config)
                # print("Connected to the ClickHouse server.")
            except Exception as error:
                print(error)
        return self._client


class TableCH(ConnectorCH):
    def __init__(
        self, db_config_name: str = "clickhouse_clickhouse_db_prod_onlinebb_ru"
    ) -> None:
        super().__init__(db_config_name)
        self._db_util = DBUtilsCH(db_config_name=db_config_name)

    def prep_to_save(
        self,
        df: PandasDataFrame,
        database: str,
        table_name: str,
    ) -> PandasDataFrame:
        table_schema = self._db_util.get_table_structure(table_name, database=database)
        df = cast_df_by_schema(df, table_schema, cast_timestamp=True)
        return df

    def get_df(self, query: str) -> PandasDataFrame:
        return self.client.query_df(query)


class DBUtilsCH(ConnectorCH):
    @staticmethod
    def _validate_output(inp: list):
        return [x[0] for x in inp]

    def get_table_structure(
        self, table_name: str, database: str = "default"
    ) -> Dict[str, Any]:
        query = f"""
            SELECT name, type, position
            FROM system.columns
            WHERE table = '{table_name}' AND database = '{database}'
        """

        schema = {}
        result = self.client.query(query)
        for column_name, data_type, position in result.result_rows:
            data_type = data_type.lower()
            orig_data_type = data_type
            if "int" in data_type and data_type not in CH_TO_PYTHON_TYPE_MAPPER.keys():
                data_type = "integer"
            if (
                "numeric" in data_type or "decimal" in data_type
            ) and data_type not in CH_TO_PYTHON_TYPE_MAPPER.keys():
                data_type = "decimal"
            if "time" in data_type:
                data_type = "timestamp"

            schema[column_name] = {
                "data_type": CH_TO_PYTHON_TYPE_MAPPER.get(data_type, "str"),
                "orig_data_type": orig_data_type,
                "is_nullable": False,
                "position": position,
            }
        return schema
