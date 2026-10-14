"""Standard-library helpers for the ARE/Open MPI VTune notebook.

Each run prints its command and retains its log and metadata. This module does
not load modules, submit jobs, or change the parent environment.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import tempfile
import time


@dataclass
class Lab:
    binary: Path
    results: Path
    allocated_cores: int
    ranks: int = 1
    size: int = 30
    iterations: int = 200

    def validate(self, threads):
        for name, value in (("allocated_cores", self.allocated_cores),
                            ("ranks", self.ranks), ("size", self.size),
                            ("iterations", self.iterations), ("threads", threads)):
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        side = round(self.ranks ** (1 / 3))
        if side ** 3 != self.ranks:
            raise ValueError("LULESH requires a cubic MPI rank count: 1, 8, 27, ...")
        limits = [self.allocated_cores]
        if os.environ.get("PBS_NCPUS", "").isdigit():
            limits.append(int(os.environ["PBS_NCPUS"]))
        if hasattr(os, "sched_getaffinity"):
            limits.append(len(os.sched_getaffinity(0)))
        if self.ranks * threads > min(limits):
            raise ValueError("MPI ranks x OpenMP threads exceeds the available allocation")
        self.binary = Path(self.binary).expanduser().resolve()
        self.results = Path(self.results).expanduser().resolve()
        if not self.binary.is_file() or not os.access(self.binary, os.X_OK):
            raise FileNotFoundError(
                f"LULESH executable missing: {self.binary}. Load the lulesh module before launching ARE.")
        if not shutil.which("mpirun"):
            raise RuntimeError("The lulesh module must supply its matching Open MPI runtime")

    def command(self, threads, analysis=None, result_prefix=None):
        """The mapping options are specific to Open MPI, as used in this lab."""
        self.validate(threads)
        cmd = ["mpirun", "-np", str(self.ranks),
               "--map-by", f"slot:PE={threads}", "--bind-to", "core",
               "--report-bindings"]
        if analysis is not None:
            if analysis not in ("hotspots", "hpc-performance", "memory-access"):
                raise ValueError(f"Unsupported workshop analysis: {analysis}")
            if result_prefix is None:
                raise ValueError("A fresh result prefix is required for profiling")
            if not shutil.which("vtune"):
                raise RuntimeError("Load the intel-vtune module before starting Jupyter")
            cmd += ["vtune", "-collect", analysis]
            if analysis == "hotspots":
                cmd += ["-knob", "sampling-mode=sw"]
            cmd += ["-trace-mpi", "-result-dir", str(result_prefix), "--"]
        cmd += [str(self.binary), "-s", str(self.size), "-i", str(self.iterations)]
        return cmd

    def run(self, threads=1, analysis=None, label=None):
        """Save launcher wall time, including finalisation for profiled runs."""
        self.validate(threads)
        self.results.mkdir(parents=True, exist_ok=True)
        label = label or analysis or "baseline"
        if not label or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in label):
            raise ValueError("Use letters, digits, '-' and '_' in run labels")
        run_dir = Path(tempfile.mkdtemp(prefix=f"{label}-r{self.ranks}-t{threads}-",
                                        dir=self.results))
        cmd = self.command(threads, analysis, run_dir / "vtune")
        omp = {"OMP_NUM_THREADS": str(threads), "OMP_DYNAMIC": "FALSE",
               "OMP_PLACES": "cores", "OMP_PROC_BIND": "close"}
        env = dict(os.environ, **omp)
        record = {
            "command": cmd, "environment": omp,
            "loaded_modules": env.get("LOADEDMODULES", ""),
            "lulesh_source": env.get("LULESH_SOURCE"),
            "host": socket.gethostname(), "pbs_jobid": env.get("PBS_JOBID"),
            "allocated_cores": self.allocated_cores,
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "binary_sha256": hashlib.sha256(self.binary.read_bytes()).hexdigest(),
            "ranks": self.ranks, "threads": threads, "size": self.size,
            "iterations": self.iterations, "analysis": analysis,
            "directory": str(run_dir), "returncode": None,
        }
        print(" ".join(f"{k}={v}" for k, v in omp.items()))
        print(shlex.join(cmd), flush=True)
        metadata = run_dir / "run.json"
        metadata.write_text(json.dumps(record, indent=2) + "\n")
        started = time.perf_counter()
        try:
            with (run_dir / "run.log").open("w") as output:
                completed = subprocess.run(cmd, cwd=run_dir, env=env,
                                           stdout=output, stderr=subprocess.STDOUT,
                                           check=False)
            record["returncode"] = completed.returncode
        finally:
            record["launcher_wall_seconds"] = time.perf_counter() - started
            metadata.write_text(json.dumps(record, indent=2) + "\n")
            print(f"Saved log and metadata: {run_dir}")
        print("\n".join((run_dir / "run.log").read_text(errors="replace").splitlines()[-35:]))
        if record["returncode"] != 0:
            raise RuntimeError(f"Run failed; inspect {run_dir / 'run.log'}")
        return record


def result_dirs(record):
    """Find the exact result or the per-host results made by -trace-mpi."""
    parent = Path(record["directory"])
    found = sorted(p for p in parent.glob("vtune*") if p.is_dir())
    if not found:
        raise FileNotFoundError(f"No VTune results under {parent}; read run.log")
    return found


def report(record, kind="summary"):
    """Print and retain one text report for every result in a collection."""
    if kind not in ("summary", "hotspots"):
        raise ValueError("Use a summary or hotspots report")
    for result in result_dirs(record):
        cmd = ["vtune", "-report", kind, "-result-dir", str(result)]
        if kind == "hotspots":
            cmd += ["-group-by", "function"]
        print(shlex.join(cmd), flush=True)
        completed = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, check=False)
        destination = result.parent / f"{result.name}-{kind}.txt"
        destination.write_text(completed.stdout)
        print(completed.stdout)
        if completed.returncode:
            raise RuntimeError(f"Report failed; inspect {destination}")
        print(f"Saved report: {destination}")
