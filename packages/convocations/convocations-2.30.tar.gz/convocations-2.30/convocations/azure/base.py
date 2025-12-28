import time
from typing import Optional, Any, Iterable, Mapping
from raft.tasks import Task
from raft.context import Context


try:
    from azure.identity._credentials.shared_cache import SharedTokenCacheCredential
    from azure.identity._credentials.shared_cache import _SharedTokenCacheCredential
except ImportError as import_ex:
    print(import_ex)

    class SharedTokenCacheCredential:
        pass

    class _SharedTokenCacheCredential:
        pass


class CachedCredential(_SharedTokenCacheCredential):
    def _get_auth_client(self, **kwargs: Any):
        from azure.identity._internal.aad_client import AadClient
        client_id = kwargs.pop('client_id', None)
        if client_id:
            return AadClient(client_id=client_id, **kwargs)
        return super()._get_auth_client(**kwargs)  # pylint: disable=no-member

    def _get_accounts_having_matching_refresh_tokens(self, is_cae: bool = False):
        """Returns an iterable of cached accounts which have a matching refresh token.

        :param bool is_cae: whether to look in the CAE cache
        :return: an iterable of cached accounts
        :rtype: Iterable[CacheItem]
        """
        import msal
        all_accounts = self._get_cache_items_for_authority(
            msal.TokenCache.CredentialType.ACCOUNT, is_cae)

        accounts = []
        for account in all_accounts:
            # When the token has no family, msal.net falls back to matching client_id,
            # which won't work for the shared cache because we don't know the IDs of
            # all contributing apps. It should be unnecessary anyway because the
            # apps should all belong to the family.
            if account['realm'] == self._tenant_id:
                accounts.append(account)
        return accounts

    def _get_cached_access_token(
        self, scopes: Iterable[str], account: Mapping[str, str], is_cae: bool = False
    ):
        import msal
        from azure.identity import CredentialUnavailableError
        from azure.core.credentials import AccessToken

        cache = self._cae_cache if is_cae else self._cache
        try:
            cache_entries = cache.find(
                msal.TokenCache.CredentialType.ACCESS_TOKEN,
                target=list(scopes),
                query={"realm": account["realm"]},
            )
            for token in cache_entries:
                expires_on = int(token["expires_on"])
                current_time = int(time.time())
                if expires_on - 300 > current_time:
                    return AccessToken(token["secret"], expires_on)
        except Exception as ex:  # pylint:disable=broad-except
            message = f"Error accessing cached data: {ex}"
            raise CredentialUnavailableError(message=message) from ex

        return None

    def _get_account(
        self, username: Optional[str] = None, tenant_id: Optional[str] = None,
        is_cae: bool = False
    ):
        """Returns exactly one account which has a refresh token and matches
        username and/or tenant_id.

        :param str username: an account's username
        :param str tenant_id: an account's tenant ID
        :param bool is_cae: whether to use the CAE cache
        :return: an account
        :rtype: CacheItem
        """
        from azure.identity import CredentialUnavailableError
        accounts = self._get_accounts_having_matching_refresh_tokens(is_cae)
        if not accounts:
            # cache is empty or contains no refresh token -> user needs to sign in
            raise CredentialUnavailableError(
                message=f'no accounts matching {tenant_id}')

        if username:
            filtered_accounts = [ x for x in accounts if x.get('username') == self._username ]
        else:
            filtered_accounts = accounts
        if len(filtered_accounts) == 1:
            return filtered_accounts[0]
        return super()._get_account(username, tenant_id, is_cae)  # pylint: disable=no-member

    def get_token(
        self, *scopes: str, claims: Optional[str] = None, tenant_id: Optional[str] = None, **kwargs: Any
    ):
        from azure.identity import CredentialUnavailableError
        if not scopes:
            raise ValueError("'get_token' requires at least one scope")

        if not self._client_initialized:
            self._initialize_client()

        is_cae = bool(kwargs.get("enable_cae", False))
        token_cache = self._cae_cache if is_cae else self._cache

        # Try to load the cache if it is None.
        if not token_cache:
            token_cache = self._initialize_cache(is_cae=is_cae)

            # If the cache is still None, raise an error.
            if not token_cache:
                raise CredentialUnavailableError(message="Shared token cache unavailable")

        account = self._get_account(self._username, self._tenant_id, is_cae=is_cae)

        token = self._get_cached_access_token(scopes, account, is_cae=is_cae)
        if token:
            return token

        # try each refresh token, returning the first access token acquired
        for refresh_token in self._get_refresh_tokens(account, is_cae=is_cae):
            token = self._client.obtain_token_by_refresh_token(
                scopes, refresh_token, claims=claims,
                tenant_id=tenant_id or self._tenant_id, **kwargs
            )
            return token

        from azure.identity._internal.shared_token_cache import NO_TOKEN
        raise CredentialUnavailableError(message=NO_TOKEN.format(account.get("username")))


