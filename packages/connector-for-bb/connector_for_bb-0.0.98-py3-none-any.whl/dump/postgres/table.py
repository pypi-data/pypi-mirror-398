import logging
from typing import Optional

import pandas as pd
from pandas import DataFrame as PandasDataFrame

from .connectors import ConnectorPG, DBUtilsPG, SequenceUtils
from .manipulators import GetDataManipulatorPG, SaveDataManipulatorPG
from .types_util import cast_df_by_schema


TECH_COLUMNS = {"_inserted_dttm", "_job_id"}


class TablePG(ConnectorPG):
    def __init__(
        self,
        table_name: str,
        db_schema: Optional[str] = None,
        limit: int = None,
        auto_cast: bool = True,
        clear_tech_cols: bool = True,
        size: int = 8388608,
        db_config_name: str = "postgres",
    ) -> None:
        super().__init__(db_config_name=db_config_name)
        self.table_name = table_name
        self.db_schema = db_schema
        self._limit = limit
        self.auto_cast = auto_cast
        self.clear_tech_cols = clear_tech_cols

        self.data_manipulator = GetDataManipulatorPG(
            size=size,
            db_config_name=self.db_config_name,
        )
        self.db_utils = DBUtilsPG(db_config_name=db_config_name)

        if self.db_schema is None:
            self.db_schema = self.db_utils.get_schema_by_table(self.table_name)

        self.table_schema = self.db_utils.get_table_structure(
            self.table_name,
            self.db_schema,
        )

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
            FROM \"{self.db_schema}\".\"{self.table_name}\"
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

        if self.clear_tech_cols:
            to_drop = TECH_COLUMNS.intersection(df.columns)
            df = df.drop(columns=to_drop)
        return df

    def count(self) -> PandasDataFrame:
        query = f"""select count(*) as cnt from ({self.query}) s"""
        return self.get_df(query)["cnt"]


class JobIDSequence(SequenceUtils):
    def __init__(
        self,
        db_config_name: str = "postgres",
    ):
        super().__init__(
            sequence_name="seq_general_job_id",
            sequence_schema="meta",
            db_config_name=db_config_name,
        )


class SaveTablePG:
    def __init__(
        self,
        table_name: str,
        db_schema: Optional[str] = None,
        insert_dttm_col_name: str = "_inserted_dttm",
        job_id_col_name: str = "_job_id",
        auto_cast: bool = True,
        size: int = 8388608,
        db_config_name: str = "postgres",
        sequence_util: SequenceUtils = JobIDSequence,
    ) -> None:
        self.table_name = table_name
        self.db_schema = db_schema
        self.insert_dttm_col_name = insert_dttm_col_name
        self.job_id_col_name = job_id_col_name
        self.auto_cast = auto_cast
        self.db_config_name = db_config_name

        self.data_manipulator = SaveDataManipulatorPG(
            size=size,
            table_name=table_name,
            db_schema=db_schema,
            db_config_name=self.db_config_name,
        )

        self.table_schemа = self.data_manipulator.db_utils.get_table_structure(
            self.table_name, db_schema=self.db_schema
        )

        self.sequence_utils = sequence_util(db_config_name=self.db_config_name)

        self._insert_dttm = pd.Timestamp.now()
        self._job_id = None
        self._metadata = {}
        self._df_shape = None

    def _create_tech_cols(self, df: PandasDataFrame) -> PandasDataFrame:
        df[self.insert_dttm_col_name] = self._insert_dttm

        if self.job_id_col_name in self.table_schemа.keys():
            self._job_id = self.sequence_utils.next_sequence
            df[self.job_id_col_name] = self._job_id
            logging.info(f"current sequence in that job: {self._job_id}")

        if self.auto_cast:
            df = cast_df_by_schema(df, self.table_schemа, cast_timestamp=False)

        self._df_shape = df.shape
        return df

    @property
    def metadata(self):
        return {
            "table_name": self.table_name,
            "db_schema": self.db_schema,
            "job_id": self._job_id,
            "df_shape": self._df_shape,
        }

    def save(self, df: PandasDataFrame) -> int:
        df = self._create_tech_cols(df)
        logging.info(f"Saving df with shape: {df.shape}")
        self.data_manipulator.save_df(df)
        return self._job_id
