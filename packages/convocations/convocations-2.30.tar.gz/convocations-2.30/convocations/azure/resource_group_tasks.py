from raft.tasks import task
from .base import AzureTask


@task(klass=AzureTask)
def resource_groups(
        ctx, name=None,
        client_id=None, client_secret=None,
        subscription_id=None, creds=None, **kwargs):
    """
    prints a list of available resource groups in a subscription
    """
    from convocations.base.utils import get_context_value
    from convocations.base.utils import print_table
    from azure.mgmt.resource.resources import ResourceManagementClient
    name = name or ''
    subscription_id = subscription_id or get_context_value(ctx, 'azure.subscription_id')
    client = ResourceManagementClient(credential=creds, subscription_id=subscription_id)
    header = [ 'name' ]
    rows = []
    for x in client.resource_groups.list():
        st = x.name.lower()
        if name in st:
            rows.append([
                x.name
            ])
    print_table(header, rows)


@task(klass=AzureTask)
def providers(
        ctx, name=None, verbose=False,
        client_id=None, client_secret=None,
        subscription_id=None, creds=None, **kwargs):
    """
    prints a list of available providers and resource types
    """
    from convocations.base.utils import get_context_value
    from convocations.base.utils import print_table, notice, notice_end
    from azure.mgmt.resource.resources import ResourceManagementClient
    name = name or ''
    subscription_id = subscription_id or get_context_value(ctx, 'azure.subscription_id')
    notice('loading providers')
    client = ResourceManagementClient(credential=creds, subscription_id=subscription_id)
    if verbose:
        header = [ 'provider', 'resource_type', 'api_version' ]
    else:
        header = [ 'provider', 'resource_type', 'default_api_version' ]
    rows = []
    name = name.lower()
    for x in client.providers.list():
        ns = x.namespace
        st = ns.lower()
        if name in st:
            if verbose:
                for y in x.resource_types:
                    for v in y.api_versions:
                        rows.append([ ns, y.resource_type, v ])
            else:
                for y in x.resource_types:
                    rows.append([
                        ns,
                        y.resource_type,
                        y.default_api_version,
                    ])
    notice_end()
    print_table(header, rows)
