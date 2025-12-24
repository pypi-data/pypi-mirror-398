import argparse
from typing import Any, Dict, Iterator, List

from beaker import Beaker, BeakerSortOrder, BeakerWorkloadType
from beaker.beaker_pb2 import User
from rich.console import Console
from rich.table import Table

from cuvette.utils.general import get_default_user


def categorize_and_sort_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort jobs by date, with executions first, then sessions."""

    def sort_job_by_date(job):
        return job["start_date"] or ""

    queued_jobs = []
    executing_jobs = []
    queued_sessions = []
    executing_sessions = []

    for job in jobs:
        if job["kind"] == "Session":
            if job["start_date"] is None:
                queued_sessions.append(job)
            else:
                executing_sessions.append(job)
        else:
            if job["start_date"] is None:
                queued_jobs.append(job)
            else:
                executing_jobs.append(job)

    # Sort executing jobs/sessions by date
    executing_jobs.sort(key=sort_job_by_date)
    executing_sessions.sort(key=sort_job_by_date)

    return queued_jobs + executing_jobs + queued_sessions + executing_sessions


def get_priority_name(priority_value: int) -> str:
    """Convert protobuf priority enum to string name."""
    priority_names = {
        0: "unspecified",
        1: "low",
        2: "normal",
        3: "high",
        4: "urgent",
        5: "immediate",
    }
    return priority_names.get(priority_value, str(priority_value))


def list_workloads(
    beaker: Beaker,
    user: User,
    sessions_only: bool = False,
    limit: int | None = 10,
) -> Iterator:
    """gRPC is slow, so uses HTTPS for sessions+experiment data"""
    if sessions_only:
        workload_type = BeakerWorkloadType.environment
        
        workloads = beaker.workload.list(
            author=user,
            finalized=False,
            workload_type=workload_type,
            sort_order=BeakerSortOrder.descending,
            sort_field='created',
            limit=limit
        )

        for workload in workloads:
            yield workload
    else:
        WORKSPACE_FAST_LIMIT = 5

        # Limit to only the top workspaces
        workspaces = list(
            beaker.workspace.list(
                workload_author=user,
                sort_order=BeakerSortOrder.descending,
                sort_field="recent_workload_activity",
                limit=WORKSPACE_FAST_LIMIT,
            )
        )

        count = 0
        for ws in workspaces:
            # use the fast HTTP API
            query = {"order": "descending", "field": "created"}
            if limit is not None:
                query["limit"] = str(limit * 2)
            response = beaker.workspace.http_request(
                f"workspaces/{ws.id}/experiments",
                query=query,
            )
            data = response.json()
            for exp in data.get("data", []):
                # Filter: non-finalized
                jobs = exp.get("jobs", [])
                if not jobs or jobs[-1].get("status", {}).get("finalized") is not None:
                    continue
                
                yield exp
                count += 1
                if limit is not None and count >= limit:
                    return


def process_experiment_json(exp: Dict[str, Any], beaker: Beaker, node_cache: Dict[str, str]) -> Dict[str, Any] | None:
    """Process experiment JSON from HTTP API into job data."""
    jobs = exp.get("jobs", [])
    if not jobs:
        return None
    
    # Get the latest job
    job_data = jobs[-1]
    status = job_data.get("status", {})
    
    # Skip finalized jobs
    if status.get("finalized") is not None:
        return None
    
    # Get hostname from node if assigned
    hostname = ""
    node_id = job_data.get("node")
    if node_id:
        if node_id in node_cache:
            hostname = node_cache[node_id]
        else:
            try:
                node = beaker.node.get(node_id)
                hostname = node.hostname
                node_cache[node_id] = hostname
            except Exception:
                hostname = node_id
    
    # Get GPU count from limits
    limits = job_data.get("limits", {})
    gpu_count = str(limits.get("gpuCount", 0))
    
    # Get priority
    priority = job_data.get("priority", "normal")
    
    # Get start date
    start_date = None
    started_str = status.get("started")
    if started_str:
        from datetime import datetime
        try:
            start_date = datetime.fromisoformat(started_str.replace("Z", "+00:00"))
        except Exception:
            pass
    
    # Check if job is being canceled
    is_canceling = status.get("canceled") is not None
    
    return {
        "workload": exp.get("id"),
        "id": job_data.get("id"),
        "kind": "Experiment",
        "name": job_data.get("name", ""),
        "start_date": start_date,
        "hostname": hostname,
        "priority": priority,
        "port_mappings": None,  # Not available in HTTP API response
        "gpus": gpu_count,
        "is_canceling": is_canceling,
    }


def get_job_data(username: str, sessions_only: bool = True) -> List[Dict[str, Any]]:
    """Get job data for a user using the new Beaker API."""
    processed_jobs = []

    with Beaker.from_env() as beaker:
        # Get the user object for filtering
        user = beaker.user.get(username)

        workloads = list_workloads(
            beaker,
            user,
            sessions_only = sessions_only,
            limit = None,
        )
        workloads = list(workloads)

        # Cache for node lookups to avoid repeated API calls
        node_cache: Dict[str, str] = {}

        for workload in workloads:
            # Check if this is a dict (from HTTP API) or a workload object (from gRPC)
            if isinstance(workload, dict):
                # Process experiment JSON directly
                processed_job = process_experiment_json(workload, beaker, node_cache)
                if processed_job:
                    processed_jobs.append(processed_job)
                continue
            
            # Get the latest non-finalized job for this workload
            job = beaker.workload.get_latest_job(workload, finalized=False)
            if job is None:
                continue

            # Determine the workload kind (Experiment or Session)
            if beaker.workload.is_environment(workload):
                kind = "Session"
            else:
                kind = "Experiment"

            # Get hostname from node if assigned
            hostname = ""
            if job.assignment_details.HasField("node_id"):
                node_id = job.assignment_details.node_id
                if node_id in node_cache:
                    hostname = node_cache[node_id]
                else:
                    try:
                        node = beaker.node.get(node_id)
                        hostname = node.hostname
                        node_cache[node_id] = hostname
                    except Exception:
                        hostname = node_id  # Fallback to node_id if lookup fails

            # Get GPU count from resource assignment
            gpu_count = "0"
            if job.assignment_details.HasField("resource_assignment"):
                gpus = job.assignment_details.resource_assignment.gpus
                gpu_count = str(len(gpus))

            # Get priority from system details
            priority = get_priority_name(job.system_details.priority)

            # Get port mappings
            port_mappings = {}
            for mapping in job.assignment_details.port_mapping_assignment:
                port_mappings[mapping.container_port] = mapping.host_port

            # Get start date
            start_date = None
            if job.status.HasField("started"):
                start_date = job.status.started.ToDatetime()

            # Check if job is being canceled
            is_canceling = job.status.HasField("canceled")

            processed_job = {
                "workload": workload.experiment.id if beaker.workload.is_experiment(workload) else workload.environment.id,
                "id": job.id,
                "kind": kind,
                "name": job.name,
                "start_date": start_date,
                "hostname": hostname,
                "priority": priority,
                "port_mappings": port_mappings if port_mappings else None,
                "gpus": gpu_count,
                "is_canceling": is_canceling,
            }
            processed_jobs.append(processed_job)

    processed_jobs = categorize_and_sort_jobs(processed_jobs)
    return processed_jobs


def display_jobs(author: str, include_experiments: bool):
    """Display jobs in a formatted table."""
    processed_jobs = get_job_data(username=author, sessions_only=not include_experiments)

    console = Console()
    table = Table(header_style="bold", box=None)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Kind", style="magenta")
    table.add_column("Name", style="green")
    table.add_column("Start Date", style="white")
    table.add_column("Hostname", style="blue", overflow="fold")
    table.add_column("Priority", style="blue")
    table.add_column("GPUs", style="magenta")
    table.add_column("Port Mappings", style="white")

    for job in processed_jobs:
        port_map_str = ""
        if job["port_mappings"] is not None:
            port_map_str = " ".join(f"{k}->{v}" for k, v in job["port_mappings"].items())

        if job["is_canceling"]:
            continue  # Skip jobs being canceled

        if job["start_date"] is None:
            status_str = "[blue]Queued[/blue]"
        else:
            status_str = job["start_date"].strftime("%Y-%m-%d %H:%M:%S")

        table.add_row(
            job["id"],
            job["kind"],
            job["name"],
            status_str,
            job["hostname"],
            job["priority"],
            job["gpus"],
            port_map_str,
        )

    console.print(table)


def sessions():
    """Entry point for listing sessions only."""
    parser = argparse.ArgumentParser(
        description="List all running sessions on AI2 through Beaker."
    )
    parser.add_argument(
        "--author", "-a", type=str, default=get_default_user(), help="The username to process."
    )
    args = parser.parse_args()

    display_jobs(args.author, include_experiments=False)


def all():
    """Entry point for listing all jobs (sessions and experiments)."""
    parser = argparse.ArgumentParser(
        description="List all running jobs on AI2 through Beaker (for cleaning up those you are done with)."
    )
    parser.add_argument(
        "--author", "-a", type=str, default=get_default_user(), help="The username to process."
    )
    args = parser.parse_args()

    display_jobs(args.author, include_experiments=True)


if __name__ == "__main__":
    all()
