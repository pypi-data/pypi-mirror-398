from abc import abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pendulum
from airflow.models import BaseOperator
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.context import Context


class AirflowBaseSensor(BaseSensorOperator):
    def __init__(self, **kwargs):
        super().__init__(mode="reschedule", **kwargs)
        # only for info purpose
        self._dag_id: str = None

    def __init_context(self, context: Context):
        self._dag_id = context["dag"].dag_id
        self.execution_date = context["execution_date"]
        self.execution_date_moscow_tz = self.execution_date.astimezone(
            pendulum.timezone("Europe/Moscow")
        )
        self.execution_date_moscow = (
            self.execution_date + self.execution_date_moscow_tz.utcoffset()
        )
        self.task_instance = context["task_instance"]

    def _poke(self) -> Any:
        raise NotImplementedError

    def poke(self, context):
        self.__init_context(context)
        output = self._poke()
        self.task_instance.xcom_push(key="sensor_data", value=output)
        return output


class AirflowBaseOperator(BaseOperator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor_metadata: Any = None
        # only for info purpose
        self._dag_id: str = None

    def __init_context(self, context: Context):
        self._dag_id = context["dag"].dag_id
        self.execution_date = context["execution_date"]
        self.execution_date_moscow_tz = self.execution_date.astimezone(
            pendulum.timezone("Europe/Moscow")
        )
        self.execution_date_moscow = (
            self.execution_date + self.execution_date_moscow_tz.utcoffset()
        )

        self.task_instance = context["task_instance"]
        self.upstream_metadata = {}
        for task_id in self.upstream_task_ids:
            self.upstream_metadata[task_id] = self.task_instance.xcom_pull(
                task_ids=task_id, key="task_data"
            )
            self.sensor_metadata = self.task_instance.xcom_pull(
                task_ids=task_id, key="sensor_data"
            )

    @abstractmethod
    def _execute(self) -> Any:
        raise NotImplementedError

    def execute(self, context: Context) -> Any:
        self.__init_context(context)
        data = self._execute()
        self.task_instance.xcom_push(key="task_data", value=data)

        return data
