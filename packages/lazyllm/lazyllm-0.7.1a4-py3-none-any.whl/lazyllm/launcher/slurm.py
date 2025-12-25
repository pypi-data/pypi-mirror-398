import re
import time
import subprocess
from queue import Queue
from collections import defaultdict

import lazyllm
from lazyllm import final
from .base import LazyLLMLaunchersBase, Job, Status

lazyllm.config.add('partition', str, 'your_part', 'SLURM_PART',
                   description='The default Slurm partition to use if no partition is specified.')


@final
class SlurmLauncher(LazyLLMLaunchersBase):
    """This class is a subclass of ``LazyLLMLaunchersBase`` and acts as a Slurm launcher.

Specifically, it provides methods to start and configure Slurm jobs, including specifying parameters such as the partition, number of nodes, number of processes, number of GPUs, and timeout settings.

Args:
    partition (str): The Slurm partition to use. Defaults to ``None``, in which case the default partition in ``lazyllm.config['partition']`` will be used.
                     This configuration can be enabled by setting environment variables, such as ``export LAZYLLM_SLURM_PART=a100``.
    nnode (int): The number of nodes to use. Defaults to ``1``.
    nproc (int): The number of processes per node. Defaults to ``1``.
    ngpus (int): The number of GPUs per node. Defaults to ``None``, meaning no GPUs will be used.
    timeout (int): The timeout for the job in seconds. Defaults to ``None``, in which case no timeout will be set.
    sync (bool): Whether to execute the job synchronously. Defaults to ``True``, otherwise it will be executed asynchronously.
    **kwargs: Extra keyword arguments, including:
        - num_can_use_nodes (int): The maximum number of nodes that can be used. Defaults to ``5``.


Examples:
    >>> import lazyllm
    >>> launcher = lazyllm.launchers.slurm(partition='partition_name', nnode=1, nproc=1, ngpus=1, sync=False)
    """
    # In order to obtain the jobid to monitor and terminate the job more
    # conveniently, only one srun command is allowed in one Job
    all_processes = defaultdict(list)
    count = 0

    @final
    class Job(Job):
        """Generic task scheduling executor.
This class wraps a task that is launched via a launcher, with features like command fixing, output handling, sync control, and return value capturing.

Args:
    cmd (LazyLLMCMD): The command object to be executed.
    launcher (Any): Launcher instance responsible for task dispatching.
    sync (bool): Whether the task should run synchronously. Defaults to True.
"""
        def __init__(self, cmd, launcher, *, sync=True, **kw):
            super(__class__, self).__init__(cmd, launcher, sync=sync)
            self.name = self._generate_name()

        def _wrap_cmd(self, cmd):
            # Assemble the order
            slurm_cmd = f'srun -p {self._launcher.partition} -N {self._launcher.nnode} --job-name={self.name}'
            if self._launcher.nproc:
                slurm_cmd += f' -n{self._launcher.nproc}'
            if self._launcher.timeout:
                slurm_cmd += f' -t {self._launcher.timeout}'
            if self._launcher.ngpus:
                slurm_cmd += f' --gres=gpu:{self._launcher.ngpus}'
            return f'{slurm_cmd} bash -c "{cmd}"'

        def _get_jobid(self):
            time.sleep(0.5)  # Wait for cmd to be stably submitted to slurm
            id_str = subprocess.check_output(['squeue', '--name=' + self.name, '--noheader'])
            if id_str:
                id_list = id_str.decode().strip().split()
                self.jobid = id_list[0]

        def get_jobip(self):
            id_str = subprocess.check_output(['squeue', '--name=' + self.name, '--noheader'])
            id_list = id_str.decode().strip().split()
            self.ip = id_list[10]
            return self.ip

        def stop(self):
            if self.jobid:
                cmd = f'scancel --quiet {self.jobid}'
                subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 encoding='utf-8', executable='/bin/bash')
                self.jobid = None

            if self.ps:
                self.ps.terminate()
                self.queue = Queue()
                self.output_thread_event.set()
                self.output_thread.join()

        def wait(self):
            if self.ps:
                self.ps.wait()

        @property
        def status(self):
            # lookup job
            if self.jobid:
                jobinfo = subprocess.check_output(['scontrol', 'show', 'job', str(self.jobid)])
                job_state = None
                job_state = None
                for line in jobinfo.decode().split('\n'):
                    if 'JobState' in line:
                        job_state = line.strip().split()[0].split('=')[1].strip().lower()
                        if job_state == 'running':
                            return Status.Running
                        elif job_state == 'tbsubmitted':
                            return Status.TBSubmitted
                        elif job_state == 'inqueue':
                            return Status.InQueue
                        elif job_state == 'pending':
                            return Status.Pending
                        elif job_state == 'done':
                            return Status.Done
                        elif job_state == 'cancelled':
                            return Status.Cancelled
                        else:
                            return Status.Failed
            else:
                return Status.Failed

    # TODO(wangzhihong): support configs; None -> lookup config
    def __init__(self, partition=None, nnode=1, nproc=1, ngpus=None, timeout=None, *, sync=True, **kwargs):
        super(__class__, self).__init__()
        # TODO: global config
        self.partition = partition if partition else lazyllm.config['partition']
        self.nnode, self.nproc, self.ngpus, self.timeout = nnode, nproc, ngpus, timeout
        self.sync = sync
        self.num_can_use_nodes = kwargs.get('num_can_use_nodes', 5)

    def makejob(self, cmd):
        """Creates and returns a SlurmLauncher.Job object.

Args:
    cmd: The command string to execute.

**Returns:**

- SlurmLauncher.Job: A configured Slurm job object.
"""
        return SlurmLauncher.Job(cmd, launcher=self, sync=self.sync)

    def _add_dict(self, node_ip, used_gpus, node_dict):
        if node_ip not in node_dict:
            node_dict[node_ip] = 8 - used_gpus
        else:
            node_dict[node_ip] -= used_gpus

    def _expand_nodelist(self, nodes_str):
        pattern = r'\[(.*?)\]'
        matches = re.search(pattern, nodes_str)
        result = []
        if matches:
            nums = matches.group(1).split(',')
            base = nodes_str.split('[')[0]
            result = [base + str(x) for x in nums]
        return result

    def get_idle_nodes(self, partion=None):
        """
        Obtain the current number of available nodes based on the available number of GPUs.
        Return a dictionary with node IP as the key and the number of available GPUs as the value.
        """
        if not partion:
            partion = self.partition
        num_can_use_nodes = self.num_can_use_nodes

        # Query the number of available GPUs for applied nodes
        nodesinfo = subprocess.check_output(['squeue', '-p', partion, '--noheader'])
        node_dict = dict()

        for line in nodesinfo.decode().split('\n'):
            if 'gpu:' in line:
                node_info = line.strip().split()
                num_nodes = int(node_info[-3])
                num_gpus = int(node_info[-2].split(':')[-1])
                node_list = node_info[-1]
                if num_nodes == 1:
                    self._add_dict(node_list, num_gpus, node_dict)
                else:
                    avg_gpus = int(num_gpus / num_nodes)
                    result = self._expand_nodelist(node_list)
                    for x in result:
                        self._add_dict(x, avg_gpus, node_dict)

        # Obtain all available idle nodes in the specified partition
        idle_nodes = []
        nodesinfo = subprocess.check_output(['sinfo', '-p', partion, '--noheader'])
        for line in nodesinfo.decode().split('\n'):
            if 'idle' in line:
                node_info = line.strip().split()
                num_nodes = int(node_info[-3])
                node_list = node_info[-1]
                if num_nodes == 1:
                    idle_nodes.append(node_list)
                else:
                    idle_nodes += self._expand_nodelist(node_list)

        # Add idle nodes under resource constraints
        num_allocated_nodes = len(node_dict)
        num_append_nodes = num_can_use_nodes - num_allocated_nodes

        for i, node_ip in enumerate(idle_nodes):
            if i + 1 <= num_append_nodes:
                node_dict[node_ip] = 8

        # Remove nodes with depleted GPUs
        node_dict = {k: v for k, v in node_dict.items() if v != 0}
        return node_dict

    def launch(self, job) -> None:
        """Launches a Slurm job and manages its execution.

This method starts the specified Slurm job and decides whether to wait for job completion based on the sync setting. If set to synchronous execution, it continuously monitors the job status until completion, then stops the job.

Args:
    job: The SlurmLauncher.Job object to launch.

**Returns:**

- The return value of the job.

Raises:
    AssertionError: If the provided job is not a SlurmLauncher.Job type.
"""
        assert isinstance(job, SlurmLauncher.Job), 'Slurm launcher only support cmd'
        job.start()
        if self.sync:
            while job.status == Status.Running:
                time.sleep(10)
            job.stop()
        return job.return_value
