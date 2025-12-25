from dagster import DagsterRunStatus, RunsFilter, RunStatusSensorContext


# 检测dagster任务是否运行
def check_dagster_job_running(context: RunStatusSensorContext, job_name: str):
    # 查询最近的运行状态
    runs = context.instance.get_runs(filters=RunsFilter(job_name=job_name), limit=1)

    # STARTING , STARTED 都是运行中
    if runs and runs[0].status in [
        DagsterRunStatus.QUEUED,
        DagsterRunStatus.NOT_STARTED,
        DagsterRunStatus.MANAGED,
        DagsterRunStatus.STARTING,
        DagsterRunStatus.STARTED,
    ]:
        # context.log.info(f"Job {job_name} is already running")
        return False
    return True
