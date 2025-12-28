from base64 import b64decode
import time
import json
from collections import defaultdict

from raft import task
from ...base.utils import print_table
from ...base.utils import notice, notice_end, notice_level
from ..base import AwsTask, yielder


@task(klass=AwsTask)
def rds_engine_versions(ctx, engine='', session=None, brief=False, profile=None, **kwargs):
    """
    shows all rds engine versions
    """
    notice_level(brief=brief)
    notice('getting engine versions')
    rds = session.client('rds')
    results = yielder(rds, 'describe_db_engine_versions', session=session, Engine=engine)
    notice_end()
    header = [ 'engine', 'version', 'desc' ]
    rows = []
    for x in results:
        rows.append([
            x['Engine'],
            x['EngineVersion'],
            x['DBEngineVersionDescription'],
        ])
    rows.sort(key=lambda lx: (lx[0], lx[1], lx[2]))
    print_table(header, rows)
    if not brief:
        print()


def instance_map(session, ec2_instances, st_name):
    from ..base import name_tag
    from ..ec2 import yield_instances
    notice('getting ec2 instance info')
    g = yield_instances(name=st_name, session=session)
    for x in g:
        name = name_tag(x)
        instance_id = x['InstanceId']
        ec2_instances[name][instance_id] = x
    notice_end()


@task(klass=AwsTask)
def rds_instances(ctx, name='', cluster=None, session=None, brief=False, profile=None, json_output=False, **kwargs):
    """
    shows all rds instances and their endpoints
    """
    notice_level(brief=brief)
    from ..base import name_tag
    from ..ec2 import yield_instances
    notice('getting instances')
    rds = session.client('rds')
    if cluster:
        instances = rds.describe_db_instances(Filters=[{
            'Name': 'db-cluster-id',
            'Values': [ cluster ],
        }])
    else:
        instances = rds.describe_db_instances()
    instances = instances['DBInstances']
    notice_end()
    name = name.lower()
    any_custom = False
    for x in instances:
        st_id = x['DBInstanceIdentifier']
        if name not in st_id.lower():
            continue
        if 'custom' in x['Engine']:
            any_custom = True
            break
    ec2_instances = {}
    if any_custom:
        ec2_instances = defaultdict(dict)
        instance_map(session, ec2_instances, 'db-')
        instance_map(session, ec2_instances, 'do-not-delete-rds-custom')
    header = [ 'name', 'engine', 'endpoint', 'status', ]
    rows = []
    for x in instances:
        st_id = x['DBInstanceIdentifier']
        engine = x['Engine']
        endpoint = x.get('Endpoint')
        if name not in st_id.lower():
            continue
        rows.append([
            st_id,
            f"{engine} {x['EngineVersion']}",
            f"{endpoint['Address']}:{endpoint['Port']}" if endpoint else '',
            x['DBInstanceStatus'],
        ])
    rows.sort(key=lambda lx: lx[0])
    print_table(header, rows)
    if not brief:
        print()
    if not any_custom:
        return
    header = [ 'name', 'id', 'ip', ]
    rows = []
    for x in instances:
        st_id = x['DBInstanceIdentifier']
        engine = x['Engine']

        if name not in st_id.lower():
            continue
        if 'custom' in engine:
            resource_id = x.get('DbiResourceId')
            if not resource_id:
                continue
            key = resource_id.lower()
            y = ec2_instances.get(key)
            y = y or ec2_instances.get(f'do-not-delete-rds-custom-{st_id.lower()}')
            for instance_id, instance in y.items():
                rows.append([
                    st_id,
                    instance_id,
                    instance['PrivateIpAddress'],
                ])
    rows.sort(key=lambda lx: lx[0])
    print_table(header, rows)
    if brief:
        if not json_output:
            for x in rows:
                print(x[2])
        else:
            rg = [ dict(zip(header, x)) for x in rows ]
            print(json.dumps(rg))


