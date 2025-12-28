import string
import random
from raft.tasks import task
from .base import AzureTask


@task(klass=AzureTask)
def update_ldaps_cert(ctx, certificate, key,
                      domain=None, resource_group=None,
                      client_id=None, client_secret=None,
                      subscription_id=None, creds=None, **kwargs):
    """
    updates ldaps cet for the specified domain
    use https://learn.microsoft.com/en-us/azure/templates/microsoft.aad/domainservices?pivots=deployment-language-bicep
    for the syntax of the update object
    """
    from convocations.base.utils import get_context_value
    from convocations.base.utils import notice, notice_end
    from azure.mgmt.resource.resources.models import GenericResource
    from azure.mgmt.resource.resources import ResourceManagementClient
    from cryptography.x509 import load_pem_x509_certificates
    from cryptography.hazmat.primitives.serialization import BestAvailableEncryption
    from cryptography.hazmat.primitives.serialization import \
        load_pem_private_key
    from cryptography.hazmat.primitives.serialization.pkcs12 import \
        serialize_key_and_certificates
    from base64 import b64encode
    notice('building pfx')
    allowed = string.ascii_uppercase + string.ascii_lowercase + string.digits
    st_password = ''.join([ random.choice(allowed) for _ in range(16) ])
    with open(certificate, 'rb') as f:
        certs = load_pem_x509_certificates(f.read())
    with open(key, 'rb') as f:
        key = load_pem_private_key(f.read(), password=None)
    en_password = BestAvailableEncryption(st_password.encode('utf-8'))
    p12 = serialize_key_and_certificates(
        None,
        key,
        certs[0],
        certs[1:] or None,
        en_password
    )
    notice_end()
    notice('updating ldaps cert')
    subscription_id = subscription_id or get_context_value(ctx, 'azure.subscription_id')
    domain = domain or get_context_value(ctx, 'azure.domain')
    resource_group = resource_group or get_context_value(ctx, 'azure.resource_group')
    client = ResourceManagementClient(credential=creds, subscription_id=subscription_id)
    parameters = GenericResource()
    parameters.properties = {
        'ldapsSettings': {
            'ldaps': 'Enabled',
            'externalAccess': 'Disabled',
            'pfxCertificate': b64encode(p12).decode('utf-8'),
            'pfxCertificatePassword': st_password,
        }
    }
    response = client.resources.begin_update(
        resource_name=domain,
        resource_group_name=resource_group,
        resource_provider_namespace='Microsoft.AAD',
        parent_resource_path='',
        resource_type='DomainServices',
        api_version='2022-12-01',
        parameters=parameters,
    )
    for x in range(30):
        response.wait(5)
        if response.done():
            break
    notice_end()
