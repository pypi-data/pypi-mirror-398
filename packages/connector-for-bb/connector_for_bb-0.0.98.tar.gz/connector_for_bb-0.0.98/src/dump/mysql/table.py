import warnings
from typing import Optional

from pandas import DataFrame as PandasDataFrame

from dump.postgres.types_util import cast_df_by_schema

from .connectors import ConnectorMySQL, DBUtilsMySQL
from .manipulators import GetDataManipulatorMySQL


class TableMySQL(ConnectorMySQL):
    def __init__(
        self,
        table_name: str,
        db_schema: Optional[str] = None,
        limit: int = None,
        auto_cast: Optional[bool] = False,
        clear_tech_cols: Optional[bool] = False,
        size: Optional[int] = 8388608,
        db_config_name: str = "maria",
    ) -> None:
        super().__init__(db_config_name=db_config_name)
        self.table_name = table_name
        self.auto_cast = auto_cast
        self._limit = limit

        self.data_manipulator = GetDataManipulatorMySQL(
            size=size,
            db_config_name=self.db_config_name,
        )

        self.db_utils = DBUtilsMySQL(db_config_name=db_config_name)
        self.table_schema = self.db_utils.get_table_structure(
            self.table_name,
        )
        if db_schema:
            warnings.warn("db_schema is not required")

        if clear_tech_cols:
            warnings.warn("clear_tech_cols is not available")

        self._filters_args: set = set()
        self._select_args: set = set()
        self._filter_operation: str = "and"

    def filter(self, *args, operation: str = "and"):
        self._filters_args: set = set(args)
        self._filter_operation = operation
        return self

    @property
    def _filters(self) -> str:
        filters = "WHERE "
        if len(self._filters_args) == 0:
            filters = "WHERE 1=1"

        filters += f" {self._filter_operation} ".join(self._filters_args)
        return filters

    def select(self, *args):
        self._select_args: set = set()
        self._select_args.update(args)
        return self

    @property
    def _select(self) -> str:
        select = "select "
        if len(self._select_args) == 0:
            select += "*"
        select += ", ".join(self._select_args)
        return select

    @property
    def query(self) -> str:
        limit = ""
        if self._limit is not None:
            limit = f"LIMIT {self._limit}"

        query = f"""
            {self._select}
            FROM {self.table_name}
            {self._filters}
            {limit}
        """
        return query

    @property
    def _clear_statments(self):
        self._filters_args: set = set()
        self._select_args: set = set()
        return self

    def get_df(self, query: Optional[str] = None) -> PandasDataFrame:
        if query is None:
            query = self.query
        df = self.data_manipulator.get_df(query)

        if self.auto_cast:
            df = cast_df_by_schema(df, self.table_schema)
        return df

    def count(self) -> PandasDataFrame:
        query = f"""select count(*) as cnt from ({self.query}) s"""
        return self.get_df(query)["cnt"]
