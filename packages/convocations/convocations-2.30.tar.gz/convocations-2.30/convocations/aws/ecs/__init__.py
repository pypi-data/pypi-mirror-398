from raft.collection import Collection
from .service_tasks import watch_service_deploy
from .task_tasks import list_tasks, task_logs, get_latest_revision



ecs_tasks = Collection()
ecs_tasks.add_task(task_logs)
ecs_tasks.add_task(get_latest_revision)
ecs_tasks.add_task(watch_service_deploy)
ecs_tasks.add_task(list_tasks)
