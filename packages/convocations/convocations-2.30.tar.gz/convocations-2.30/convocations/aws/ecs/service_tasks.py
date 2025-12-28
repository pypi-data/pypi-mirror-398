import time
from raft.tasks import task
from ..base import AwsTask


@task(klass=AwsTask, help={
    'cluster': 'ecs cluster name',
    'service': 'ecs service name, must be running on `cluster`',
    'interval': 'the polling interval at which logs are checked, default is 10 seconds',
    'tail': 'the number of previous events to show, default is 10',
})
def watch_service_deploy(ctx, cluster, service, interval=10, tail=10, session=None, **kwargs):
    """
    watches the ecs service event log until a deployment is completed or fails.

    n.b., the timestamps on the service event log are displayed in
    US/Central timezone.
    """
    from botocore.exceptions import ClientError
    from pytz import timezone
    from ...base.utils import notice_end
    ecs = session.client('ecs')
    cst6cdt = timezone('US/Central')
    seen_ids = set()
    primary = None
    first = True
    while True:
        try:
            response = ecs.describe_services(cluster=cluster, services=[service])
        except ClientError as err:
            if err.response['Error']['Code'] == 'ServiceNotActiveException':
                notice_end(f'service {service} not active.')
                return
            # Anything else coming from ECS → propagate or handle as needed
            raise
        service0 = response['services'][0]
        deployments = service0.get('deployments') or []
        primary = None
        for x in deployments:
            if x['status'] == 'PRIMARY':
                primary = x
                break
        # ECS returns events in reverse chronological order (newest first)
        # so we reverse to print oldest first
        new_events = []
        for event in service0.get('events', []):
            st_id = event['id']
            if st_id not in seen_ids:
                new_events.append(event)
                seen_ids.add(st_id)
                if first and len(new_events) >= tail:
                    break
            else:
                break
        first = False
        if new_events:
            new_events = new_events[::-1]
            for x in new_events:
                dt = x['createdAt']
                dt = dt.astimezone(cst6cdt)
                dt = dt.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{dt}] {x['message']}")
        if primary and primary['rolloutState'] == 'COMPLETED':
            break
        # If the service ever stops returning new events you’ll just loop here
        time.sleep(interval)
    if primary:
        if primary['rolloutState'] == 'COMPLETED':
            notice_end(f'deployment completed successfully for service {service} in cluster {cluster}.')
        else:
            reason = primary['rolloutStateReason']
            notice_end(f'deployment failed: [{reason}]')
