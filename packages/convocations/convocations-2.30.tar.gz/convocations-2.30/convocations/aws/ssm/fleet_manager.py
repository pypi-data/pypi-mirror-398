import contextlib
import json
import os
import signal
import sys
from subprocess import check_call

from raft.tasks import task

from convocations.base.utils import get_context_value
from convocations.base.utils import notice, notice_end, print_table
from convocations.aws.base import AwsTask, yielder


def ssm_client(session, quiet=False):
    if not quiet:
        notice('connecting to ssm')
    ssm = session.client('ssm')
    if not quiet:
        notice_end()
    return ssm


def find_managed_instances(name, session, ssm=None, quiet=False):
    name = name.lower()
    ssm = ssm or ssm_client(session, quiet=quiet)
    if not quiet:
        notice('finding matching instances')
    rg = yielder(ssm, 'describe_instance_information', session)
    result = []
    for x in rg:
        st = x['ComputerName']
        instance_id = x['InstanceId']
        if name in st.lower() or name == instance_id:
            result.append(x)
    if not quiet:
        notice_end()
    return result


def instance_table(instances):
    from pytz import timezone
    tz = timezone('CST6CDT')
    header = [ 'id', 'name', 'ip', 'status', 'last' ]
    rows = []
    for x in instances:
        st = x['ComputerName']
        instance_id = x['InstanceId']
        dt = x['LastPingDateTime']
        if dt:
            dt = dt.astimezone(tz)
            dt = dt.strftime('%Y-%m-%d %H:%M')
        else:
            dt = ''
        row = [ instance_id, st, x['IPAddress'] ]
        row.append(x.get('PingStatus', ''))
        row.append(dt)
        rows.append(row)
    rows.sort(key=lambda lx: lx[1])
    print()
    print_table(header, rows)


@task(klass=AwsTask)
def managed_instances(ctx, name='', session=None, **kwargs):
    """
    lists all ssm managed instances with `name` in their `ComputerName`
    """
    rg = find_managed_instances(name, session)
    instance_table(rg)


@task(klass=AwsTask)
def unmanaged_instances(ctx, session=None, **kwargs):
    """
    lists all ec2 instances not enrolled in ssm management
    """
    from convocations.aws.base import name_tag
    from convocations.aws.ec2 import yield_instances
    rg = find_managed_instances(name='', session=session)
    managed_ids = { x['InstanceId'] for x in rg }
    notice('connecting to ec2')
    instances = yield_instances(session=session)
    instances = [ x for x in instances if x['InstanceId'] not in managed_ids ]
    notice_end()
    header = [ 'id', 'name', 'ip' ]
    rows = []
    for x in instances:
        row = [ x['InstanceId'], name_tag(x), x.get('PrivateIpAddress', '') ]
        rows.append(row)
    rows.sort(key=lambda lx: lx[1])
    print()
    print_table(header, rows)


@task(klass=AwsTask)
def ssm_documents(ctx, quiet=False, session=None, **kwargs):
    """
    prints a list of available ssm documents
    """
    ssm = ssm_client(session, quiet=quiet)
    filters = [{
        'Key': 'DocumentType',
        'Values': [ 'Session' ],
    }, {
        'Key': 'Owner',
        'Values': [ 'Amazon', ],
    }, {
        'Key': 'Name',
        'Values': [ 'SSM-SessionManager', ]
    }]
    rg = yielder(ssm, 'list_documents', session=session,
                 Filters=filters)
    header = [ 'name' ]
    rows = []
    for x in rg:
        rows.append([ x['Name'] ])
    print_table(header, rows)


@contextlib.contextmanager
def ignore_user_entered_signals():
    """
    Ignores user entered signals to avoid process getting killed.
    """
    if sys.platform == 'win32':
        signal_list = [signal.SIGINT]
    else:
        signal_list = [signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP]
    actual_signals = []
    for user_signal in signal_list:
        actual_signals.append(signal.signal(user_signal, signal.SIG_IGN))
    try:
        yield
    finally:
        for sig, user_signal in enumerate(signal_list):
            signal.signal(user_signal, actual_signals[sig])


@task(klass=AwsTask, help={
    'name': 'the name or instance id of the target instance in ssm',
    'reason': 'the reason we are using ssm to connect, for auditing',
    'session': 'do not pass anything into this parameter',
})
def start_shell(ctx, name, reason='convocations', session=None, quiet=False, **kwargs):
    """
    starts a shell to the specified instance
    """
    ssm = ssm_client(session, quiet=quiet)
    rg = find_managed_instances(name, session, ssm=ssm, quiet=quiet)
    if not rg:
        notice_end('no matching instances found')
        return
    if len(rg) > 1:
        notice_end('2 or more matching instances found')
        instance_table(rg)
        return
    notice('checking plugin version')
    result = ctx.run('session-manager-plugin --version', hide=True, warn=False)
    if result.exited != 0:
        notice_end(False)
        notice_end('please install the session manager plugin')
        base_url = 'https://docs.aws.amazon.com/systems-manager/latest/userguide/'
        print(f'ubuntu: {base_url}install-plugin-debian-and-ubuntu.html')
        print(f'windows: {base_url}install-plugin-windows.html')
        return
    notice_end(f'{result.stdout}')
    instance_id = rg[0]['InstanceId']
    params = { 'Reason': reason, 'Target': instance_id, }
    start_session_result = ssm.start_session(**params)
    profile = get_context_value(ctx, 'aws.profile')
    endpoint_url = ssm.meta.endpoint_url
    env = os.environ.copy()
    env_key = 'AWS_SSM_START_SESSION_RESPONSE'
    env[env_key] = json.dumps(start_session_result)
    with ignore_user_entered_signals():
        check_call([
            "session-manager-plugin",
            env_key,
            ssm.meta.region_name,
            "StartSession",
            profile,
            json.dumps(params),
            endpoint_url], env=env)
