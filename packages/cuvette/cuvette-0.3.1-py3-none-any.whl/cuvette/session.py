import abc
import re
import random
import string
import subprocess
import time
from typing import Callable, Generator, Optional, Union

from typing import Optional
from beaker import (
    Beaker,
    BeakerTaskSpec,
    BeakerImageSource,
    BeakerResultSpec,
    BeakerDataMount,
    BeakerDataSource,
    BeakerEnvVar,
    BeakerConstraints,
    BeakerTaskContext,
    BeakerJobPriority,
)
from beaker.types import BeakerExperimentSpec, BeakerTaskResources, BeakerWorkloadStatus

from cuvette.utils.general import send_notification
from cuvette.constants.secrets import USER_ENV_SECRETS, USER_FILE_SECRETS
from cuvette.constants.quotes import HEADER_QUOTES

# SESSION_NAME = "👋davidh👋"

SESSION_NAME = "eval-debugging"
SESSION_WORKSPACE = "ai2/olmo-3-evals"
SESSION_PRIORITY = "high"
SESSION_BUDGET = "ai2/oe-base"

ENTRYPOINT = "/entrypoint.sh"

UPDATE_PORT_CMD = "bport {session_id}"


"""
Contains a experiment-based launcher and session-based launcher (legacy)
"""

class Launcher(abc.ABC):
    def __init__(
        self,
        cluster_name: Optional[str | list] = None,
        host_name: Optional[str | list] = None,
        num_gpus: int = 0,
    ):
        self.cluster_name = cluster_name
        self.host_name = host_name
        self.num_gpus = num_gpus

    def build_quick_start_command(
        self,
        cluster_name: Optional[str | list] = None,
        host_name: Optional[str | list] = None,
        num_gpus: int = 0,
    ) -> str:
        """Build the quick start command string"""
        gpu_flag = f" -g {num_gpus}" if num_gpus > 0 else ""
        cluster_flag = ""
        if cluster_name is not None:
            if not isinstance(cluster_name, list):
                cluster_name = [cluster_name]
            cluster_flag = f" -c {' '.join(cluster_name)}"
        host_flag = ""
        if host_name is not None:
            if not isinstance(host_name, list):
                host_name = [host_name]
            host_flag = f" -H {' '.join(host_name)}"
        return f"bl{cluster_flag}{host_flag}{gpu_flag}"

    def update_port(self, session_id):
        # Run the port update script
        port_process = subprocess.run(
            UPDATE_PORT_CMD.format(session_id=session_id),
            shell=True,
            executable="/bin/zsh",
            capture_output=True,
            text=True,
        )

        if port_process.returncode == 0:
            updated_notif = f"Session launched with {self.num_gpus} GPUs on {self.host_name}"
            send_notification("Beaker Launch", updated_notif)
            success = True
        else:
            error_notif = f"Port update failed ({session_id})"
            send_notification("Beaker Launch", error_notif)
            success = False

        return success

    @property
    def quick_start_command(self) -> str:
        """Return the quick start command string for display."""
        return self.build_quick_start_command(
            cluster_name=self.cluster_name,
            host_name=self.host_name,
            num_gpus=self.num_gpus,
        )

    @property
    @abc.abstractmethod
    def launch_command(self) -> Union[str, Callable[[], Generator[str, None, None]]]:
        """Return the launch command (shell string or Python callable)."""
        ...

    @abc.abstractmethod
    def on_complete(
        self, returncode: int, output_lines: list[str], session_id: str
    ) -> tuple[Optional[str], bool]:
        """Handle session/experiment completion."""
        ...


