from raft.collection import Collection
from .subscription_tasks import subscriptions
from .resource_group_tasks import resource_groups
from .resource_group_tasks import providers
from .ldap_tasks import update_ldaps_cert
from .application_tasks import apps, register_app
from .group_tasks import groups
from .group_tasks import create_group
from .group_tasks import add_group_members
from .group_tasks import list_group_members
from .sharepoint_tasks import grant_access_to_site
from .sharepoint_tasks import revoke_site_access
from .sharepoint_tasks import list_site_permissions
from .whoami import whoami


azure_tasks = Collection()
azure_tasks.add_task(subscriptions)
azure_tasks.add_task(resource_groups)
azure_tasks.add_task(providers)
azure_tasks.add_task(update_ldaps_cert)
azure_tasks.add_task(apps)
azure_tasks.add_task(groups)
azure_tasks.add_task(create_group)
azure_tasks.add_task(add_group_members)
azure_tasks.add_task(list_group_members)
azure_tasks.add_task(grant_access_to_site)
azure_tasks.add_task(revoke_site_access)
azure_tasks.add_task(list_site_permissions)
azure_tasks.add_task(whoami)
azure_tasks.add_task(register_app)
