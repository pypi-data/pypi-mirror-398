from raft import task

from convocations.aws.base import AwsTask


@task(klass=AwsTask)
def start_task(ctx, task_name, command='', cluster=None, tail=True, fargate=True, ec2=False, session=None, **kwargs):
    """
    kicks off a task in ecs

    ```yaml
    tundra:
      ecs:
        cluster: cluster1
        network_configuration:
          subnets:
            - subnet-0123456789
            - subnet-1234567890
          security_groups:
            - sg-0123456789
          assignPublicIp: DISABLED
    ```
    :param ctx:
    :param task_name: the name of the task
    :param command: the command to run inside the container
    :param cluster: the cluster name
    :param tail: if specified, we will tail the logs
    :param fargate: if specified, we will launch in fargate
    :param ec2: if specified, we will launch in ec2
    :param session:
    :param kwargs:

    :return:
    """
    from convocations.aws.ecs import get_latest_revision
    from convocations.aws.ecs import task_logs
    from convocations.base.utils import get_context_value, notice, notice_end
    x = get_latest_revision(ctx, task_name, session=session, quiet=True)
    ecs = session.client('ecs')
    if command:
        command = command.split(' ')
    cluster = cluster or get_context_value(ctx, 'tundra.ecs.cluster')
    network = get_context_value(ctx, 'tundra.ecs.network_configuration')
    if network:
        network = dict(awsvpcConfiguration=network)
    launch_type = 'FARGATE'
    if ec2:
        launch_type = 'EC2'
    notice(f'starting {x} on cluster {cluster} as {launch_type}')
    overrides = {
        'name': task_name,
    }
    if command:
        overrides['command'] = command
    params = dict(
        cluster=cluster,
        taskDefinition=x,
        overrides={
            'containerOverrides': [overrides]
        },
        launchType=launch_type,
    )
    if network:
        params['networkConfiguration'] = network
    result = ecs.run_task(**params)
    result = result['tasks'][0]
    task_arn = result['taskArn']
    task_id = task_arn.rsplit('/', 1)[-1]
    notice_end(task_id)
    if tail:
        task_logs(ctx, cluster, task_name, task_id, session=session, **kwargs)


@task(klass=AwsTask)
def deploy(ctx, cluster=None, service=None, session=None, **kwargs):
    """
    deploys a service in ecs, forcing a new deployment

    :param ctx:
    :param cluster: the cluster name
    :param service: the service name
    :param (boto3.session.Session) session: the session passed in from `AwsTask`
    :param kwargs:

    :return:
    """
    from ..base.utils import get_context_value
    from ..base.utils import notice, notice_end
    from botocore.exceptions import ClientError
    ecs = session.client('ecs')
    cluster = cluster or get_context_value(ctx, 'tundra.ecs.cluster')
    service = service or get_context_value(ctx, 'tundra.ecs.service')
    notice(f'deploying service {service} in cluster {cluster}')
    try:
        response = ecs.update_service(
            cluster=cluster,
            service=service,
            forceNewDeployment=True,
        )
        notice_end(f"{response['service']['status']}")
    except ClientError as ex:
        code = ex.response['Error']['Code']
        notice_end(code)
        if code in ('ServiceNotFoundException', 'ServiceNotActiveException'):
            # Service does not exist → stop the loop
            return
        # Anything else coming from ECS → propagate or handle as needed
        raise
