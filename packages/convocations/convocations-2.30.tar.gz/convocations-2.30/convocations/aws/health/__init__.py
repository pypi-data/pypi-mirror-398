from raft.tasks import task
from ...base.utils import dump_yaml
from ..base import AwsTask
from ..base import yielder


@task(klass=AwsTask)
def ec2_events(ctx, session=None, **kwargs):
    """
    shows all health events for ec2 instances that are
    in status open
    """
    health = session.client('health')
    fn = yielder(health, 'describe_events', session=session)
    events = list(fn)
    dump_yaml(events, quiet=False)
