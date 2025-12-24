import time
from typing import List

from beaker import Beaker, BeakerExperiment
from beaker.exceptions import BeakerError

from cuvette.utils.general import gather_experiments, get_default_user, ExperimentWithJobs


def stop_jobs(author, workspace, limit=5000):
    beaker = Beaker.from_env()
    experiments: List[ExperimentWithJobs] = gather_experiments(
        [author],
        workspace_name=workspace,
        limit=limit,
    )
    print(f"Found {len(experiments)} failed experiments")

    for i, experiment in enumerate(experiments):
        try:
            workload = beaker.workload.get(experiment.id)
            beaker.workload.cancel(workload)
        except BeakerError as e:
            print(f"Failed to stop https://beaker.org/ex/{experiment.id}: {e}")
            continue

        print(f"({i+1}/{len(experiments)}) stopped https://beaker.org/ex/{experiment.id})")

        if (i + 1) % 200 == 0:
            print("Giving the Beaker API a 20s breather to prevent overloding and timeouts...")
            time.sleep(20)


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
        "-l", "--limit", type=int, default=100, help="Maximum number of experiments to check"
    )
    args = parser.parse_args()

    stop_jobs(args.author, args.workspace, args.limit)
