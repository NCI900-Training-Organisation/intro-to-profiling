"""Exec LULESH with a glibc gmon prefix that identifies the Open MPI rank."""
import json
import os
from pathlib import Path
import socket
import sys


def main():
    if len(sys.argv) < 4:
        raise SystemExit("Usage: rank_run.py <run-directory> <profile|baseline> <executable> [args...]")
    directory = Path(sys.argv[1]).resolve()
    mode = sys.argv[2]
    rank = os.environ.get("OMPI_COMM_WORLD_RANK")
    if mode not in ("profile", "baseline") or rank is None or not rank.isdigit():
        raise SystemExit("Expected a profile/baseline run launched through Open MPI")
    prefix = directory / f"gmon.rank-{int(rank):03d}"
    env = os.environ.copy()
    env.pop("GMON_OUT_PREFIX", None)
    if mode == "profile":
        env["GMON_OUT_PREFIX"] = str(prefix)
    metadata = {"rank": int(rank), "pid": os.getpid(), "hostname": socket.gethostname(),
                "mode": mode, "command": sys.argv[3:],
                "gmon_prefix": str(prefix) if mode == "profile" else None}
    (directory / f"rank-{int(rank):03d}.json").write_text(json.dumps(metadata, indent=2))
    os.chdir(directory)
    # exec preserves this PID: glibc writes <prefix>.<pid> on normal exit.
    os.execvpe(sys.argv[3], sys.argv[3:], env)


if __name__ == "__main__":
    main()
