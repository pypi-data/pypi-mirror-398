import os
import subprocess
from typing import List

from beaker import Beaker, BeakerExperiment, BeakerJob, BeakerWorkloadType


class ExperimentWithJobs:
    """Wrapper class to attach jobs to an experiment object (exists because Beaker's protobuf is immutable)"""
    def __init__(self, experiment: BeakerExperiment, jobs: List[BeakerJob]):
        self._experiment = experiment
        self.jobs = jobs
    
    def __getattr__(self, name):
        # Delegate all other attribute access to the underlying experiment
        return getattr(self._experiment, name)
    
    @property
    def id(self):
        return self._experiment.id
    
    @property
    def name(self):
        # Try to get name from experiment, fallback to id if not available
        if hasattr(self._experiment, 'name'):
            return self._experiment.name
        return self._experiment.id


def run_command(cmd, shell=True):
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_default_user():
    beaker: Beaker = Beaker.from_env()
    user = beaker.user_name
    return user


def send_notification(title, message):
    """Send a notification on MacOS"""
    os.system(f"""osascript -e 'display notification "{message}" with title "{title}"' """)


def gather_experiments(author_list, workspace_name, limit=2000) -> List[ExperimentWithJobs]:
    """Gather all experiments from a workspace, filtered by author."""
    beaker = Beaker.from_env()
    experiments = []

    # bookkeeping
    num_author_exps = {}
    for author in author_list:
        num_author_exps[author] = 0

    print(f'Pulling experiments from "{workspace_name}" for author(s) {author_list}...')
    
    # Get workspace object
    workspace = beaker.workspace.get(workspace_name)
    
    # Get user objects for filtering
    user_objects = {}
    for author in author_list:
        user_objects[author] = beaker.user.get(author)
    
    # Process each author separately since workload.list can only filter by one author at a time
    # Track which author each workload belongs to
    workload_to_author = {}
    all_workloads = []
    for author in author_list:
        user = user_objects[author]
        # List workloads (experiments) from the workspace for this author
        author_workloads = list(
            beaker.workload.list(
                workspace=workspace,
                author=user,
                workload_type=BeakerWorkloadType.experiment,
                limit=limit,
            )
        )
        for workload in author_workloads:
            workload_id = workload.experiment.id if beaker.workload.is_experiment(workload) else workload.environment.id
            if workload_id not in workload_to_author:
                workload_to_author[workload_id] = author
                all_workloads.append(workload)
    
    for workload in all_workloads:
        # Check if this workload is an experiment
        if not beaker.workload.is_experiment(workload):
            continue
        
        workload_id = workload.experiment.id
        author_name = workload_to_author.get(workload_id, author_list[0] if author_list else "unknown")
        
        # Get the experiment object from the workload
        experiment = workload.experiment
        
        # Fetch jobs for this experiment by getting jobs for each task
        # Jobs are associated with tasks, not directly with experiments
        jobs = []
        for task in experiment.tasks:
            task_jobs = list(beaker.job.list(task=task))
            jobs.extend(task_jobs)
        
        # Wrap the experiment with jobs since we can't modify protobuf fields directly
        experiment_with_jobs = ExperimentWithJobs(experiment, jobs)
        experiments.append(experiment_with_jobs)
        num_author_exps[author_name] += 1
        
        if len(experiments) >= limit:
            break

    print(f"Total experiments for authors {author_list}: {len(experiments)}")
    for author, count in num_author_exps.items():
        print(f"Author {author} had {count} experiments")
    return experiments
