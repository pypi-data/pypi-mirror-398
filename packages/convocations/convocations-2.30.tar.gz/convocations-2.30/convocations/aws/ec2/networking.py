from raft import task

from ..cfn.import_instance import get_instance
from ..base import AwsTask


@task(klass=AwsTask)
def used_ips(ctx, subnet=None, verbose=False, session=None, **kwargs):
    """
    shows all ips used in a particular subnet in a tabular format

    * you can provide either the subnet id or a substring of the subnet's
      name tag
    * if you provide the name, and multiple subnets match that same name,
      all ips from all matching subnets will be shown; to avoid this,
      use the subnet id in the `subnet` parameter
    * matches will be shown in ascending order of ip address
    * will show the name and id of ec2 instances
    * will show the elb name and elb type of elastic load balancers
    * will show the file system id for efs mount targets
    * if verbose mode is enabled, if a resource is not an efs, elb, or ec2
      instance, we will print the full yaml for the object
    """
    from ...base.utils import notice, notice_end
    from ...base.utils import dump_yaml
    from ...base.utils import print_table
    from ..ec2 import get_tag
    from ..base import yielder
    ec2 = session.client('ec2')
    notice('loading subnets')
    rg_subnets = list(yielder(ec2, 'describe_subnets', session=session))
    notice_end()
    id_matches = []
    name_matches = []
    matches = None
    subnet = (subnet or '').lower()
    for x in rg_subnets:
        n_id = x['SubnetId']
        if n_id == subnet:
            id_matches.append(n_id)
        name = get_tag(x, 'name')
        if subnet in name.lower():
            name_matches.append(n_id)
    if id_matches:
        matches = id_matches
    else:
        matches = name_matches
    if not matches:
        notice_end('no matching subnets')
    else:
        notice_end(f'found {len(matches)} subnet match(es)')
    notice('loading interfaces')
    rg_interfaces = list(yielder(
        ec2,
        'describe_network_interfaces',
        session=session,
        Filters=[{
            'Name': 'subnet-id',
            'Values': matches,
        }]
    ))
    notice_end(f'found {len(rg_interfaces)}')
    notice('verbose')
    notice_end(f'{verbose}')
    header = [ 'ip', 'id', 'name' ]
    rows = []
    for x in rg_interfaces:
        attachment = x.get('Attachment') or {}
        instance_id = attachment.get('InstanceId')
        owner_id = attachment.get('InstanceOwnerId')
        description = (x.get('Description') or '').lower()
        interface_type = x.get('InterfaceType') or ''
        name = ''
        if instance_id:
            name, _ = get_instance(ctx, None, instance_id, session=session)
        elif owner_id == 'amazon-elb':
            try:
                instance_id, name = description.rsplit('/', 1)[0].rsplit('/', 1)
            except ValueError:
                instance_id, name = description.split(' ', 1)
        elif owner_id == 'amazon-aws':
            if description.startswith('efs'):
                description = description.rsplit(' ', 1)[0]
                name, instance_id = description.split(' for ', 1)
            if interface_type == 'vpc_endpoint':
                instance_id = description.split(' ')[-1]
                name = interface_type
            if description.startswith('network interface for transit gateway'):
                _, instance_id = description.rsplit(' ', 1)
                name = 'tgw vpc attachment'
            if description.startswith('aws lambda vpc'):
                instance_id = x['NetworkInterfaceId']
                name = 'lambda'
        elif owner_id == 'amazon-rds':
            name = 'rds'
            instance_id = x['NetworkInterfaceId']
        elif owner_id == 'amazon-redshift':
            name = 'redshift'
            instance_id = x['NetworkInterfaceId']
        elif description.startswith('es '):
            instance_id = description.split(' ', 1)[-1]
            name = 'opensearch'
        elif description.startswith('elasticache '):
            name, instance_id = description.split(' ', 1)
        elif description.startswith('interface for nat gateway'):
            _, instance_id = description.rsplit(' ', 1)
            name = 'nat gateway'
        if verbose and not instance_id:
            dump_yaml(x, quiet=False)
        if instance_id is None:
            instance_id = x['NetworkInterfaceId']
            name = description
        for y in x['PrivateIpAddresses']:
            rows.append([
                y['PrivateIpAddress'],
                instance_id,
                name,
            ])
    rows.sort(key=lambda lx: list(map(int, lx[0].split('.'))))
    print_table(header, rows)
