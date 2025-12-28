import re
from raft.tasks import task
from .base import AzureTask
from ..base.utils import notice, notice_end, print_table


def print_groups(result):
    header = [ 'id', 'name', 'on-prem' ]
    rows = []
    for x in result:
        rows.append([
            x['id'],
            x['displayName'],
            x['onPremisesSyncEnabled'] or '',
        ])
    print_table(header, rows)


def is_uuid(st):
    regex = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    uuid_regex = re.compile(regex, re.IGNORECASE)
    return bool(uuid_regex.match(st))


def resolve_group_id(api, st):
    if is_uuid(st):
        return st
    notice('getting group')
    result = api.search_groups(st)
    if len(result) > 1:
        notice_end('\N{warning sign} \N{warning sign} \N{warning sign} '
                   'multiple groups found')
        print_groups(result)
        return None
    group_id = result[0]['id']
    notice_end(group_id)
    return group_id


def print_members(members):
    header = [ 'id', 'member' ]
    rows = []
    for i, member in enumerate(members, 1):
        rows.append([
            member['id'],
            member['userPrincipalName'].lower(), ])
    rows.sort(key=lambda lx: lx[1])
    print_table(header, rows)
    print()


@task(klass=AzureTask)
def list_group_members(ctx, group_name_or_id, quiet=False, creds=None, tenant_id=None, **kwargs):
    """
    lists all members of a group
    """
    from affliction.graph_client import SynchronousGraphClient
    api = SynchronousGraphClient(tenant_id, creds=creds)
    if is_uuid(group_name_or_id):
        st = group_name_or_id
        members = api.get_group_members(st)
        if not quiet:
            print_members(members)
        else:
            return members
    result = api.search_groups(group_name_or_id)
    all_members = []
    for x in result:
        group_id = x['id']
        name = x['displayName']
        if not quiet:
            notice(f'{name} / {group_id}')
        members = api.get_group_members(group_id)
        all_members += members
        if not quiet:
            notice_end()
            print_members(members)
    if quiet:
        return all_members
    return None


@task(klass=AzureTask)
def groups(ctx, name, creds=None, quiet=False, members=False, tenant_id=None, **kwargs):
    """
    shows all groups with a substring of name
    """
    from affliction.graph_client import SynchronousGraphClient
    api = SynchronousGraphClient(tenant_id, creds=creds)
    name = (name or '').lower()
    params = None
    result = api.search_groups(name, params=params)
    if quiet:
        return result

    print_groups(result)

    header = [ 'member id', 'group', 'member' ]
    if members:
        for x in result:
            group_id = x['id']
            name = x['displayName']
            notice(name)
            members = api.get_group_members(group_id)
            notice_end()
            rows = []
            for i, member in enumerate(members, 1):
                rows.append([
                    member['id'],
                    x['displayName'],
                    member['userPrincipalName'].lower(), ])
            rows.sort(key=lambda lx: lx[2])
            print_table(header, rows)
            print()
    return None


@task(klass=AzureTask, help={
    'name': 'the name of the group to create',
    'description': 'the group description',
    'creds': 'for internal use only',
    'tenant_id': 'for internal use only',
})
def create_group(
        ctx, name, description=None, creds=None, tenant_id=None, **kwargs):
    """
    creates an entra group with the provided name and description
    """
    from affliction.graph_client import SynchronousGraphClient
    api = SynchronousGraphClient(tenant_id, creds=creds)
    notice('creating group')
    result = api.create_group(name, description=description)
    notice_end(result['id'])


@task(klass=AzureTask)
def add_group_members(
        ctx, group_name_or_id, upn, creds=None, tenant_id=None, **kwargs):
    """
    adds members to a group.  users must be specified by upn.  for group,
    group name or id may be given.  if a group name is provided, and more than
    one group matches the name, nothing will be done.
    """
    from affliction.graph_client import SynchronousGraphClient
    api = SynchronousGraphClient(tenant_id, creds=creds)
    # b3e90e13-9a22-46e0-a7a2-739c61eafd80
    group_id = resolve_group_id(api, group_name_or_id)
    if not group_id:
        return
    upns = upn.split(',')
    for x in upns:
        notice(x)
        try:
            user = api.get_user(x)
        except:
            notice_end(False)
            continue
        notice_end(user['id'])
        notice('adding to group')
        api.add_group_member(group_id, user['id'])
        notice_end()

    members = api.get_group_members(group_id)
    print_members(members)
