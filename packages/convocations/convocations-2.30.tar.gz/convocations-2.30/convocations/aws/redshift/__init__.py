from raft.collection import Collection
from .clusters import redshift_clusters


redshift_tasks = Collection(
    redshift_clusters,
)
