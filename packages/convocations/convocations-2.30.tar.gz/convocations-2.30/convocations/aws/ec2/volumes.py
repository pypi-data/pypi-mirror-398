from raft.tasks import task
from ..base import AwsTask


@task(klass=AwsTask)
def gp2_to_gp3(ctx, dry_run=False, session=None, **kwargs):
    """
    converts all gp2 volumes to gp3
    """
    from ...base.utils import print_table, notice, notice_end
    from ..base import yielder
    notice('describing volumes')
    ec2 = session.client('ec2')
    filters = [{
        'Name': 'volume-type',
        'Values': [ 'gp2' ],
    }]
    fn = yielder(ec2, 'describe_volumes', session, Filters=filters)
    gp2_volumes = list(fn)
    notice_end(f'{len(gp2_volumes)}')
    rows = []
    for x in gp2_volumes:
        rows.append([ x['VolumeId'], x['VolumeType'] ])
    print_table([ 'volume', 'type' ], rows)
    if dry_run:
        return
    for volume in gp2_volumes:
        volume_id = volume['VolumeId']
        notice(f'modifying {volume_id}')
        ec2.modify_volume(VolumeId=volume_id, VolumeType='gp3')
        notice_end()


@task(klass=AwsTask)
def available_volumes(ctx, session=None, **kwargs):
    """
    lists all unattached volumes
    """
    from ...base.utils import print_table, notice, notice_end
    from ..base import yielder, name_tag
    notice('describing volumes')
    ec2 = session.client('ec2')
    filters = [{
        'Name': 'status',
        'Values': [ 'available' ],
    }]
    fn = yielder(ec2, 'describe_volumes', session, Filters=filters)
    gp2_volumes = list(fn)
    notice_end(f'{len(gp2_volumes)}')
    rows = []
    for x in gp2_volumes:
        name = name_tag(x) or ''
        rows.append([ x['VolumeId'], x['VolumeType'], x['Size'], name ])
    print_table([ 'volume', 'type', 'size', 'name', ], rows)
