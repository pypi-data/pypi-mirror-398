import os
import os.path
from tempfile import NamedTemporaryFile
from raft.tasks import task


@task
def ecdsa_key_pair(ctx, name, directory='.', curve='secp256k1'):
    """
    creates an ecdsa key pair
    :param ctx:
    :param name: the name of the vert
    :param str curve: pick one of the available values from
        `openssl ecparam -list_curves`
    :param str directory: the directory in which the cert and key
        will be stored
    """
    key_path = os.path.join(directory, f'{name}.key')
    cert_path = os.path.join(directory, f'{name}.crt')
    ctx.run(
        f'openssl ecparam -name {curve} -genkey -noout '
        f' -out {key_path}')
    command = (
        f'openssl ec -in {key_path} -pubout >{cert_path}'
    )
    ctx.run(command)


@task
def ecdsa_self_signed_cert(ctx, name, directory='.', curve='secp256k1', days=3650):
    """
    creates an ecdsa key pair
    :param ctx:
    :param name: the name of the vert
    :param str curve: pick one of the available values from
        `openssl ecparam -list_curves`
    :param str directory: the directory in which the cert and key
        will be stored
    """
    key_path = os.path.join(directory, f'{name}.key')
    cert_path = os.path.join(directory, f'{name}.crt')
    ctx.run(
        f'openssl ecparam -name {curve} -genkey -noout '
        f' -out {key_path}')
    with NamedTemporaryFile('w') as f:
        f.write('\n'.join([
            '[req]',
            'distinguished_name = req_distinguished_name',
            'req_extensions = v3_req',
            'prompt = no',
            '[req_distinguished_name]',
            'C = US',
            f'CN = {name}',
            '[v3_req]',
            'keyUsage = keyEncipherment, dataEncipherment',
            'extendedKeyUsage = serverAuth, clientAuth',
        ]))
        f.flush()
        command = (
            f'openssl req -new -x509 -sha256'
            f' -out {cert_path}'
            f' -key {key_path}'
            f' -days {days}'
            f' -config {f.name}'
        )
        ctx.run(command)
        # command = (
        #     f'openssl x509 -req -days {days}'
        #     f' -in {csr_path} -signkey {key_path} -out {cert_path}'
        # )
        # ctx.run(command)