@task(klass=AwsTask)
def rds_rdp_password(ctx, name='', session=None, brief=False, profile=None, **kwargs):
    """
    shows all rds instances and their endpoints
    """
    notice_level(brief=brief)
    from ..base import name_tag
    from ..ec2 import yield_instances
    from Crypto.Cipher import PKCS1_v1_5
    from Crypto.PublicKey import RSA
    notice('getting instances')
    rds = session.client('rds')
    secrets = session.client('secretsmanager')
    ec2 = session.client('ec2')
    instances = rds.describe_db_instances(Filters=[{
        'Name': 'engine',
        'Values': [ 'custom-sqlserver-ee', ],
    }])
    instances = instances['DBInstances']
    notice_end()
    name = name.lower()
    matches = []
    for x in instances:
        st_id = x['DBInstanceIdentifier']
        if name not in st_id.lower():
            continue
        matches.append(x)
    header = [ 'password', 'id', 'name', 'private ip' ]
    rows = []
    for x in matches:
        st_id = x['DBInstanceIdentifier']
        notice(f'[{st_id}] looking up private key')
        secret_name = f'do-not-delete-rds-custom-rdp-privatekey-{st_id}'
        response = secrets.list_secrets(Filters=[{
            'Key': 'name',
            'Values': [ secret_name ],
        }])
        rg_secrets = response['SecretList']
        if not rg_secrets:
            notice_end(False)
            continue
        notice_end()
        secret_value = rg_secrets[0]
        arn = secret_value['ARN']
        notice('looking up private key')
        response = secrets.get_secret_value(SecretId=arn)
        key = response['SecretString']
        notice_end()
        notice('getting ec2 instance info')
        instance_name = f'do-not-delete-rds-custom-{st_id}'
        instances = list(yield_instances(name=instance_name, session=session))
        notice_end()
        for instance in instances:
            instance_id = instance['InstanceId']
            row = [
                st_id,
                instance_id,
                instance['PrivateIpAddress'],
            ]
            notice(f'[{instance_id}] getting password')
            response = ec2.get_password_data(InstanceId=instance_id)
            password_data = response['PasswordData']
            rsa_key = RSA.importKey(key.encode('utf-8'))
            cipher = PKCS1_v1_5.new(rsa_key)
            plaintext = cipher.decrypt(b64decode(password_data.encode('utf-8')), None)
            notice_end()
            rows.append([ plaintext.decode('utf-8') ] + row)
    rows.sort(key=lambda lx: lx[1])
    print_table(header, rows)

@task(klass=AwsTask)
def rds_clusters(ctx, name='', session=None, profile=None, **kwargs):
    """
    shows all rds instances and their endpoints
    """
    rds = session.client('rds')
    clusters = rds.describe_db_clusters()
    name = name.lower()
    clusters = clusters['DBClusters']
    header = [ 'name', 'endpoint', ]
    rows = []
    for x in clusters:
        cluster_name = x['DBClusterIdentifier']
        cluster_name = cluster_name.lower()
        if name in cluster_name:
            rows.append([
                x['DBClusterIdentifier'],
                x['Endpoint'],
            ])
    rows.sort(key=lambda lx: lx[0])
    print_table(header, rows)


@task(klass=AwsTask)
def sys_password(ctx, cluster_name, session=None, profile=None, **kwargs):
    """
    shows the sys password for an custom rds for oracle rac database
    """
    notice('connecting to rds')
    rds = session.client('rds')
    clusters = rds.describe_db_clusters(Filters=[{
        'Name': 'db-cluster-id',
        'Values': [ cluster_name ],
    }, {
        'Name': 'engine',
        'Values': [ 'custom-oracle-rac-ee' ],
    }])
    clusters = clusters['DBClusters']
    resource = None
    resource_id = None
    if clusters:
        notice_end()
        notice(cluster_name)
        cluster_name = cluster_name.lower()
        for x in clusters:
            st = x['DBClusterIdentifier'].lower()
            if cluster_name == st:
                resource = x
                resource_id = x['DbClusterResourceId']
                notice_end(resource_id)
                break
        if resource_id:
            notice('engine')
            engine = resource['Engine'].lower()
            notice_end(engine)
            secret_name = f'do-not-delete-rds-custom-{resource_id}-sys-'
    else:
        instances = rds.describe_db_instances(Filters=[{
            'Name': 'db-instance-id',
            'Values': [ cluster_name ],
        }, {
            'Name': 'engine',
            'Values': [ 'custom-oracle-ee' ],
        }])
        instances = instances['DBInstances']
        if instances:
            resource_id = instances[0]['DbiResourceId']
            notice_end(resource_id)
            secret_name = f'rds-custom!oracle-do-not-delete-{resource_id}'
        else:
            notice_end('not found')
            return

    notice('looking up sys password')
    sm = session.client('secretsmanager')
    fn = yielder(sm, 'list_secrets', session, Filters=[{
        'Key': 'name',
        'Values': [ secret_name ],
    }])
    notice_end()
    for x in fn:
        name = x['Name']
        if 'ssh' in name:
            continue
        response = sm.get_secret_value(SecretId=name)
        print(response['SecretString'])


