import os
import re
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
import time
import boto3
from raft.tasks import task
from .ec2 import instance_by_name, aws_filter
from .base import AwsTask, get_account_id, get_tag
from ..base.utils import notice, notice_end, confirm
from ..base.utils import print_table


def get_latest_ami(name, session):
    ec2 = session.client('ec2')
    responses = ec2.describe_images(Filters=[{
        'Name': 'name',
        'Values': [ f'*{name}*', ],
    }], Owners=[
        session.account_id,
    ])
    images = responses['Images']
    dt = datetime.utcnow()
    latest_image = None
    for image in images:
        creation_date = image['CreationDate']
        creation_date = datetime.strptime(creation_date[:-5], '%Y-%m-%dT%H:%M:%S')
        if dt - creation_date < timedelta(minutes=10):
            latest_image = image
    return latest_image


def load_image(image, session):
    ec2 = session.resource('ec2')
    image_id = image['ImageId']
    return ec2.Image(image_id)


def public_ip(ami_name, session=None):
    """
    Grabs the public IP address from the output in
    cloudformation
    """
    session = session or boto3.DEFAULT_SESSION
    cfn = session.resource('cloudformation')
    notice('getting ip')
    stack = cfn.Stack(f'{ami_name}')
    stack.load()
    outputs = stack.outputs or []
    result = None
    for x in outputs:
        if x['OutputKey'] == 'Ip':
            result = x['OutputValue']
            break
    notice_end(result or 'not found')
    return result


def tail_output_log(ctx, ip, name, session, delay=None):
    """
    In our standard ami builds, the
    user data log file will be written to
    /var/log/{ami_name}-output.log.  Tail it here
    """
    wait_time = 30 if delay is None else int(delay)
    instance = instance_by_name(ctx, name, session=session)
    username = get_tag(instance, 'ssh_user') or 'ubuntu'
    if 'centos' in name:
        username = 'centos'
        wait_time = 90 if delay is None else delay
    elif 'oracle' in name or 'ol7' in name or 'ol8' in name:
        username = 'ec2-user'
        wait_time = 90 if delay is None else delay
    elif 'amazon' in name or 'amzn' in name:
        username = 'ec2-user'
        wait_time = 20 if delay is None else delay
    key_pair = get_tag(instance, 'key_name') or instance.key_name
    if not key_pair.startswith('/'):
        key_pair = f'/{key_pair}'
    notice(f'loading {key_pair} from ssm')
    ssm = session.client('ssm')
    x = ''
    local_key = None
    try:
        try:
            key = ssm.get_parameter(Name=key_pair, WithDecryption=True)
            with NamedTemporaryFile('w', suffix='.key', delete=False) as f:
                f.write(key['Parameter']['Value'])
                local_key = f.name
            os.chmod(local_key, 0o600)
            x = f'-i {local_key}'
            notice_end()
        except Exception as ex:
            notice_end(f'{ex}')
        notice(f'waiting {wait_time} seconds for ssh')
        time.sleep(wait_time)
        notice_end()

        ctx.run(
            f'ssh {x} -o "ServerAliveInterval 2" {username}@{ip}'
            f' "sudo tail -F /var/log/{name}-output.log -F /var/log/cfn-init-cmd.log | '
            f' stdbuf -o0 sed \'/^Cloud-init.*finished at.*/ q\'"', warn=True)
        ctx.run(
            f'ssh {x} -o "ServerAliveInterval 2" {username}@{ip}'
            f' "sudo tail -f /var/log/cfn-init-cmd.log"', warn=True)
        notice_end('----- end of output log -----')
    finally:
        if os.path.exists(local_key):
            os.remove(local_key)


@task(klass=AwsTask)
def wait_for_ami(ctx, name, session=None, delay=None, **kwargs):
    """
    waits for an ami with `name` in it
    """
    # first check if we have a public ip available
    if not name.endswith('-ami'):
        name = f'{name}-ami'
    ip = public_ip(name, session)
    if ip:
        tail_output_log(ctx, ip, name, session, delay=delay)
    name = name[:-4]
    p_image = None
    for i in range(1, 41):
        if p_image:
            notice(f'checking {p_image.id}/{i}')
            p_image.load()
            notice_end(p_image.state)
            if p_image.state == 'available':
                break
        else:
            notice(f'check #{i}')
            latest_image = get_latest_ami(name, session)
            if not latest_image:
                notice_end('not yet initiated')
            else:
                p_image = load_image(latest_image, session)
                notice_end(f'{p_image.id}/{p_image.state}')
                if p_image.state == 'available':
                    break
        time.sleep(15)


@task(positional=['name'], klass=AwsTask, help={
    'name': 'the name of the ami to look for, we will search case-insensitive '
            'for partial match',
    'owners': 'a comma delimited list of owner ami ids to filter by',
    'product_codes': 'a comma delimited list of product codes to filter by',
})
def amis(ctx, name=None, owners=None,
         product_codes=None, quick=False,
         session=None, profile=None, verbose=False, **kwargs):
    """
    Lists all of our amis in aws
    """
    notice('getting images')
    images = []
    if name:
        name = name.lower()
    ec2 = session.client('ec2')
    owners = owners.split(',') if owners else [ 'self' ]
    filters = None
    if product_codes:
        owners.append('aws-marketplace')
        product_codes = product_codes.split(',')
        filters = [ aws_filter('product-code', x) for x in product_codes ]
    params = dict(Owners=owners, Filters=filters)
    if not filters:
        del params['Filters']
    result = ec2.describe_images(**params)
    for x in result['Images']:
        if not name or name in x['Name'].lower():
            images.append(x)
    images.sort(key=lambda lx: lx['CreationDate'])
    images = images[::-1]
    rows = []
    for x in images:
        row = [
            x['ImageId'], x['Name'],
            x['CreationDate'].split('T', 1)[0], x['State'],
        ]
        snapshots = []
        for device_mapping in x['BlockDeviceMappings']:
            if 'Ebs' in device_mapping:
                snapshot_id = device_mapping.get('Ebs', {}).get('SnapshotId')
                snapshot_id = snapshot_id or ''
                snapshots.append(snapshot_id)
        row.append(', '.join(snapshots))
        if verbose:
            row.append(x.get('Description') or '')
        rows.append(row)

    notice_end()
    if quick:
        values = ','.join(x[0] for x in rows)
        print(values)
    else:
        header = ['id', 'name', 'at', 'status', 'snapshot_id' ]
        if verbose:
            header.append('desc')
        print_table(header, rows)


