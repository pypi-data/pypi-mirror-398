from raft.collection import Collection
from .codebuild import codebuild_collection
from .codebuild import global_collection as global_codebuild
from . import codebuild, rds
from . import codedeploy
from . import ec2
from . import elb
from . import iam
from . import ami_helpers
from . import open_id
from .keypairs import new_key_pair, show_public_key
from .cfn import import_instance
from .cfn import import_route_table
from .cfn import import_security_group
from .cfn import import_subnet
from .cfn import import_vpc
from .cfn import import_ecs_service
from .cfn import import_code_pipeline
from .cfn import stack_commands
from . import mgn
from . import transit_gateway
from . import ram
from .ssm import runners as ssm_runners
from .ssm.fleet_manager import ssm_documents
from .ssm.runners import ssm_parameters
from . import s3
from . import organizations
from . import route53
from . import vpc_peering
from .route53 import zone_parser
from .route53.compare import compare_zones
from . import reservations
from .ec2 import routing
from .ec2 import ssh
from .ec2.volumes import gp2_to_gp3
from .ec2.volumes import available_volumes
from .ec2 import networking as ec2_networking
from .ip_ranges import ip_ranges, ip_range_services
from .health import ec2_events
from . import efs
from .ssm.fleet_manager import managed_instances, unmanaged_instances, start_shell
from .workspaces.workspace_tasks import workspaces
from .redshift.clusters import redshift_clusters
from .ecs import ecs_tasks


ns = Collection()
ns.add_collection(codebuild_collection, 'codebuild')
ns.add_collection(ecs_tasks, 'ecs')
ns.add_tasks(codebuild.build)
ns.add_tasks(codedeploy)
ns.add_tasks(ec2)
ns.add_tasks(ec2_networking)
ns.add_tasks(elb)
ns.add_tasks(iam)
ns.add_tasks(import_instance)
ns.add_tasks(import_route_table)
ns.add_tasks(import_security_group)
ns.add_tasks(import_subnet)
ns.add_tasks(import_vpc)
ns.add_tasks(import_ecs_service)
ns.add_tasks(mgn)
ns.add_tasks(stack_commands)
ns.add_tasks(transit_gateway)
ns.add_tasks(open_id)
ns.add_tasks(ami_helpers)
ns.add_task(new_key_pair)
ns.add_task(show_public_key)
ns.add_task(ssm_runners.run_posh)
ns.add_tasks(ram)
ns.add_tasks(s3)
ns.add_tasks(organizations)
ns.add_tasks(route53)
ns.add_tasks(zone_parser)
ns.add_tasks(vpc_peering)
ns.add_tasks(import_code_pipeline)
ns.add_tasks(rds)
ns.add_tasks(reservations)
ns.add_tasks(routing)
ns.add_tasks(ssh)
ns.add_task(ip_ranges)
ns.add_task(ip_range_services)
ns.add_task(ec2_events)
ns.add_task(ssm_parameters)
ns.add_tasks(efs)
ns.add_task(gp2_to_gp3)
ns.add_task(available_volumes)
ns.add_task(managed_instances)
ns.add_task(unmanaged_instances)
ns.add_task(workspaces)
ns.add_task(start_shell)
ns.add_task(ssm_documents)
ns.add_task(redshift_clusters)
ns.add_task(compare_zones)
