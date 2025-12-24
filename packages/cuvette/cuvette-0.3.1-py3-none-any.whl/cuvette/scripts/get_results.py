import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from beaker import Beaker, BeakerExperiment
from tqdm import tqdm

from cuvette.utils.general import gather_experiments, get_default_user, ExperimentWithJobs

def download_job(job, output_dir):
    beaker = Beaker.from_env()

    beaker.dataset.fetch(
        dataset=job,
        target=f"{output_dir}/{job}",
        force=True,
        quiet=True,
        validate_checksum=True
    )

    return job

def get_results(author, workspace, limit, output_dir):
    experiments: List[ExperimentWithJobs] = gather_experiments(
        author_list=[author], workspace_name=workspace, limit=limit
    )
    print(f"Found {len(experiments)} experiments")

    jobs = []
    for experiment in experiments:
        for job in experiment.jobs:
            if job.result and job.result.beaker:
                jobs += [job.result.beaker]

    with ThreadPoolExecutor() as executor: # max_workers=32
        futures = [executor.submit(download_job, job, output_dir) for job in jobs]
        
        for future in tqdm(as_completed(futures), total=len(jobs)):
            try:
                future.result()
            except Exception as e:
                print(f"Error downloading job: {e}")

    print('Done!')

def main():
    parser = argparse.ArgumentParser(description="Analyze logs wtih ChatGPT.")
    parser.add_argument("-w", "--workspace", type=str, required=True, help="Beaker workspace name")
    parser.add_argument(
        "--author",
        "-a",
        type=str,
        default=get_default_user(),
        help="Author name to filter experiments by.",
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=100, help="Maximum number of experiments to check"
    )
    parser.add_argument(
        "-o", "--output-dir", type=str, default='workspace', help="The directory to output the results. Defaults to workspace/"
    )
    args = parser.parse_args()

    get_results(args.author, args.workspace, args.limit, args.output_dir)