class ConvocationsCredential(SharedTokenCacheCredential):
    """Authenticates using tokens in the local cache shared between
    Microsoft applications.

    :param str username: Username (typically an email address) of the user
        to authenticate as. This is used when the
        local cache contains tokens for multiple identities.

    :keyword str authority: Authority of an Azure Active Directory
        endpoint, for example 'login.microsoftonline.com', the authority
        for Azure Public Cloud (which is the default).
        :class:`~azure.identity.AzureAuthorityHosts`
        defines authorities for other clouds.
    :keyword str tenant_id: an Azure Active Directory tenant ID. Used to
        select an account when the cache contains tokens for
        multiple identities.
    :keyword AuthenticationRecord authentication_record: an authentication
        record returned by a user credential such as
        :class:`DeviceCodeCredential` or
        :class:`InteractiveBrowserCredential`
    :keyword cache_persistence_options: configuration for persistent token
        caching. If not provided, the credential
        will use the persistent cache shared by Microsoft development
        applications
    :type cache_persistence_options: ~azure.identity.TokenCachePersistenceOptions
    """

    def __init__(self, username: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(username, **kwargs)
        self._credential = CachedCredential(
            username=username, **kwargs)


def get_token_info(creds, verbose=True):
    """
    prints the username from the jwt we get from the credentials
    """
    from ..base.utils import notice, notice_end
    # from ..base.utils import dump_yaml
    import jwt
    if verbose:
        notice('logged in as')
    token = creds.get_token('https://management.azure.com/.default')
    data = jwt.decode(token.token.encode('utf8'), options={ 'verify_signature': False })
    # dump_yaml(data, quiet=False)
    try:
        upn = data['unique_name']
    except KeyError:
        upn = f'app/{data["appid"]}'
    if verbose:
        notice_end(upn)
        notice('tid')
    tid = data['tid']
    if verbose:
        notice_end(tid)
        notice('issuer')
    issuer = data['iss']
    if verbose:
        notice_end(issuer)
    if issuer.endswith('/'):
        issuer = issuer[:-1]
    issuer_id = issuer.rsplit('/', 1)[-1]
    tenant_id = issuer_id
    return upn, tenant_id


class AzureTask(Task):
    def __call__(self, *args, **kwargs):
        from azure.identity import ClientSecretCredential
        from azure.identity import ChainedTokenCredential
        from azure.identity import InteractiveBrowserCredential
        from azure.identity import TokenCachePersistenceOptions
        from ..base.utils import get_context_value
        from ..base.utils import notice, notice_end
        ctx = args[0]
        has_context = isinstance(ctx, Context)
        client_id = kwargs.get('client_id')
        client_secret = kwargs.get('client_secret')
        tenant_id = kwargs.get('tenant_id')
        allowed_tenants = kwargs.get('allowed_tenants')
        if allowed_tenants:
            allowed_tenants = allowed_tenants.split(',')
        allow_unencrypted_storage = kwargs.get('allow_unencrypted_storage')
        creds = kwargs.get('creds')
        quiet = kwargs.get('quiet') or False
        cache_name = kwargs.get('cache_name') or None
        verbose = not quiet
        if has_context:
            client_id = client_id or get_context_value(ctx, 'azure.client_id')
            client_secret = client_secret or get_context_value(ctx, 'azure.client_secret')
            tenant_id = tenant_id or get_context_value(ctx, 'azure.tenant_id')
            allow_unencrypted_storage = allow_unencrypted_storage or get_context_value(
                ctx, 'azure.allow_unencrypted_storage')
            cache_name = cache_name or get_context_value(ctx, 'azure.cache_name')
        cache_name = cache_name or 'convocations'
        if verbose:
            notice('client_id')
            notice_end(client_id)
            notice('tenant_id')
            notice_end(tenant_id)
            notice('cache name')
            notice_end(cache_name)
        if not creds and client_id and client_secret and tenant_id:
            creds = ClientSecretCredential(tenant_id, client_id, client_secret)
        elif not creds:
            if verbose:
                notice('using interactive credential')
            options = TokenCachePersistenceOptions(
                name=cache_name,
                allow_unencrypted_storage=allow_unencrypted_storage)
            creds = ChainedTokenCredential(
                ConvocationsCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    cache_persistence_options=options,
                    additionally_allowed_tenants=['*']),
                InteractiveBrowserCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    cache_persistence_options=options,
                )
            )
            if verbose:
                notice_end()
        upn, tenant_id = get_token_info(creds, verbose)
        kwargs['creds'] = creds
        kwargs.setdefault('upn', upn)
        kwargs.setdefault('tenant_id', tenant_id)
        return super().__call__(*args, **kwargs)
