from raft.tasks import task
from .base import AzureTask


@task(klass=AzureTask)
def subscriptions(ctx, tenant_id=None, client_id=None, client_secret=None, creds=None, **kwargs):
    """
    prints a list of subscriptions available in this account
    """
    from azure.mgmt.resource.subscriptions import SubscriptionClient
    from ..base.utils import print_table
    client = SubscriptionClient(credential=creds)
    header = [ 'id', 'name' ]
    rows = []
    for x in client.subscriptions.list():
        rows.append([
            x.subscription_id,
            x.display_name,
        ])
    print_table(header, rows)


