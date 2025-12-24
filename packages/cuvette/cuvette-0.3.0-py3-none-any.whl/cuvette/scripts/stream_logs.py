import argparse
import sys

from beaker import Beaker, BeakerJob
from beaker.exceptions import BeakerJobNotFound


def stream_experiment_logs(job_id: str, do_stream: bool, return_logs: bool = False):
    beaker = Beaker.from_env()

    try:
        job: BeakerJob = beaker.job.get(job_id)

        if job.execution is None:
            if job.assignment_details.HasField("environment_id"):
                raise ValueError("Job is a session. Please provide an execution job.")
            raise RuntimeError(job)

        experiment_id = job.execution.experiment
    except BeakerJobNotFound:
        print(f"Job {job_id} not found, using {job_id} as an experiment ID...")
        experiment_id = job_id

    workload = beaker.workload.get(experiment_id)
    
    # Get tasks from the experiment
    experiment = workload.experiment
    tasks = list(experiment.tasks)
    
    if len(tasks) > 1:
        # If multiple tasks, use the first one (replica 0)
        task = tasks[0]
        print(f'Multiple tasks found! Using task: "{task.id}"...')
    else:
        task = tasks[0] if tasks else None
    
    # Get the latest job for this task
    if task is None:
        raise ValueError(f"No tasks found for experiment {experiment_id}")
    
    job: BeakerJob | None = beaker.workload.get_latest_job(workload, task=task)
    if job is None:
        raise ValueError(f"No jobs found for experiment {experiment_id}")

    try:
        if do_stream:
            # Stream logs from the job
            for job_log in beaker.job.logs(job, follow=True):
                log_line = job_log.message.decode("utf-8", errors="replace").rstrip()
                print(log_line)
                sys.stdout.flush()
        else:
            # Get all logs from the job
            log_stream = beaker.job.logs(job)

            logs = ""
            for job_log in log_stream:
                logs += job_log.message.decode("utf-8", errors="replace").rstrip()
                logs += "\n"

            if return_logs:
                return logs

            print(logs)
            sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nLog streaming interrupted by user")
    except Exception as e:
        print(f"Error streaming logs: {e}")


def main():
    parser = argparse.ArgumentParser(description="Stream logs from a Beaker job")
    parser.add_argument("-j", "--job_id", help="The ID or name of the Beaker job", required=True)
    parser.add_argument(
        "-s",
        "--stream",
        help="The ID or name of the Beaker job",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    stream_experiment_logs(args.job_id, do_stream=args.stream)


def logs():
    parser = argparse.ArgumentParser(description="Get logs from a Beaker job")
    parser.add_argument("job_id", help="The ID or name of the Beaker job")

    args = parser.parse_args()

    stream_experiment_logs(args.job_id, do_stream=False)


def stream():
    parser = argparse.ArgumentParser(description="Stream logs from a Beaker job")
    parser.add_argument("job_id", help="The ID or name of the Beaker job")

    args = parser.parse_args()

    stream_experiment_logs(args.job_id, do_stream=True)
