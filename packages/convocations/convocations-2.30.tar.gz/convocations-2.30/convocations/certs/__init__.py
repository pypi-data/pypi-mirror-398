from raft import Collection
from .validator import validate_chain
from .ed25519 import ed25519_self_signed_cert
from .ecdsa import ecdsa_key_pair, ecdsa_self_signed_cert


cert_tasks = Collection(
    validate_chain,
    ed25519_self_signed_cert,
    ecdsa_key_pair,
    ecdsa_self_signed_cert
)
