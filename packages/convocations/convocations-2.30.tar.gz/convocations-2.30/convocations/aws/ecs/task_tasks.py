import posixpath
import time

from raft.tasks import task
from convocations.aws.base import AwsTask
from convocations.base.utils import print_table, notice, notice_end


def get_task_arns(session, cluster, service, client=None):
    from ..base import yielder
    client = client or session.client('ecs')
    kwargs = {
        'cluster': cluster,
        'serviceName': service,
    }
    tasks = yielder(client, 'list_tasks', **kwargs)
    return list(tasks)


def get_tasks(session, cluster, service, client=None):
    client = client or session.client('ecs')
    arns = get_task_arns(session, cluster, service, client)
    response = client.describe_tasks(
        cluster=cluster,
        tasks=arns,
    )
    return response['tasks']


@task(klass=AwsTask, help={
    'cluster': 'the name of the cluster',
    'service': 'the name of the service',
})
def list_tasks(ctx, cluster, service, session=None, **kwargs):
    """
    lists tasks for a given ecs service in a specified cluster.

    will show a table with the following values;
      * the task id
      * the status of the task (e.g., RUNNING, PENDING, STOPPED)
      * the name of the container as specified in the task definition
      * the image being used by the container (in short form)
    """
    ecs = session.client('ecs')
    notice('getting tasks')
    tasks = get_tasks(session, cluster, service, ecs)
    notice_end(f'{len(tasks)}')
    if not tasks:
        return
    header = [ 'id', 'status', 'name', 'image', ]
    rows = []
    for x in tasks:
        containers = x['containers']
        for container in containers:
            row = [
                container['taskArn'].rsplit('/', 1)[-1],
                container['lastStatus'].lower(),
                container['name'],
                container['image'].split('/', 1)[-1],
            ]
            rows.append(row)
    print_table(header, rows)


def ecs_log_stream(cluster_name: str, task_id: str, session, container_name: str = None):
    """
    Returns (log_group, log_stream, aws_region) for the given ECS task.
    Assumes the task definition is using the awslogs driver.
    """
    ecs = session.client('ecs')

    # 1) Describe the running (or stopped) task to get its taskDefinitionArn
    resp = ecs.describe_tasks(cluster=cluster_name, tasks=[task_id])
    tasks = resp.get('tasks', [])
    if not tasks:
        raise ValueError(
            f'No task found with ID {task_id} in cluster {cluster_name}')
    t = tasks[0]
    task_def_arn = t['taskDefinitionArn']

    # 2) Describe that task definition to read the log config from the container
    task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)['taskDefinition']
    # Assuming a single container definition; pick the one you need if more
    container_definitions = task_def['containerDefinitions']
    container_def = container_definitions[0]
    if container_name:
        container_name = container_name.lower()
        for x in container_definitions:
            if x['name'].lower() == container_name:
                container_def = x
                break
    log_cfg = container_def.get('logConfiguration', {})
    if log_cfg.get('logDriver') != 'awslogs':
        raise RuntimeError('Task is not using the awslogs driver')

    opts = log_cfg['options']
    log_group = opts['awslogs-group']
    stream_pref = opts.get('awslogs-stream-prefix')
    log_region = opts.get('awslogs-region', ecs.meta.region_name)

    # 3) Build the exact stream name
    # ECS uses: {prefix}/{containerName}/{ecsTaskId}
    ecs_task_short_id = t['taskArn'].split('/')[-1]
    pieces = []
    if stream_pref:
        pieces.append(stream_pref)
    pieces.append(container_def['name'])
    pieces.append(ecs_task_short_id)
    stream_name = posixpath.join(*pieces)

    return log_group, stream_name, log_region


def task_status(ctx, cluster_name, task_id, session=None, **kwargs):
    """
    gets the status of a task
    :param ctx:
    :param cluster_name: the name of the cluster
    :param task_id: the id of the task
    :param session: the session passed in from `AwsTask`
    :param kwargs:
    :return:
    """
    ecs = session.client('ecs')
    response = ecs.describe_tasks(
        cluster=cluster_name, tasks=[task_id]
    )
    response = response['tasks'][0]
    status = response['lastStatus']
    if status == 'STOPPED':
        code = response.get('stopCode')
        reason = response.get('stoppedReason')
        if code:
            notice('stop code')
            notice_end(code)
        if reason:
            print(f'{reason}')
        containers = response.get('containers') or []
        for x in containers:
            reason = x.get('reason')
            if reason:
                notice(f'container {x["name"]} stopped with reason')
                notice_end()
                print(reason)
    return status


def print_logs(group_name=None, stream_name=None, start_time=None, client=None, session=None):
    from ..cloudwatch import yield_logs
    lines = list(
        yield_logs(group_name, stream_name, start_time, client=client, session=session)
    )
    lines.sort(key=lambda lx: lx['timestamp'])
    for x in lines:
        print(x['message'])
    if lines:
        start_time = lines[-1]['timestamp']
    return start_time


@task(klass=AwsTask)
def task_logs(ctx, cluster_name, task_id, container_name=None, session=None, **kwargs):
    logs = session.client('logs')
    start_time = None
    notice(f'getting logs for {task_id}')
    group_name, stream_name, _ = ecs_log_stream(cluster_name, task_id, session, container_name)
    notice_end(f'{group_name}/{stream_name}')
    try:
        for n in range(0, 600):
            try:
                start_time = print_logs(group_name, stream_name, start_time, logs, session)
                if n % 5 == 0:
                    status = task_status(ctx, cluster_name, task_id, session=session)
                    if status == 'STOPPED':
                        break
                time.sleep(1)
            except logs.exceptions.ResourceNotFoundException:
                status = task_status(ctx, cluster_name, task_id, session=session)
                if status == 'STOPPED':
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    time.sleep(3)
    print_logs(group_name, stream_name, start_time, logs, session)


@task(klass=AwsTask)
def get_latest_revision(ctx, task_name, session=None, quiet=False, **kwargs):
    """
    prints out the latest task revision for a task
    :param ctx:
    :param task_name: the name of the task
    :param session: the session passed in from `AwsTask`
    :param quiet: if this flag is set, output is repressed
    :param kwargs:
    :return:
    """
    talkative = not quiet
    if talkative:
        notice('getting task definition')
    ecs = session.client('ecs')
    result = ecs.describe_task_definition(taskDefinition=task_name)
    x = result['taskDefinition']
    result = f"{task_name}:{x['revision']}"
    if talkative:
        notice_end(result)
    return result