@task(klass=AwsTask, help={
    'image_ids': 'the ami id of the image to delete',
})
def delete_ami(ctx, image_ids, session=None, **kwargs):
    """
    Deletes the ami and any associated snapshots
    """
    ec2 = session.resource('ec2')
    for image_id in image_ids.split(','):
        notice('loading image')
        image = ec2.Image(image_id)
        image.load()
        if not image.meta.data:
            notice_end('not found')
            return
        notice_end(image.name)
        snapshot_ids = []
        snapshots = []
        for x in image.block_device_mappings:
            ebs = x.get('Ebs') or {}
            snapshot_id = ebs.get('SnapshotId')
            if snapshot_id:
                notice(f'loading {snapshot_id}')
                snapshot_ids.append(snapshot_id)
                snapshot = ec2.Snapshot(snapshot_id)
                snapshots.append(snapshot)
                notice_end()
        if not snapshots:
            notice('finding snapshots')
            notice_end('n/a')
        r = confirm(f'You are deleting ami [{image.name}]')
        if not r:
            return

        notice('deregistering ami')
        image.deregister()
        notice_end()
        for snapshot_id, snapshot in zip(snapshot_ids, snapshots):
            notice(f'deleting {snapshot_id}')
            snapshot.delete()
            notice_end()


@task(klass=AwsTask, help={
    'image_id': 'the ami id of the image to delete',
})
def delete_ami_snapshots(ctx, image_id, session=None, **kwargs):
    """
    Deletes the ami and any associated snapshots
    """
    from convocations.aws.base import yielder
    account_id = get_account_id(session)
    ec2 = session.client('ec2')
    notice('finding snapshots')
    snapshots = yielder(ec2, 'describe_snapshots', OwnerIds=[ account_id ])
    rows = []
    for x in snapshots:
        description = x.get('Description') or ''
        snapshot_id = x.get('SnapshotId')
        if image_id in description:
            row = [ snapshot_id, description ]
            rows.append(row)
    notice_end(f'{len(rows)}')
    print_table([ 'id', 'description' ], rows)
    for x, _ in rows:
        r = confirm(f'deleting {x}')
        if r:
            ec2.delete_snapshot(SnapshotId=x)


@task(klass=AwsTask)
def orphaned_ami_snapshots(ctx, delete=False, session=None, **kwargs):
    """
    Finds any ami related snapshots where the original ami has been
    deregistered
    """
    from convocations.aws.base import yielder
    account_id = get_account_id(session)
    ec2 = session.client('ec2')
    notice('finding snapshots')
    snapshots = yielder(ec2, 'describe_snapshots', OwnerIds=[ account_id ])
    snapshots = list(snapshots)
    matcher = re.compile(
        r'^Created by CreateImage\(i\-[0-9a-f]+\) for (?P<image_id>ami\-[0-9a-f]+)$',
    )
    mp_snapshots = defaultdict(list)
    image_ids = set()
    for x in snapshots:
        description = x.get('Description') or ''
        result = matcher.match(description)
        if result:
            image_id = result.group('image_id')
            image_ids.add(image_id)
            x['ImageId'] = image_id
            mp_snapshots[image_id].append(x)
    notice_end(f'{len(snapshots)}')
    notice('loading amis')
    images = yielder(ec2, 'describe_images', Owners=[ account_id ])
    available_image_ids = { x['ImageId'] for x in images }
    notice_end(f'{len(available_image_ids)}')
    unavailable_image_ids = image_ids - available_image_ids
    rows = []
    for x in snapshots:
        image_id = x.get('ImageId')
        if not image_id:
            continue
        description = x.get('Description') or ''
        snapshot_id = x.get('SnapshotId')
        if image_id in unavailable_image_ids:
            row = [ snapshot_id, description ]
            rows.append(row)
    print_table([ 'id', 'description' ], rows)
    if delete:
        for x, _ in rows:
            r = confirm(f'delete {x}')
            if r:
                ec2.delete_snapshot(SnapshotId=x)


@task(klass=AwsTask)
def centos_amis(ctx, session=None, prefix=None, **kwargs):
    """
    finds all marketplace amis released under the centos product code
    """
    amis(ctx, product_codes='aw0evgkw8e5c1q413zgy5pjce', session=session)


@task(klass=AwsTask)
def oracle_amis(ctx, session=None, prefix=None, **kwargs):
    """
    finds all marketplace amis released under the oracle owner id
    """
    amis(ctx, owners='131827586825', session=session, prefix=prefix)


@task(klass=AwsTask)
def ubuntu_amis(ctx, session=None, prefix=None, **kwargs):
    """
    finds all marketplace amis released under the ubuntu owner id
    """
    amis(ctx, owners='099720109477', session=session, prefix=prefix)

