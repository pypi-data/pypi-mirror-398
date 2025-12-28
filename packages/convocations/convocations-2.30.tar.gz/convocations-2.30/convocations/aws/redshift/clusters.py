from raft.tasks import task
from ..base import AwsTask


@task(klass=AwsTask)
def redshift_clusters(ctx, name='', session=None, **kwargs):
    """
    describes all the redshift clusters available
    """
    from ...base.utils import print_table
    client = session.client('redshift')
    response = client.describe_clusters()
    clusters = response['Clusters']
    rows = []
    for cluster in clusters:
        rows.append([
            cluster['ClusterIdentifier'],
            cluster['Endpoint']['Address'],
        ])
    print_table([ 'name', 'host' ], rows)