@task(klass=AwsTask)
def rds_master_password(ctx, instance_name, session=None, profile=None, **kwargs):
    """
    shows the master password for an rds via secrets manager
    """
    notice('connecting to rds')
    rds = session.client('rds')
    clusters = rds.describe_db_instances()
    clusters = clusters['DBInstances']
    instance_name = instance_name.lower()
    resource = None
    resource_id = None
    for x in clusters:
        st = x['DBInstanceIdentifier'].lower()
        if instance_name == st:
            resource = x
            resource_id = x['DBInstanceIdentifier']
            break
    if not resource_id:
        return
    notice_end(resource_id)
    notice('is managed via secrets?')
    secret = resource.get('MasterUserSecret')
    if secret:
        notice_end()
    else:
        notice_end(False)
        return
    user = resource.get('MasterUsername')
    notice(f'{user} password')
    secret_name = secret['SecretArn']
    sm = session.client('secretsmanager')
    response = sm.get_secret_value(SecretId=secret_name)
    notice_end()
    password = response['SecretString']
    password = json.loads(password)
    password = password['password']
    print(password)


@task(klass=AwsTask)
def rds_ssh(ctx, name, session=None, profile=None, **kwargs):
    """
    sshes to a custom rds for oracle rac database
    """
    notice('connecting to rds')
    rds = session.client('rds')
    instances = rds.describe_db_instances(Filters=[{
        'Name': 'db-instance-id',
        'Values': [ name ],
    }])
    instances = instances['DBInstances']
    if instances:
        resource_id = instances[0]['DbiResourceId']
        notice_end(resource_id)
    else:
        notice_end('not found')
        return
    from convocations.aws.ec2 import instance_by_name
    from convocations.aws.ec2.ssh import download_secret
    x = instance_by_name(ctx, resource_id, session=session)
    key_name = x.key_name
    username = 'ec2-user'
    ip_address = x.private_ip_address
    notice('key name')
    notice_end(key_name)
    notice('ip address')
    notice_end(ip_address)
    with download_secret(session, x.key_name) as f:
        ssh_cmd = f'ssh -i {f.name} {username}@{ip_address}'
        notice_end(ssh_cmd)
        ctx.run(ssh_cmd, pty=True)
        return


@task(klass=AwsTask)
def download_rds_ssh_key(ctx, name, filename, session=None, **kwargs):
    """
    saves the ssh private key file to a specified filename
    """
    from convocations.aws.ec2 import instance_by_name, instance_by_ip
    from convocations.aws.ec2.ssh import download_secret
    if len(name.split('.')) != 4:
        notice('connecting to rds')
        rds = session.client('rds')
        instances = rds.describe_db_instances(Filters=[{
            'Name': 'db-instance-id',
            'Values': [ name ],
        }])
        instances = instances['DBInstances']
        if instances:
            resource_id = instances[0]['DbiResourceId']
            notice_end(resource_id)
        else:
            notice_end('not found')
            return
        x = instance_by_name(ctx, resource_id, session=session)
    else:
        x = instance_by_ip(ctx, name, session=session)
    key_name = x.key_name
    notice('key name')
    notice_end(key_name)
    with download_secret(session, x.key_name) as f:
        ctx.run(f'cp -f {f.name} {filename}')


@task(klass=AwsTask)
def delete_rac_cluster(ctx, name, session=None, **kwargs):
    """
    creates the staging oroms rds cluster and database instances
    """
    notice('connecting to rds')
    rds = session.client('rds')
    notice_end()
    notice('getting instances')
    instances = rds.describe_db_instances(Filters=[{
        'Name': 'db-cluster-id',
        'Values': [ name ]
    }])
    instances = instances['DBInstances']
    notice_end()
    for x in instances[1:]:
        st = x['DBInstanceIdentifier']
        notice(f'deleting {st}')
        rds.delete_db_instance(
            DBInstanceIdentifier=st,
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True,
        )
        time.sleep(5)
        notice_end()
    notice('deleting cluster')
    rds.delete_db_cluster(
        DBClusterIdentifier=name,
        SkipFinalSnapshot=True,
    )
    notice_end()
