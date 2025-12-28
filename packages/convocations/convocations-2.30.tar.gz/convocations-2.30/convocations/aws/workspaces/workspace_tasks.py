from raft.tasks import task
from ...base.utils import notice, notice_end, print_table
from ..base import AwsTask


@task(klass=AwsTask)
def workspaces(ctx, name='', session=None, **kwargs):
    """
    lists all available workspaces
    """
    from ..base import yielder
    notice('getting workspaces')
    client = session.client('workspaces', region_name='us-east-1')
    rg = yielder(client, 'describe_workspaces', session)
    workspace_map = { x['WorkspaceId']: x for x in rg }
    notice_end(len(workspace_map))
    notice('getting statuses')
    w = list(workspace_map.keys())
    key = 'LastKnownUserConnectionTimestamp'
    while w:
        workspace_ids = w[:25]
        w = w[25:]
        statuses = yielder(
            client,
            'describe_workspaces_connection_status',
            session, WorkspaceIds=workspace_ids)
        statuses = list(statuses)
        for x in statuses:
            workspace_id = x['WorkspaceId']
            last_connection = x.get(key)
            if last_connection:
                last_connection = last_connection.strftime('%Y-%m-%d')
            else:
                last_connection = ''
            workspace_map[workspace_id]['last'] = last_connection
    rows = []
    header = [ 'id', 'user', 'last used' ]
    name = name.lower()
    for x in workspace_map.values():
        username = x['UserName']
        if name in username.lower():
            row = [ x['WorkspaceId'], username, x.get('last', '') ]
            rows.append(row)
    notice_end()
    rows.sort(key=lambda lx: lx[-1])
    rows.reverse()
    print_table(header, rows)
