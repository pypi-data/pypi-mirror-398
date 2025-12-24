from typing import List

import grpc

from beaker import Beaker, BeakerJobPriority
from beaker import beaker_pb2 as pb2
from beaker._service_client import RpcMethod
from beaker.exceptions import BeakerJobNotFound

from cuvette.utils.general import get_default_user


PRIORITY_MAP = {
    "low": BeakerJobPriority.low,
    "normal": BeakerJobPriority.normal,
    "high": BeakerJobPriority.high,
    "urgent": BeakerJobPriority.urgent,
}

def gather_experiments(
    beaker: Beaker, 
    author_list: List[str], 
    workspace_name: str, 
    limit: int = 2000) -> List[pb2.Workload]:
    """Gather all experiments from a workspace, filtered by author."""
    workspace = beaker.workspace.get(workspace_name)
    
    workloads = []
    for author in author_list:
        # Server-side filtering by author AND workspace - much faster!
        for workload in beaker.workload.list(
            workspace=workspace,
            author=author,  # Filter happens on server
            limit=limit - len(workloads),
        ):
            workloads.append(workload)
            if len(workloads) >= limit:
                break
        if len(workloads) >= limit:
            break
    
    print(f"Total experiments for authors {author_list}: {len(workloads)}")
    return workloads


def change_priority(author, workspace, priority, limit=5000):
    with Beaker.from_env() as beaker:
        workloads = gather_experiments(beaker, [author], workspace, limit)
        print(f"Found {len(workloads)} experiments")

        priority_enum = PRIORITY_MAP[priority]

        for i, workload in enumerate(workloads):
            experiment_id = workload.experiment.id
            
            # Get jobs from tasks
            for task in workload.experiment.tasks:
                for job in beaker.job.list(task=task, limit=10):  # Get recent jobs per task
                    try:
                        request = pb2.UpdateJobSourcePriorityRequest(
                            job_id=job.id,
                            priority=priority_enum.as_pb2(),
                        )
                        beaker.job.rpc_request(
                            RpcMethod[pb2.UpdateJobSourcePriorityResponse](
                                beaker.job.service.UpdateJobSourcePriority
                            ),
                            request,
                            exceptions_for_status={
                                grpc.StatusCode.NOT_FOUND: BeakerJobNotFound(job.id),
                            },
                        )
                    except Exception as e:
                        print(f"Failed to update priority for job {job.id}: {e}")

            print(f"({i+1}/{len(workloads)}) updated https://beaker.org/ex/{experiment_id})")

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--author",
        "-a",
        type=str,
        default=get_default_user(),
        help="Author name to filter experiments by.",
    )
    parser.add_argument("-w", "--workspace", type=str, required=True, help="Beaker workspace name")
    parser.add_argument(
        "-p",
        "--priority",
        type=str,
        required=True,
        choices=["low", "normal", "high", "urgent"],
        help="Priority level to set for jobs",
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=100, help="Maximum number of experiments to check"
    )
    args = parser.parse_args()

    change_priority(args.author, args.workspace, args.priority, args.limit)


if __name__ == "__main__":
    main()
