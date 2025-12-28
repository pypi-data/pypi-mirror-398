#!/usr/bin/env python3
import subprocess
import shlex
import threading
import time
import queue
import logging
import sys
import numpy as np

from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Any
from datetime import datetime, time as dt_time

logger = logging.getLogger(__name__)


class SSHJobScheduler:
    """
    Tiny 'low-key Slurm' using ssh to chip0x nodes, with multi-threaded probing.

    - One worker thread per host.
    - Each worker:
        * probes CPU on its host (remote psutil),
        * if CPU <= cpu_threshold: grabs a job from a shared queue,
          launches it via nohup in the background,
        * repeats until the queue is empty or max_jobs_per_host reached.

    `executable` can be python, C++/Geant4 binary, etc.
    Remote job logs always go to: <remote_workdir>/logs/job_<job_idx>.log

    Scheduler logs:
      - Always go to stdout
      - Also to scheduler.log next to this script (hidden from API)
    """

    _logging_initialized = False  # class-level flag

    def __init__(
        self,
        hosts: Sequence[str],
        remote_workdir: str,
        executable: str,
        script_path: Optional[str] = None,
        cpu_threshold: float = 40.0,
        extra_env_cmd: Optional[str] = None,
        ssh_timeout: float = 60.0,
        cpu_probe_interval: float = 0.0,
        busy_sleep: float = 10.0,
        max_jobs_per_host: int = 2,
        cooldown_after_launch: float = 30.0,
        allowed_hours: Optional[Tuple[int, int]] = None,
        time_window_sleep: float = 300.0,
    ) -> None:
        """
        hosts              : list of hostnames, e.g. ["chip01", "chip02", "chip03"]
        remote_workdir     : remote directory where jobs are run
        executable         : path to the program to run (Python, C++, etc.)
        script_path        : optional script path (for Python); for C++ set None
        cpu_threshold      : only take a job if CPU% <= this
        extra_env_cmd      : optional env setup (conda, Geant4 env script, etc.)
        ssh_timeout        : timeout for CPU probe ssh calls (s)
        cpu_probe_interval : psutil.cpu_percent(interval=...), e.g. 0.0 or 10.0
        busy_sleep         : seconds to sleep when host is busy or probe fails
        max_jobs_per_host  : max number of jobs this scheduler run can assign
                             to a single host
        cooldown_after_launch : seconds to sleep on that host after launching
                                a job (to let CPU ramp up)
        allowed_hours      : optional (start_hour, end_hour) in local time, 0–23.
                             If None, jobs are allowed any time of day.
                             Example: (0, 8)  -> only submit between 00:00–07:59.
                             Example: (22, 6) -> only submit from 22:00 through
                             05:59 (wraps around midnight).
        time_window_sleep  : seconds to sleep when outside allowed window before
                             checking again.
        """
        self.hosts = list(hosts)
        self.remote_workdir = remote_workdir
        self.executable = executable
        self.script_path = script_path
        self.cpu_threshold = cpu_threshold
        self.extra_env_cmd = extra_env_cmd
        self.ssh_timeout = ssh_timeout
        self.cpu_probe_interval = cpu_probe_interval
        self.busy_sleep = busy_sleep
        self.max_jobs_per_host = max_jobs_per_host
        self.cooldown_after_launch = cooldown_after_launch

        # Time-window control
        self.allowed_hours = allowed_hours
        self.time_window_sleep = time_window_sleep

        # Hidden default: python used for CPU probing
        self._probe_python = "/data9/MuographyVenv/g4_11/bin/python"

        # Configure logging once per process (first scheduler instance wins)
        if not SSHJobScheduler._logging_initialized:
            self._setup_logging()
            SSHJobScheduler._logging_initialized = True

    # ---------- logging setup ----------

    def _setup_logging(self) -> None:
        handlers = [logging.StreamHandler(sys.stdout)]

        script_dir = Path(__file__).resolve().parent
        log_path = script_dir / "scheduler.log"
        handlers.append(logging.FileHandler(log_path))

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=handlers,
        )

        logger.info("Scheduler logging to stdout and %s", log_path)

    # ---------- time window helpers ----------

    def _within_time_window(self) -> bool:
        """
        Return True if current local time is within allowed_hours.

        allowed_hours = (start_hour, end_hour) in [0, 23].
        If start < end:  simple range  [start, end)
        If start > end:  wraps midnight, e.g. (22, 6) -> [22:00, 24:00) ∪ [00:00, 06:00)
        If allowed_hours is None: always True.
        """
        if self.allowed_hours is None:
            return True

        start_h, end_h = self.allowed_hours
        now = datetime.now().time()

        start_t = dt_time(start_h, 0)
        end_t = dt_time(end_h, 0)

        if start_h == end_h:
            # degenerate: never allowed
            return False

        if start_h < end_h:
            return start_t <= now < end_t
        else:
            # wraps midnight
            return now >= start_t or now < end_t

    def set_allowed_time_window(self, start_hour: int, end_hour: int) -> None:
        """
        Public method to adjust time window after construction, if desired.
        """
        self.allowed_hours = (start_hour, end_hour)

    # ---------- CPU probe on one host ----------

    def _query_remote_cpu(self, host: str) -> Optional[float]:
        python_cmd = shlex.quote(self._probe_python)
        remote_cmd = f"""{python_cmd} - << 'EOF'
import psutil
print(psutil.cpu_percent(interval={self.cpu_probe_interval}))
EOF
"""
        logger.info("[%s] probing CPU...", host)
        try:
            result = subprocess.run(
                ["ssh", host, remote_cmd],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.ssh_timeout,
            )
        except subprocess.CalledProcessError as e:
            logger.warning("[%s] CPU probe failed: %s", host, e)
            if e.stderr:
                logger.warning("  stderr: %s", e.stderr.strip())
            return None
        except subprocess.TimeoutExpired:
            logger.warning("[%s] CPU probe timed out.", host)
            return None

        lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
        if not lines:
            logger.warning("[%s] CPU probe: no output.", host)
            return None

        try:
            cpu_val = float(lines[-1])
        except ValueError:
            logger.warning("[%s] CPU probe: could not parse '%s' as float.", host, lines[-1])
            return None

        logger.info("[%s] CPU ≈ %.1f%%", host, cpu_val)
        return cpu_val

    # ---------- job launching ----------

    def _build_remote_job_command(self, extra_args: Optional[Sequence[Any]]) -> str:
        parts: List[str] = []
        parts.append(f"cd {shlex.quote(self.remote_workdir)}")
        if self.extra_env_cmd:
            parts.append(self.extra_env_cmd)

        if self.script_path:
            cmd = f"{shlex.quote(self.executable)} {shlex.quote(self.script_path)}"
        else:
            cmd = shlex.quote(self.executable)

        if extra_args:
            arg_str = " ".join(shlex.quote(str(a)) for a in extra_args)
            cmd = f"{cmd} {arg_str}"

        parts.append(cmd)
        return " && ".join(parts)

    def _launch_on_host(
        self,
        host: str,
        extra_args: Sequence[Any],
        log_file: str,
    ) -> None:
        base_cmd = self._build_remote_job_command(extra_args)

        # ensure logs/ exists on the remote side, then nohup
        remote_cmd = (
            f"cd {shlex.quote(self.remote_workdir)} && "
            f"mkdir -p logs && "
            f"nohup sh -c {shlex.quote(base_cmd)} "
            f"> {shlex.quote(log_file)} 2>&1 </dev/null &"
        )

        logger.info("[%s] launching job (background): %s", host, remote_cmd)

        subprocess.Popen(
            ["ssh", host, remote_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # ---------- per-host worker ----------

    def _host_worker(
        self,
        host: str,
        jobs_q: "queue.Queue[Tuple[int, Sequence[Any]]]",
        results: List[Optional[str]],
    ) -> None:
        launched = 0

        while True:
            if jobs_q.empty():
                break

            if launched >= self.max_jobs_per_host:
                logger.info(
                    "[%s] reached max_jobs_per_host=%d, worker exiting.",
                    host, self.max_jobs_per_host,
                )
                break

            # --- respect submission time window ---
            if not self._within_time_window():
                logger.info(
                    "[%s] outside allowed submission window %s, sleeping %.1fs",
                    host, self.allowed_hours, self.time_window_sleep,
                )
                time.sleep(self.time_window_sleep)
                continue

            cpu = self._query_remote_cpu(host)
            if cpu is None:
                logger.info("[%s] probe failed, sleeping %.1fs", host, self.busy_sleep)
                time.sleep(self.busy_sleep)
                continue

            if cpu > self.cpu_threshold:
                logger.info(
                    "[%s] busy (%.1f%% > %.1f%%), sleeping %.1fs",
                    host, cpu, self.cpu_threshold, self.busy_sleep,
                )
                time.sleep(self.busy_sleep)
                continue

            try:
                job_idx, job_args = jobs_q.get_nowait()
            except queue.Empty:
                break

            log_file = f"logs/job_{job_idx}.log"
            logger.info("[%s] picked job %d with args=%s", host, job_idx, job_args)
            self._launch_on_host(host, extra_args=job_args, log_file=log_file)
            results[job_idx] = host
            launched += 1

            # cooldown so CPU can ramp before we consider another job on this host
            logger.info(
                "[%s] cooldown %.1fs after launching job %d",
                host, self.cooldown_after_launch, job_idx,
            )
            time.sleep(self.cooldown_after_launch)

        logger.info("[%s] worker exiting.", host)

    # ---------- public API ----------

    def dispatch_many_from_columns(
        self,
        *arg_columns: Sequence[Any],
    ) -> List[Tuple[int, Optional[str]]]:
        """
        arg_columns: each is a list/array of same length.
        e.g. thicknesses, energies, etc.

        Returns list of (job_index, host_name or None).
        """
        if not arg_columns:
            raise ValueError("dispatch_many_from_columns: need at least one arg column.")

        lengths = [len(col) for col in arg_columns]
        if len(set(lengths)) != 1:
            raise ValueError(f"All arg columns must have same length, got {lengths}")

        num_jobs = lengths[0]
        logger.info(
            "[dispatcher] preparing %d jobs across %d hosts with %d positional args each.",
            num_jobs, len(self.hosts), len(arg_columns),
        )

        jobs_q: "queue.Queue[Tuple[int, Sequence[Any]]]" = queue.Queue()
        for idx in range(num_jobs):
            job_args = [col[idx] for col in arg_columns]
            jobs_q.put((idx, job_args))

        results: List[Optional[str]] = [None] * num_jobs

        threads: List[threading.Thread] = []
        for host in self.hosts:
            t = threading.Thread(
                target=self._host_worker,
                args=(host, jobs_q, results),
                daemon=True,
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        logger.info("[dispatcher] all workers finished.")
        return [(idx, results[idx]) for idx in range(num_jobs)]


if __name__ == "__main__":
    # Example: Python job using your venv as main executable & hidden probe python
    scheduler = SSHJobScheduler(
        hosts=["chip03", "chip04", "chip05", "chip06", "chip07", "chip08"],
        remote_workdir="/data9/MuographyPython/slab_ET_scan",
        executable="/data9/MuographyVenv/g4_11/bin/python",
        script_path="/data9/MuographyPython/slab_ET_scan/test_script.py",
        cpu_threshold=50.0,
        extra_env_cmd=None,
        ssh_timeout=40.0,
        cpu_probe_interval=10.0,   # average CPU over 10 s per probe
        busy_sleep=10.0,
        max_jobs_per_host=2,       # ramp protection: at most 2 jobs per host
        cooldown_after_launch=30.0,
        allowed_hours=(0, 8),      # only submit jobs between 00:00–07:59 (local time)
        time_window_sleep=600.0,   # re-check every 10 minutes if outside window
    )

    results = scheduler.dispatch_many_from_columns(
        np.arange(0, 20, 1),  # arg0
        np.arange(0, 20, 1),  # arg1
    )

    logger.info("Dispatch results: %s", results)
