import asyncio
import webbrowser
from urllib.parse import urlencode

from raft.tasks import task

from ..base.utils import get_context_value
from ..base.utils import notice, notice_end
from .base import AzureTask


@task(klass=AzureTask)
def apps(ctx, name=None, creds=None, quiet=False, **kwargs):
    """
    shows all applications with a substring of name
    """
    from msgraph.graph_service_client import GraphServiceClient
    from msgraph.generated.applications.applications_request_builder import (
        ApplicationsRequestBuilder as A,
    )
    from msgraph.generated.models.application_collection_response import (
        ApplicationCollectionResponse as AppResponse,
    )
    from ..base.utils import print_table
    client = GraphServiceClient(credentials=creds)
    name = (name or '').lower()
    result = []

    async def yield_applications(skip=0):
        params = A.ApplicationsRequestBuilderGetQueryParameters(
            count=True,
            top=999,
        )
        if name:
            notice('building search')
            pieces = name.split(' ')
            search_query = [ f'"displayName:{piece}"' for piece in pieces ]
            params.search = ' AND '.join(search_query)
            notice_end(params.search)
        builder = A.ApplicationsRequestBuilderGetRequestConfiguration(
            query_parameters=params,
            headers={
                'ConsistencyLevel': 'eventual',
            }
        )
        notice('executing search')
        response: AppResponse = await client.applications.get(builder)
        notice_end(f'{response.odata_count}')
        for x in response.value:
            yield x
        if response.odata_next_link:
            async for x in yield_applications(skip + len(response.value)):
                yield x

    async def get():
        async for x in yield_applications():
            result.append(x)

    asyncio.run(get())
    if result and not quiet:
        header = [ 'app_id', 'name', ]
        rows = []
        for row in result:
            rows.append([
                row.id,
                row.display_name,
            ])
        rows.sort(key=lambda lx: lx[1].lower())
        print_table(header, rows)
        return None
    return result


@task(klass=AzureTask, help={
    'name': 'the name of the app, exact match, case-insensitive',
    'target_tenant_id': 'the id or fully-qualified tenant name '
                        '(e.g., contoso.onmicrosoft.com) that will be '
                        'granting permissions to the app',
})
def register_app(ctx, name, target_tenant_id, creds=None, **kwargs):
    """
    registers an app with the specified tenant id by requesting admin consent
    :param ctx: the context
    :param name: the name of the app (exact match, case-insensitive)
    :param target_tenant_id: the id or fully qualified tenant name
                             (e.g., contoso.onmicrosoft.com) of the tenant
                             granting permission to the app
    :param creds: leave blank
    """
    from affliction.graph_client import SynchronousGraphClient
    home_tenant = get_context_value(ctx, 'azure.tenant_id')
    notice('looking up app id')
    api = SynchronousGraphClient(tenant_id=home_tenant, creds=creds)
    result = api.get_apps({
        '$search': f'"displayName:{name}"',
    })
    name = name.lower()
    client_id = None
    for x in result:
        if x['displayName'].lower() == name:
            client_id = x['appId']
            break
    if not client_id:
        notice_end(False)
        return
    notice_end(client_id)
    url = f'https://login.microsoftonline.com/{target_tenant_id}/v2.0/adminconsent'
    params = {
        'client_id': client_id,
        'redirect_uri': 'http://localhost:8080',
        'scope': 'https://graph.microsoft.com/.default',
    }
    q = urlencode(params)
    url = f'{url}?{q}'
    webbrowser.open(url)