class SessionLauncher(Launcher):
    LAUNCH_COMMAND = """\
    beaker session create \
        --name {name} \
        {gpu_command} \
        {cluster_command} \
        {hostname_command} \
        --image beaker://{image} \
        --workspace {workspace} \
        --priority {priority} \
        --budget {budget} \
        --bare \
        --detach \
        --port 8000 --port 8001 --port 8080 --port 8888 \
        --workdir /oe-eval-default/davidh \
        --mount src=weka,ref=oe-eval-default,dst=/oe-eval-default \
        --mount src=weka,ref=oe-training-default,dst=/oe-training-default \
        --mount src=weka,ref=oe-adapt-default,dst=/oe-adapt-default \
        {user_file_secrets} \
        {user_env_secrets} \
        -- {entrypoint} \
    """

    def create_session_launch_command(
        self,
        cluster_name: Optional[str | list] = None,
        host_name: Optional[str | list] = None,
        num_gpus: int = 0,
        session_name: str = SESSION_NAME,
        workspace: str = SESSION_WORKSPACE,
        priority: str = SESSION_PRIORITY,
        command=[ENTRYPOINT],
        image="davidh/davidh-interactive"
    ) -> str:
        """Build the beaker session launch command"""
        gpu_command = ""
        if num_gpus > 0:
            gpu_command = f"--gpus {num_gpus}"

        cluster_command = ""
        if cluster_name is not None:
            if not isinstance(cluster_name, list):
                cluster_name = [cluster_name]
            for _cluster_name in cluster_name:
                cluster_command += f"--cluster {_cluster_name} "

        hostname_command = ""
        if host_name is not None:
            if not isinstance(host_name, list):
                host_name = [host_name]
            for _host_name in host_name:
                hostname_command += f"--hostname {_host_name} "

        user_file_secrets_str = ""
        dst_seen = set()
        for user_file_secret in USER_FILE_SECRETS:
            ref, dst = user_file_secret['name'], f"/root/{user_file_secret['path']}"
            
            # No duplicate destinations for mounts. Only keep the first
            if dst in dst_seen:
                continue
            dst_seen.add(dst)
            
            user_file_secrets_str += f"--mount src=secret,ref={ref},dst={dst} "
        
        user_env_secrets_str = ""
        for user_env_secret in USER_ENV_SECRETS:
            local_name, beaker_name = user_env_secret['env'], user_env_secret['name']
            user_env_secrets_str += f"--secret-env {local_name}={beaker_name} "

        assert len(command) == 1, f"Sessions must have 1 cmd: {command}"
        command = command[0]

        command = self.LAUNCH_COMMAND.format(
            name=session_name,
            workspace=workspace,
            priority=priority,
            gpu_command=gpu_command,
            cluster_command=cluster_command,
            hostname_command=hostname_command,
            user_file_secrets=user_file_secrets_str,
            user_env_secrets=user_env_secrets_str,
            budget=SESSION_BUDGET,
            image=image,
            entrypoint=command
        )
        command = command.replace("  ", " ")
        return command

    @property
    def launch_command(self) -> str:
        return self.create_session_launch_command(
            cluster_name=self.cluster_name,
            host_name=self.host_name,
            num_gpus=self.num_gpus,
        )

    def get_host_name(self, session_id):
        """Get the hostname for a session ID"""
        command = ["beaker", "session", "describe"]
        if session_id:
            command.append(session_id)

        result = subprocess.run(command, capture_output=True, text=True)

        match = re.search(r"[^\s]*\.reviz\.ai2\.in", result.stdout)

        return match.group(0) if match else None

    def on_complete(
        self, returncode: int, output_lines: list[str], session_id: str
    ) -> tuple[Optional[str], bool]:
        """Handle session launch completion and port update."""
        try:
            # Get the hostname for printing
            host_name = self.get_host_name(session_id)

            # Wait before connecting (or else the locking mechanism fails)
            time.sleep(2)

            success = self.update_port(session_id)
            return host_name, success
        except Exception as e:
            error_notif = f"Port update error: {str(e)}"
            send_notification("Beaker Launch", error_notif)
            return None, False


