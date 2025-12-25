   
from dagster import DagsterRunStatus, RunsFilter


def dagster_job_check(context, job_name, jobs_number=1):
     # 检查是否有正在运行的相同job
    instance = context.instance
    runs = instance.get_runs(filters=RunsFilter(job_name=job_name, statuses=[DagsterRunStatus.STARTED, DagsterRunStatus.QUEUED]))
    # 过滤出当前job且状态是STARTED的运行
    active_runs = [run for run in runs if run.job_name == job_name and run.status == DagsterRunStatus.STARTED]
    if len(active_runs) > jobs_number:
        # 有正在运行的实例，跳过此次执行
        context.log.info(f'【正在运行:{job_name}.当前任务列表】{str(active_runs)}')
        return False
    context.log.info(f'【当前任务名称】{str(job_name)}')
    return True

def dagster_sensor_check(context, job_name, jobs_number=1):
     # 检查是否有正在运行的相同job
    instance = context.instance
    runs = instance.get_runs(filters=RunsFilter(job_name=job_name, statuses=[DagsterRunStatus.STARTED, DagsterRunStatus.STARTING, DagsterRunStatus.QUEUED]))
    # 过滤出当前job且状态是STARTED的运行
    active_runs = [run for run in runs if run.job_name == job_name]
    if len(active_runs) > jobs_number:
        # 有正在运行的实例，跳过此次执行
        context.log.info(f'【正在运行:{job_name}.当前任务列表】{str(active_runs)}')
        return False
    context.log.info(f'【当前任务名称】{str(job_name)}')
    return True