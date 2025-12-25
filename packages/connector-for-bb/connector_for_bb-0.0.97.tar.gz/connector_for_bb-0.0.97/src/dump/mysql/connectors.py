import logging

import pymysql

from dump.config_utils import load_config


TYPE_MAPPER = {
    # Integer types
    "tinyint": "Int16",
    "smallint": "Int32",
    "mediumint": "Int32",
    "int": "Int64",
    "integer": "Int64",
    "bigint": "Int64",
    # Float types
    "float": "float32",
    "real": "float64",
    "double": "float64",
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


class ConnectorMySQL:
    def __init__(
        self,
        db_config_name: str = "postgres",
    ) -> None:
        self.db_config_name = db_config_name

        self.__config = load_config(section=self.db_config_name)
        self.__config["port"] = int(self.__config["port"])

        self._conn = None
        self._cursor = None

    @property
    def conn(self):
        if self._conn is None:
            try:
                self._conn = pymysql.connect(
                    **self.__config, ssl={"check_hostname": False}
                )
            except pymysql.Error as error:
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


class DBUtilsMySQL(ConnectorMySQL):
    @staticmethod
    def _validate_output(inp: list):
        return [x[0] for x in inp]

    def get_table_structure(self, table_name: str) -> dict:
        query = f"""
            SELECT column_name, data_type, is_nullable, ordinal_position
            FROM information_schema.columns
            WHERE table_name = '{table_name}';
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
