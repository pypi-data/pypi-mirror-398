import os
import os.path
from tempfile import NamedTemporaryFile
from raft.tasks import task


@task
def ed25519_self_signed_cert(
        ctx, names, days=365, directory='.', outfile=None):
    """
    creates a new self-signed ed25519 cert with the appropriate names as subjects
      * names should be specified as a comma separated list, with no spaces
        between the commas
      * the first `name` is used as the subject
      * outputs key to outfile.key, cert to outfile.crt, and csr to outfile.csr
      * if no outfile is specified, will use the subject as the outfile base
    :param ctx:
    :param names: the subject / alt names to use with the
    :param str curve: pick one of the available values from
        `openssl ecparam -list_curves`
    :param int days: number of days the cert should last, default is 365
    :param str directory: the directory in which the cert, key, and csr
        will be stored
    :param outfile:
    """
    names = names.split(',')
    outfile = outfile or names[0]
    key_path = os.path.join(directory, f'{outfile}.key')
    cert_path = os.path.join(directory, f'{outfile}.crt')
    csr_path = os.path.join(directory, f'{outfile}.csr')
    ctx.run(f'openssl genpkey -algorithm ED25519 >{key_path}')
    with NamedTemporaryFile('w') as f:
        f.write('\n'.join([
            '[req]',
            'distinguished_name = req_distinguished_name',
            'req_extensions = v3_req',
            'prompt = no',
            '[req_distinguished_name]',
            'C = US',
            f'CN = {names[0]}',
            '[v3_req]',
            'keyUsage = keyEncipherment, dataEncipherment',
            'extendedKeyUsage = serverAuth, clientAuth',
            'subjectAltName = @alt_names',
            '[alt_names]',
            ''
        ]))
        for i, x in enumerate(names, 1):
            f.write(f'DNS.{i} = {x}\n')
        f.flush()
        command = (
            f'openssl req -new'
            f' -out {csr_path}'
            f' -key {key_path}'
            f' -config {f.name}'
        )
        ctx.run(command)
        command = (
            f'openssl x509 -req -days {days}'
            f' -in {csr_path} -signkey {key_path} -out {cert_path}'
        )
        ctx.run(command)
