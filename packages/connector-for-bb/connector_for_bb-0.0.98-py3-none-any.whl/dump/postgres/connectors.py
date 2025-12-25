import logging

import psycopg2
from psycopg2 import connect

from dump.config_utils import load_config


TYPE_MAPPER = {
    # Integer types
    "smallint": "Int16",
    "int2": "Int16",
    "integer": "Int32",
    "int": "Int32",
    "int4": "Int32",
    "bigint": "Int64",
    "int8": "Int64",
    "smallserial": "Int16",
    "serial2": "Int16",
    "serial": "Int32",
    "serial4": "Int32",
    "bigserial": "Int64",
    "serial8": "Int64",
    # Float types
    "real": "float32",
    "float4": "float32",
    "double precision": "float64",
    "float8": "float64",
    "decimal": "float64",
    "numeric": "float64",
    # Other types
    "USER-DEFINED": "str",
    "character varying": "str",
    "character": "str",
    "text": "str",
    "boolean": "bool",
    "timestamp without time zone": "timestamp",
    "timestamp": "timestamp",
    "date": "timestamp",
}


class ConnectorPG:
    def __init__(
        self,
        db_config_name: str = "postgres",
    ) -> None:
        self.db_config_name = db_config_name
        self.__config = load_config(section=self.db_config_name)

        self._conn: connect = None
        self._cursor = None

    @property
    def conn(self):
        if self._conn is None:
            try:
                # connecting to the PostgreSQL server
                with psycopg2.connect(**self.__config) as pgconn:
                    # print("Connected to the PostgreSQL server.")
                    self._conn = pgconn
            except (psycopg2.DatabaseError, Exception) as error:
                raise error
        return self._conn

    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = self.conn.cursor()
        return self._cursor

    def close(self):
        try:
            self.conn.close()
            self._conn = None
            self._cursor = None
        except Exception as e:
            logging.info(f"Error while closing connection: {e}")

    @property
    def commit(self):
        self.conn.commit()

    def execute(self, query: str):
        self.cursor.execute(query)
        self.conn.commit()

    def fetchall(self, query: str, auto_close: bool = True) -> list:
        self.execute(query)
        values = self.cursor.fetchall()
        self.conn.commit()

        if auto_close:
            self.cursor.close()
            self.close()
        return values


class DBUtilsPG(ConnectorPG):
    @staticmethod
    def _validate_output(inp: list):
        return [x[0] for x in inp]

    @property
    def _schemas(self) -> list:
        query = """
            SELECT schema_name
            FROM information_schema.schemata;
        """
        data = self._validate_output(self.fetchall(query))
        return data

    def get_tables_in_schema(self, schema: str) -> list:
        query = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
        """
        tables = self._validate_output(self.fetchall(query))
        return tables

    def get_table_structure(self, table_name: str, db_schema: str) -> dict:
        query = f"""
            SELECT column_name, data_type, is_nullable, ordinal_position
            FROM information_schema.columns
            WHERE table_name = '{table_name}' and
            table_schema = '{db_schema}';
        """

        schema = {}
        for column_name, data_type, is_nullable, position in self.fetchall(query):
            orig_data_type = data_type
            if "int" in data_type and data_type not in TYPE_MAPPER.keys():
                data_type = "integer"
            if (
                "numeric" in data_type or "decimal" in data_type
            ) and data_type not in TYPE_MAPPER.keys():
                data_type = "decimal"
            if "time" in data_type:
                data_type = "timestamp"

            schema[column_name] = {
                "data_type": TYPE_MAPPER.get(data_type, "str"),
                "orig_data_type": orig_data_type,
                "is_nullable": is_nullable,
                "position": position,
            }
        return schema

    def get_schema_by_table(self, table_name: str) -> str:
        query = f"""
            SELECT table_schema
            FROM information_schema.tables
            WHERE table_name = '{table_name}';
        """
        schema = self._validate_output(self.fetchall(query))
        return schema[0]

    def get_primary_keys(self, table_name: str, db_schema: str) -> list:
        query = f"""
            select column_name
            from information_schema.key_column_usage
            where table_schema = '{db_schema}'
            and table_name = '{table_name}'
        """
        keys = self._validate_output(self.fetchall(query))
        return keys


class SequenceUtils:
    def __init__(
        self,
        sequence_name: str = "seq_general_job_id",
        sequence_schema: str = "public",
        db_config_name: str = "postgres",
    ) -> None:
        self.sequence_name = sequence_name
        self.sequence_schema = sequence_schema

        self.connector = ConnectorPG(db_config_name)

    @property
    def next_sequence(self):
        query = f"""
            SELECT nextval('{self.sequence_schema}.{self.sequence_name}');
        """
        sequence = self.connector.fetchall(query)[0][0]
        return sequence

    @property
    def current_sequence(self):
        query = f"""
            SELECT last_value FROM {self.sequence_schema}.{self.sequence_name}
        """
        sequence = self.connector.fetchall(query)[0][0]
        return sequence


# class TemporaryTablePG(ConnectorPG):
#     def __init__(self, name: str, db_config_name: str = "postgres") -> None:
#         super().__init__(db_config_name)
#         self.name = name
#         self.data_manipulator = DataManupulationPG(db_config_name=self.db_config_name)

#         # mapping dtypes to PG types
#         self._KIND_MAPPER = {
#             "M": "timestamp",
#             "f": "real",
#             "i": "bigint",
#         }

#     def _pd_types_to_pg_types(self, df: PandasDataFrame) -> dict:
#         df_types = df.dtypes.to_dict()
#         some = {
#             col: self._KIND_MAPPER.get(col_type.kind, "varchar")
#             for col, col_type in df_types.items()
#         }
#         return some

#     def _types_to_str_statments(self, types: dict) -> str:
#         types_statments = ", \n ".join([" ".join(x) for x in types.items()])
#         return types_statments

#     def create_table(self, df: PandasDataFrame):
#         types = self._pd_types_to_pg_types(df)
#         types_statments = self._types_to_str_statments(types)
#         query = f"""
#         CREATE TEMP TABLE {self.name}(
#             {types_statments}
#         );
#         """
#         self.execute(query)
#         self.commit
