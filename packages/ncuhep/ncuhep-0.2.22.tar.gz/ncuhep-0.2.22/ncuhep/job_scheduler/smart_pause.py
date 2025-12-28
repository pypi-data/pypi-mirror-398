"""
smart_pause.py  —  small helper library for being nice on shared CPU nodes.

Provides a SmartPause class that can:
    - scan other users' CPU usage
    - wait for a "good" slot before launching heavy jobs
    - suggest a thread count based on current load
"""

from __future__ import annotations

import time
import getpass
from typing import List, Tuple, Optional

import psutil

# (cpu_percent, pid, username, process_name)
ProcessInfo = Tuple[float, int, str, str]


class SmartPause:
    def __init__(
        self,
        base_threads: Optional[int] = None,
        max_total_cpu: float = 90.0,
        max_other_cores: Optional[float] = 8.0,
        min_sleep: float = 20.0,
        max_checks: int = 999_999,
        min_threads: int = 1,
        max_threads: Optional[int] = None,
        headroom: float = 0.95,
        min_cpu_per_proc: float = 20.0,
        verbose: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        base_threads : int or None
            Your "nominal" max thread count (e.g. what you'd normally pass to -t).
            If None, defaults to psutil.cpu_count(logical=True).
        max_total_cpu : float
            Do not start a new job if total CPU% is above this.
        max_other_cores : float or None
            Approximate max number of cores other users are allowed to burn
            before we wait. None disables this check (only total CPU is used).
        min_sleep : float
            Seconds to sleep between checks in wait_for_good_slot().
        max_checks : int
            Maximum number of wait iterations before giving up.
        min_threads : int
            Minimum thread count suggest_thread_count() will return.
        max_threads : int or None
            Maximum thread count suggest_thread_count() will return.
            Defaults to base_threads.
        headroom : float
            Fraction of free cores to use (e.g. 0.95 -> 95% of free cores).
        min_cpu_per_proc : float
            Only processes with CPU% >= this are counted as "heavy".
        verbose : bool
            If True, prints diagnostics.
        """
        self.n_cpus = psutil.cpu_count(logical=True) or 1

        if base_threads is None:
            base_threads = self.n_cpus
        if max_threads is None:
            max_threads = base_threads

        self.base_threads = base_threads
        self.max_total_cpu = max_total_cpu
        self.max_other_cores = max_other_cores
        self.min_sleep = min_sleep
        self.max_checks = max_checks
        self.min_threads = max(1, min_threads)
        self.max_threads = max_threads
        self.headroom = headroom
        self.min_cpu_per_proc = min_cpu_per_proc
        self.verbose = verbose

    # ------------ core helpers ------------

    def scan_other_users_cpu(
        self,
        min_cpu_per_proc: Optional[float] = None,
        sample_interval: float = 0.5,
    ) -> Tuple[float, List[ProcessInfo]]:
        """
        Look for CPU-heavy processes belonging to *other* users.

        Parameters
        ----------
        min_cpu_per_proc : float or None
            Per-process CPU% threshold to count as "heavy".
            If None, uses self.min_cpu_per_proc.
        sample_interval : float
            Seconds to wait between priming and measuring cpu_percent.

        Returns
        -------
        total_other_cpu : float
            Sum of cpu_percent of all other users' heavy processes
            (can exceed 100% on multi-core machines).
        offenders : list of (cpu, pid, user, name)
            Sorted by descending CPU usage.
        """
        if min_cpu_per_proc is None:
            min_cpu_per_proc = self.min_cpu_per_proc

        my_user = getpass.getuser()
        procs: List[psutil.Process] = []

        # Prime per-process CPU accounting
        for p in psutil.process_iter(attrs=["pid", "username", "name"]):
            try:
                p.cpu_percent(interval=None)
                procs.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        time.sleep(sample_interval)

        total_other_cpu = 0.0
        offenders: List[ProcessInfo] = []

        for p in procs:
            try:
                info = p.info
                user = info.get("username")
                if user is None or user == my_user:
                    continue

                cpu = p.cpu_percent(interval=None)
                if cpu >= min_cpu_per_proc:
                    total_other_cpu += cpu
                    offenders.append((cpu, info["pid"], user, info["name"]))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        offenders.sort(reverse=True, key=lambda x: x[0])
        return total_other_cpu, offenders

    def wait_for_good_slot(
        self,
        max_total_cpu: Optional[float] = None,
        max_other_cores: Optional[float] = None,
        min_sleep: Optional[float] = None,
        max_checks: Optional[int] = None,
        min_cpu_per_proc: Optional[float] = None,
        verbose: Optional[bool] = None,
    ) -> None:
        """
        Block until the node is reasonably idle.

        Conditions:
          - total system CPU < max_total_cpu (0–100)
          - other users are not burning more than max_other_cores (approx.) cores

        If max_other_cores is None, only the total CPU condition is checked.
        """
        if max_total_cpu is None:
            max_total_cpu = self.max_total_cpu
        if max_other_cores is None:
            max_other_cores = self.max_other_cores
        if min_sleep is None:
            min_sleep = self.min_sleep
        if max_checks is None:
            max_checks = self.max_checks
        if min_cpu_per_proc is None:
            min_cpu_per_proc = self.min_cpu_per_proc
        if verbose is None:
            verbose = self.verbose

        if max_other_cores is not None:
            max_other_users_cpu = max_other_cores * 100.0
        else:
            max_other_users_cpu = float("inf")

        if verbose:
            print(
                f"[wait_for_good_slot] n_cpus={self.n_cpus}, "
                f"max_total_cpu={max_total_cpu}%, "
                f"max_other_cores={max_other_cores}"
            )

        for i in range(max_checks):
            total_cpu = psutil.cpu_percent(interval=1.0)

            other_cpu, offenders = self.scan_other_users_cpu(
                min_cpu_per_proc=min_cpu_per_proc
            )
            other_cores_equiv = other_cpu / 100.0

            if verbose:
                print(
                    f"[slot check {i}] total CPU={total_cpu:5.1f}% | "
                    f"other users ≈ {other_cores_equiv:5.1f} cores"
                )

                if offenders:
                    print("  Heavy external jobs (top 8):")
                    for cpu, pid, user, name in offenders[:8]:
                        print(f"    {user:12s} pid={pid:6d} cpu={cpu:6.1f}%  {name}")

            if (total_cpu < max_total_cpu) and (other_cpu < max_other_users_cpu):
                if verbose:
                    print("CPU conditions OK, proceeding.\n")
                return

            if verbose:
                print(
                    f"  Server busy (other users ~{other_cores_equiv:.1f} cores). "
                    f"Sleeping {min_sleep:.1f} s...\n"
                )
            time.sleep(min_sleep)

        if verbose:
            print("Max checks reached, proceeding anyway.\n")

    def suggest_thread_count(
        self,
        base_threads: Optional[int] = None,
        min_threads: Optional[int] = None,
        max_threads: Optional[int] = None,
        headroom: Optional[float] = None,
        min_cpu_per_proc: Optional[float] = None,
    ) -> int:
        """
        Suggest a thread count based on how many cores *other users* are burning.

        Heuristic:
            used_cores_by_others ≈ sum(process_cpu%) / 100
            free_cores ≈ n_cpus - used_cores_by_others
            allowed_cores ≈ headroom * free_cores

        Everything is clamped into [min_threads, max_threads].
        """
        if base_threads is None:
            base_threads = self.base_threads
        if min_threads is None:
            min_threads = self.min_threads
        if max_threads is None:
            max_threads = self.max_threads
        if headroom is None:
            headroom = self.headroom
        if min_cpu_per_proc is None:
            min_cpu_per_proc = self.min_cpu_per_proc

        other_cpu, _ = self.scan_other_users_cpu(min_cpu_per_proc=min_cpu_per_proc)
        used_cores_by_others = other_cpu / 100.0
        free_cores = max(1.0, self.n_cpus - used_cores_by_others)

        allowed_cores = free_cores * headroom
        suggested = int(allowed_cores)

        suggested = max(min_threads, suggested)
        suggested = min(max_threads, suggested)

        if self.verbose:
            print(
                f"[suggest_thread_count] n_cpus={self.n_cpus}, "
                f"other≈{used_cores_by_others:.1f} cores, "
                f"free≈{free_cores:.1f} cores, "
                f"headroom={headroom:.2f}, "
                f"suggested threads={suggested}"
            )

        return suggested
