"""Standard-library orchestration for the single-node ARE GNU gprof lesson.

The application runs inside the existing allocation. Reports retain the exact
binary identity and profile filenames; no jobs or modules are launched here.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time


def sha256(path):
    with Path(path).open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_session(expected=12):
    """Check the requested ARE configuration without using whole-node CPU counts."""
    cpus = os.environ.get("PBS_NCPUS", "")
    if cpus and (not cpus.isdigit() or int(cpus) != expected):
        raise RuntimeError(f"Launch ARE with {expected} CPU cores on one node; PBS_NCPUS={cpus}")
    nodefile = os.environ.get("PBS_NODEFILE", "")
    nodes = []
    if nodefile and Path(nodefile).is_file():
        nodes = sorted(set(Path(nodefile).read_text().split()))
        if len(nodes) != 1:
            raise RuntimeError("This notebook requires one node")
    affinity = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    if affinity is not None and affinity < expected:
        raise RuntimeError("Kernel CPU affinity is narrower than the ARE allocation; check with the instructor")
    info = {"expected_cores": expected, "PBS_NCPUS": cpus, "nodes": nodes,
            "affinity_cpu_count": affinity, "host": socket.gethostname(),
            "PBS_JOBID": os.environ.get("PBS_JOBID")}
    print(json.dumps(info, indent=2))
    if not cpus or not nodes:
        print("Verify 12 cores and one node on the ARE session card; the lab still caps runs at 12 cores.")
    return info


@dataclass
class Lab:
    baseline: Path
    instrumented: Path
    results: Path
    allocated_cores: int = 12
    ranks: int = 1
    size: int = 30
    iterations: int = 200

    def validate(self):
        for name in ("allocated_cores", "ranks", "size", "iterations"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        side = round(self.ranks ** (1 / 3))
        if side ** 3 != self.ranks:
            raise ValueError("LULESH requires a cubic MPI rank count: 1, 8, 27, ...")
        limits = [self.allocated_cores, 12]
        if os.environ.get("PBS_NCPUS", "").isdigit():
            limits.append(int(os.environ["PBS_NCPUS"]))
        if hasattr(os, "sched_getaffinity"):
            limits.append(len(os.sched_getaffinity(0)))
        if self.ranks > min(limits):
            raise ValueError("MPI ranks exceed this lesson's allocation; one application thread per rank")
        for name in ("baseline", "instrumented"):
            path = Path(getattr(self, name)).expanduser().resolve()
            if not path.is_file() or not os.access(path, os.X_OK):
                raise FileNotFoundError(f"Missing {name} executable: {path}; load lulesh-gprof before ARE starts")
            setattr(self, name, path)
        if self.baseline == self.instrumented:
            raise ValueError("Baseline and instrumented executables must be distinct")
        if not shutil.which("mpirun"):
            raise RuntimeError("Load the matching Open MPI runtime through lulesh-gprof")
        self.results = Path(self.results).expanduser().resolve()

    def run(self, profile=False, label=None):
        self.validate()
        if type(profile) is not bool:
            raise ValueError("profile must be True or False")
        mode = "profile" if profile else "baseline"
        binary = self.instrumented if profile else self.baseline
        self.results.mkdir(parents=True, exist_ok=True)
        tag = re.sub(r"[^A-Za-z0-9_-]", "_", label or mode)
        directory = Path(tempfile.mkdtemp(prefix=f"{tag}-r{self.ranks}-", dir=self.results))
        command = ["mpirun", "-np", str(self.ranks), "--map-by", "slot:PE=1",
                   "--bind-to", "core", "--report-bindings", sys.executable,
                   str(Path(__file__).with_name("rank_run.py")), str(directory), mode,
                   str(binary), "-s", str(self.size), "-i", str(self.iterations)]
        env = os.environ.copy()
        env.pop("GMON_OUT_PREFIX", None)
        env.update(OMP_NUM_THREADS="1", OMP_DYNAMIC="FALSE", OMP_PROC_BIND="close",
                   OMP_PLACES="cores", LC_ALL="C")
        record = {"directory": str(directory), "mode": mode, "binary": str(binary),
                  "binary_sha256": sha256(binary), "ranks": self.ranks, "threads": 1,
                  "size": self.size, "iterations": self.iterations,
                  "allocated_cores": self.allocated_cores, "command": command,
                  "loaded_modules": env.get("LOADEDMODULES"),
                  "source": env.get("LULESH_SOURCE"), "job_id": env.get("PBS_JOBID"),
                  "host": socket.gethostname(), "started_utc": datetime.now(timezone.utc).isoformat(),
                  "environment": {k: env[k] for k in ("OMP_NUM_THREADS", "OMP_DYNAMIC", "LC_ALL")}}
        print(shlex.join(command))
        started = time.perf_counter()
        try:
            completed = subprocess.run(command, cwd=directory, env=env, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            record["returncode"] = completed.returncode
            output = completed.stdout
        except OSError as error:
            output = str(error)
            record["returncode"] = None
        record["launcher_wall_seconds"] = time.perf_counter() - started
        (directory / "run.log").write_text(output)
        match = re.search(r"Elapsed time\s*=\s*([0-9.eE+-]+)", output)
        record["application_seconds"] = float(match[1]) if match else None
        record["profiles"] = [str(p) for p in sorted(directory.glob("gmon.rank-*.*"))]
        (directory / "run.json").write_text(json.dumps(record, indent=2))
        print(output)
        print(f"Saved run: {directory}")
        if record["returncode"] != 0:
            raise RuntimeError(f"Run failed; inspect {directory / 'run.log'}")
        # Match the actual rank and PID, rather than guessing ranks from sorted PIDs.
        for rank in range(self.ranks):
            manifest = directory / f"rank-{rank:03d}.json"
            if not manifest.is_file():
                raise RuntimeError(f"Missing rank {rank} manifest in {directory}")
            data = json.loads(manifest.read_text())
            if profile:
                path = Path(f"{data['gmon_prefix']}.{data['pid']}")
                if not path.is_file() or path.stat().st_size == 0:
                    raise RuntimeError(f"Missing gmon data for rank {rank}; check -pg, normal exit and GMON_OUT_PREFIX: {directory}")
        if profile and len(record["profiles"]) != self.ranks:
            raise RuntimeError(f"Unexpected profile count in {directory}; expected {self.ranks}")
        if not profile and list(directory.glob("gmon*")):
            raise RuntimeError(f"Baseline emitted gmon data: check that it was built without -pg: {directory}")
        return record


def profile_files(record, rank=None):
    if record.get("mode") != "profile":
        raise ValueError("Reports require an instrumented run")
    binary = Path(record["binary"])
    if not binary.is_file() or sha256(binary) != record["binary_sha256"]:
        raise RuntimeError("Executable changed since collection; restore the exact matching binary")
    files = [Path(p) for p in record["profiles"]]
    if rank is not None:
        if type(rank) is not int or not 0 <= rank < record["ranks"]:
            raise ValueError("Rank is outside this run")
        files = [p for p in files if p.name.startswith(f"gmon.rank-{rank:03d}.")]
    if not files or any(not p.is_file() or p.stat().st_size == 0 for p in files):
        raise FileNotFoundError("Missing or empty gmon profile data")
    return files


def report(record, kind="flat", rank=0, lines=35):
    options = {"flat": "-p", "graph": "-q", "info": "-i"}
    if kind not in options:
        raise ValueError("Report kind must be flat, graph or info")
    files = profile_files(record, rank)
    command = ["gprof", "-b", "--demangle", options[kind], record["binary"], *map(str, files)]
    scope = "all-ranks-summed" if rank is None else f"rank-{rank:03d}"
    destination = Path(record["directory"]) / f"{scope}-{kind}.txt"
    return _report(command, destination, lines)


def _report(command, destination, lines):
    print(shlex.join(command))
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, env={**os.environ, "LC_ALL": "C"})
    destination.write_text(completed.stdout)
    destination.with_suffix(".command.json").write_text(json.dumps(command, indent=2))
    if completed.returncode:
        raise RuntimeError(f"gprof failed; inspect {destination}")
    preview = completed.stdout.splitlines()
    print("\n".join(preview if lines is None else preview[:lines]))
    print(f"Full report: {destination}")
    return destination


def merge_profiles(records, results):
    """Sum repeats only when binary and workload match; keep original raw files."""
    if len(records) < 2:
        raise ValueError("Select at least two comparable profile runs")
    keys = ("binary_sha256", "ranks", "threads", "size", "iterations")
    signature = tuple(records[0][key] for key in keys)
    if any(tuple(r[key] for key in keys) != signature for r in records):
        raise ValueError("Only merge the same binary, input and process/thread configuration")
    files = [p for record in records for p in profile_files(record)]
    if len(files) != len(set(files)):
        raise ValueError("A profile was selected more than once")
    directory = Path(tempfile.mkdtemp(prefix="merged-", dir=results))
    command = ["gprof", "-s", records[0]["binary"], *map(str, files)]
    completed = subprocess.run(command, cwd=directory, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, env={**os.environ, "LC_ALL": "C"})
    (directory / "merge.log").write_text(completed.stdout)
    (directory / "merge.json").write_text(json.dumps({"command": command, "runs": records,
                                                     "returncode": completed.returncode}, indent=2))
    merged = directory / "gmon.sum"
    if completed.returncode or not merged.is_file():
        raise RuntimeError(f"Merge failed; inspect {directory / 'merge.log'}")
    _report(["gprof", "-b", "--demangle", "-p", records[0]["binary"], str(merged)],
            directory / "sum-flat.txt", 35)
    print("This report SUMS time and calls across inputs; it is not an average run or MPI wall time.")
    return directory
