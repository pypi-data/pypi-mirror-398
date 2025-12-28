from collections import defaultdict
from raft.tasks import task

from ...base.utils import dump_yaml
from ...base.utils import print_table
from ...base.utils import notice, notice_end
from ..base import AwsTask
from ..base import yielder


def get_records(session, zone_id):
    """
    Get all records in a zone
    """
    notice(f'getting records for {zone_id}')
    route53 = session.client('route53')
    kwargs = dict(
        HostedZoneId=zone_id,
        MaxItems='300',
    )
    rg = list(yielder(route53, 'list_resource_record_sets', **kwargs))
    records = defaultdict(dict)
    for record in rg:
        record_type = record['Type']
        name = record['Name']
        if 'ResourceRecords' in record:
            values = [ x['Value'] for x in record['ResourceRecords'] ]
            values.sort()
        else:
            values = record['AliasTarget']
        records[record_type][name] = (values, record)
    notice_end()
    return records


@task(klass=AwsTask)
def compare_zones(ctx, original_zone_id, original_profile,
                  new_zone_id, new_profile, cfn=False,
                  session=None, debug=False, **kwargs):
    """
    Compare two route53 zones
    """
    from boto3.session import Session
    original_session = Session(profile_name=original_profile)
    new_session = Session(profile_name=new_profile)
    original_records = get_records(original_session, original_zone_id)
    new_records = get_records(new_session, new_zone_id)
    header = [ 'type', 'name', 'status', 'values', 'new_values' ]
    rows = []
    for record_type, records in original_records.items():
        for name, t in records.items():
            values, record = t
            mp_new = new_records[record_type]
            if name not in mp_new:
                rows.append([record_type, name, 'missing', values, '' ])
                continue
            new_values, new_record = mp_new[name]
            if values != new_values:
                rows.append([record_type, name, 'different', values, new_values ])
    print_table(header, rows)
    if cfn:
        for row in rows:
            record_type = row[0]
            name = row[1]
            _, record = original_records[record_type][name]
            mp = {
                'Name': record['Name'],
                'HostedZoneId': '!Ref HostedZone',
                'Type': record['Type'],
            }
            if 'AliasTarget' in record:
                mp['AliasTarget'] = record['AliasTarget']
            elif 'ResourceRecords' in record:
                mp['ResourceRecords'] = [ x['Value'] for x in record['ResourceRecords'] ]
                mp['TTL'] = record['TTL']
            mp = { 'Type': 'AWS::Route53::RecordSet', 'Properties': mp, }
            pieces = [
                x.title().replace('-', '').replace('_', '')
                for x in name.split('.') ]
            pieces = pieces[:-1]
            if record_type == 'CNAME':
                pieces[0] = pieces[0].lower()
            mp = { 'Dot'.join(pieces): mp }
            dump_yaml(mp, quiet=False)
