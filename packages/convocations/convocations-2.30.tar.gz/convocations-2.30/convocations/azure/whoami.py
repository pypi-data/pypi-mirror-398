from raft.tasks import task
from .base import AzureTask
from ..base.utils import dump_yaml
from ..base.utils import notice, notice_end


@task(klass=AzureTask)
def whoami(ctx, creds=None, **kwargs):
    """
    calls the whoami endpoint in the graph api
    """
    from affliction.graph_client import SynchronousGraphClient
    notice('calling whoami')
    tenant_id = kwargs.get('tenant_id')
    api = SynchronousGraphClient(tenant_id=tenant_id, creds=creds)
    result = { 'hello': 'sasame' }
    try:
        result = api.whoami()
        notice_end()
    except:
        notice_end()
        notice('appid')
        import jwt
        token = creds.get_token('https://graph.microsoft.com/.default')
        data = jwt.decode(
            token.token.encode('utf8'),
            options={'verify_signature': False})
        app_id = data['appid']
        notice_end(app_id)
        result = api.get(f"{api.base_url}/applications(appId='{app_id}')")
    dump_yaml(result, quiet=False)