class ExperimentLauncher(Launcher):

    def __init__(
        self,
        cluster_name: Optional[str | list] = None,
        host_name: Optional[str | list] = None,
        num_gpus: int = 0,
    ):
        super().__init__(cluster_name, host_name, num_gpus)
        self._workload = None
        self._job = None

    def create_task_spec(
        self,
        num_gpus: int = 0,
        workspace: str = SESSION_WORKSPACE,
        priority: str = SESSION_PRIORITY,
        session_name: str = SESSION_NAME,
        cluster_name: Optional[str | list] = None,
        host_name: Optional[str | list] = None,
        command=[ENTRYPOINT],
        image="davidh/davidh-interactive"
    ):
        # WEKA Mounts
        datasets = [
            BeakerDataMount(
                mount_path="/oe-eval-default",
                source=BeakerDataSource(weka="oe-eval-default"),
            ),
            BeakerDataMount(
                mount_path="/oe-training-default",
                source=BeakerDataSource(weka="oe-training-default"),
            ),
            BeakerDataMount(
                mount_path="/oe-adapt-default",
                source=BeakerDataSource(weka="oe-adapt-default"),
            ),
        ]

        # User secrets mount (e.g. .ssh/id_rsa)
        dst_seen = set()
        for secret in USER_FILE_SECRETS:
            mount_path = f"/root/{secret['path']}"
            if mount_path in dst_seen:
                continue
            dst_seen.add(mount_path)
            datasets.append(
                BeakerDataMount(
                    mount_path=mount_path,
                    source=BeakerDataSource(secret=secret["name"]),
                )
            )

        # Beaker secrets mount (e.g. HF_TOKEN)
        env_vars = []
        for secret in USER_ENV_SECRETS:
            env_vars.append(
                BeakerEnvVar(
                    name=secret["env"],
                    secret=secret["name"],
                )
            )

        if cluster_name is not None and host_name is None:
            constraints = BeakerConstraints(cluster=cluster_name)
        elif host_name is not None and cluster_name is None:
            constraints = BeakerConstraints(hostname=host_name)
        else:
            raise ValueError("Exactly one of clusters or host_name must be specified (not both or neither)")

        match priority:
            case "high":
                priority_val = BeakerJobPriority.high
            case "normal":
                priority_val = BeakerJobPriority.normal
            case "low":
                priority_val = BeakerJobPriority.low
            case "urgent":
                priority_val = BeakerJobPriority.urgent
            case _:
                raise ValueError(f"Unknown priority value: {priority!r}")

        command = ["bash", "-lc", "source /root/.bashrc && exec /usr/sbin/sshd -D"]

        task = BeakerTaskSpec(
            name=session_name,
            image=BeakerImageSource(beaker=image),
            command=command,
            host_networking=True,
            result=BeakerResultSpec(path="/output"),
            datasets=datasets,
            env_vars=env_vars,
            constraints=constraints,
            context=BeakerTaskContext(
                priority=priority_val,
                preemptible=False,
            ),
            resources=BeakerTaskResources(gpu_count=num_gpus)
        )

        experiment = BeakerExperimentSpec(
            tasks=[task],
            # description=random.choice(HEADER_QUOTES),
            description="https://github.com/davidheineman/cuvette",
            budget=SESSION_BUDGET
        )

        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))

        with Beaker.from_env() as beaker:
            workload = beaker.experiment.create(
                spec=experiment, 
                name=session_name + "-" + suffix,
                workspace=workspace
            )

        return workload

    @property
    def launch_command(self) -> Callable[[], Generator[str, None, None]]:
        return self._job_launcher

    def _job_launcher(self) -> Generator[str, None, None]:
        yield f"Creating experiment with {self.num_gpus} GPUs..."
        self._workload = self.create_task_spec(
            cluster_name=self.cluster_name,
            host_name=self.host_name,
            num_gpus=self.num_gpus or 0,
        )

        with Beaker.from_env() as beaker:
            yield f"Staring job: {beaker.workload.url(self._workload)}"

            job = None
            while job is None:
                yield "Waiting for job to be scheduled..."
                job = beaker.workload.get_latest_job(self._workload)
                if job is None:
                    time.sleep(0.5)

            last_status = None
            while True:
                job = beaker.workload.get_latest_job(self._workload)
                if job is None:
                    time.sleep(0.5)
                    continue

                current_status = job.status.status

                if current_status != last_status:
                    status_name = BeakerWorkloadStatus(current_status).name
                    yield f"Status: {status_name}"
                    last_status = current_status

                if current_status == BeakerWorkloadStatus.running:
                    self._job = job
                    yield "Job started!"
                    break

                if current_status in (
                    BeakerWorkloadStatus.succeeded,
                    BeakerWorkloadStatus.failed,
                    BeakerWorkloadStatus.canceled,
                ):
                    self._job = job
                    yield f"Job ended with status: {BeakerWorkloadStatus(current_status).name}"
                    break

                time.sleep(0.5)

    def on_complete(
        self, returncode: int, output_lines: list[str], session_id: str
    ) -> tuple[Optional[str], bool]:
        """Handle experiment completion - job is already running at this point."""
        if self._job is None:
            return None, False
        hostname = getattr(self._job, "hostname", None)
        return hostname, True
