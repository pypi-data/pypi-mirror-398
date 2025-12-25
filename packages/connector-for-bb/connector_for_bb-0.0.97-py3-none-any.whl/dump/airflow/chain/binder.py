import os
import time
import psutil

from airflow.stats import Stats
from airflow.operators.python import PythonOperator
from airflow.models.baseoperator import chain

from datetime import datetime, timedelta


def stats_metric(task_id: str, status: str, *args):
    """
        Высчитывает метрики потребления для тасок и публикует в statsD
    """
    p = psutil.Process(os.getpid())
    cpu_times = p.cpu_times()            # user/system CPU seconds
    mem_info  = p.memory_info()          # rss, vms и т.п.
    io_counters = p.io_counters()        # read_bytes, write_bytes и т.п.

    tag_into = {"task_id":task_id, "phase":status, "dag_id":dags_id}

    metric_cpu_times_user = f"airflow_metric_{task_id}_cpu_times_user_{status} ({cpu_times.user})"
    metric_cpu_times_system = f"airflow_metric_{task_id}_cpu_times_system_{status} ({cpu_times.system})"
    metric_mem_info_rss = f"airflow_metric_{task_id}_mem_info_rss_{status} ({mem_info.rss})"
    metric_mem_info_vms = f"airflow_metric_{task_id}_mem_info_vms_{status} ({mem_info.vms})"
    metric_io_counters_read_bytes = f"airflow_metric_{task_id}_io_counters_read_bytes_{status} ({io_counters.read_bytes})"
    metric_io_counters_write_bytes = f"airflow_metric_{task_id}_io_counters_write_bytes_{status} ({io_counters.write_bytes})"


    Stats.gauge(f'metric.{task_id}.cpu_times_user', cpu_times.user, tags=tag_into)
    Stats.gauge(f'metric.{task_id}.cpu_times_system', cpu_times.system, tags=tag_into)
    Stats.gauge(f'metric.{task_id}.mem_info_rss', mem_info.rss, tags=tag_into)
    Stats.gauge(f'metric.{task_id}.mem_info_vms', mem_info.vms, tags=tag_into)
    Stats.gauge(f'metric.{task_id}.io_counters_read_bytes', io_counters.read_bytes, tags=tag_into)
    Stats.gauge(f'metric.{task_id}.io_counters_write_bytes', io_counters.write_bytes, tags=tag_into)

    print(f"""{metric_cpu_times_user}\n
        {metric_cpu_times_system}\n
        {metric_mem_info_rss}\n
        {metric_mem_info_vms}\n
        {metric_io_counters_read_bytes}\n
        {metric_io_counters_write_bytes}""")


def chain_with_intermediates(tasks):
    """
    Вставляет между каждой парой тасок список тасок c метриками.
    Затем разворачивает все в единую цепочку зависимостей.
    [MonitoringOperator_start, BaseOperator, MonitoringOperator_finish] — примерный формат
    """

    chain_list = []
    
    for task in tasks:
 
        pre  = PythonOperator(task_id=f"airflow_monitoring_{task.task_id}_start", 
                              python_callable=stats_metric, 
                              op_args=[task.task_id, 'start'])
        
        post = PythonOperator(task_id=f"airflow_monitoring_{task.task_id}_finish", 
                              python_callable=stats_metric, 
                              op_args=[task.task_id, 'finish'])
        
        chain_list.append(pre)
        chain_list.append(task)
        chain_list.append(post)

    chain(*chain_list)
    print(*chain_list)