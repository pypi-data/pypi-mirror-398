import os.path

from raft.tasks import task

from ...base.utils import load_yaml
from ...base.utils import notice, notice_end, print_table, dump_yaml
from ...base.utils import get_context_value
from ..base import AwsTask
from ..base import yielder


@task(klass=AwsTask)
def nameservers(ctx, zone_name, session=None, **kwargs):
    """
    lists all of the name servers for a particular zone name
    """
    route53 = session.client('route53')
    g = yielder(route53, 'list_hosted_zones', session)
    header = [ 'zone', 'id', 'nameserver' ]
    rows = []
    for x in g:
        if zone_name.lower() in x['Name']:
            notice(x['Name'])
            hosted_zone = route53.get_hosted_zone(Id=x['Id'])
            if 'DelegationSet' in hosted_zone:
                ns = hosted_zone['DelegationSet']['NameServers']
                for nameserver in ns:
                    rows.append([ x['Name'], x['Id'], nameserver ])
            else:
                rows.append([ x['Name'], x['Id'], '' ])
            notice_end()
    print_table(header, rows)


def recordset_key(values):
    t = values['Type']
    if t in ('A', 'CNAME'):
        t = 'ACNAME'
    return f"{values['Name']}::{t}"


def update_template(filepath, data):
    from ...base.utils import yaml_serializer
    notice(f'updating {filepath}')
    rt = yaml_serializer(typ='rt')
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            template_body = rt.load(filepath)
        resources = template_body['Resources']
        resource_map = {
            recordset_key(values['Properties']): x
            for x, values in resources.items()
            if values['Type'] == 'AWS::Route53::RecordSet'
        }
        for key, values in data.items():
            rkey = recordset_key(values['Properties'])
            existing_key = resource_map.get(rkey)
            if existing_key:
                props = values['Properties']
                resources[existing_key]['Properties']['Type'] = props['Type']
                resource_records = props.get('ResourceRecords')
                if resource_records:
                    resources[existing_key]['Properties']['ResourceRecords'] = resource_records
                else:
                    alias_target = props.get('AliasTarget')
                    resources[existing_key]['Properties'][
                        'AliasTarget'] = alias_target
            else:
                resources[key] = values
    else:
        template_body = dict(
            AWSTemplateFormatVersion='2010-09-09',
            Description='imported via upholstery',
            Resources=data,
        )
        notice_end('not found')
    with open(filepath, 'w') as f:
        rt.dump(template_body, f)
    notice_end()


@task(klass=AwsTask)
def export_hosted_zone(ctx, domain=None, zone_id=None, filename=None, session=None, prefix=None, **kwargs):
    """
    creates cloudformation yaml for all recordsets in a hostedzone
    """
    route53 = session.client('route53')
    if not zone_id:
        notice('finding zone id')
        zones = list(yielder(route53, 'list_hosted_zones', session))
        for x in zones:
            name = x['Name']
            if domain in { name, name[:-1] }:
                zone_id = x['Id']
                domain = name
                break
        if not zone_id:
            notice_end(False)
            return
        notice_end(zone_id)
    if not domain:
        notice('finding domain')
        zones = list(yielder(route53, 'list_hosted_zones', session))
        for x in zones:
            if x['Id'] == zone_id:
                domain = x['Name']
                break
        if not domain:
            notice_end(False)
            return
        notice_end(domain)
    records = list(yielder(
        route53,
        'list_resource_record_sets',
        session,
        HostedZoneId=zone_id))
    resources = {}
    for x in records:
        name = x['Name']
        t = x['Type']
        properties = {
            'HostedZoneName': domain,
            'Name': name,
            'Type': t,
        }
        for key in 'TTL', 'ResourceRecords', 'AliasTarget':
            value = x.get(key)
            if value:
                if key == 'ResourceRecords':
                    properties[key] = [ y['Value'] for y in value ]
                else:
                    properties[key] = value
        name = name.rsplit(domain, 1)
        name = name[0][:-1].split('.')
        name = [ (piece if name != '.' else 'dot') for piece in name ]
        name = [ piece.title() for piece in name ]
        name = ''.join(name)
        name = name.replace('_', '')
        name = name or 'Apex'
        if t not in ('A', 'CNAME'):
            name = f'{name}{t.lower().title()}'
        name = name.replace('-', '')
        resources[name] = {
            'Type': 'AWS::Route53::RecordSet',
            'Properties': properties,
        }
    if filename:
        prefix = prefix or get_context_value(ctx, 'upholstery.prefix')
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext not in ('.yml', '.yaml'):
            filename = f'{filename}.yml'
        filename = os.path.join(prefix, 'cfn', filename)
        update_template(filename, resources)
    else:
        dump_yaml(resources, quiet=False)
