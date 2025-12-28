from raft import task
from ..base import AwsTask
from ..base import yielder
from ..base import name_tag


@task(klass=AwsTask)
def efs(ctx, name=None, access_points=True, session=None, **kwargs):
    """
    lists matching efs drives where the value of name tag contains the provided value
    if no value for `name` is provided, the convocation will display all
    efs drives in the region.
    """
    from ...base.utils import print_table, notice, notice_end
    client = session.client('efs')
    notice('describing file systems')
    fn = yielder(client, 'describe_file_systems', session=session)
    shares = list(fn)
    notice_end(len(shares))
    header = [ 'id', 'name', 'date', ]
    if access_points:
        header.append('access points')
    rows = []
    name = (name or '').lower()
    for x in shares:
        fs_name = name_tag(x)
        fs_id = x['FileSystemId']
        if name in fs_name or name == fs_id:
            row = [fs_id , fs_name, x['CreationTime'] ]
            rows.append(row)
    if access_points:
        notice('describing access points')
        for row in rows:
            fs_id = row[0]
            try:
                response = client.describe_access_points(FileSystemId=fs_id)
            except:
                row.append('')
                continue
            if not response['AccessPoints']:
                row.append('')
                continue
            ap_ids = [ x['AccessPointId'] for x in response['AccessPoints'] ]
            row.append(', '.join(ap_ids))
        notice_end()
    print_table(header, rows)
