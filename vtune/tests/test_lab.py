"""Exercise orchestration using fake CLI programs, never real profiling data."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_DIR))
from lab import Lab, report, result_dirs


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vtune tests with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.tool("mpirun", '''
import os, sys
args = sys.argv[1:]
if args == ["--version"]:
    print("Open MPI TEST DOUBLE")
    sys.exit(0)
while args and (args[0].startswith("--") or args[0] == "-np"):
    option = args.pop(0)
    if option != "--report-bindings":
        args.pop(0)
os.execvp(args[0], args)
''')
        self.tool("vtune", '''
from pathlib import Path
import subprocess, sys
args = sys.argv[1:]
if args == ["-version"]:
    print("VTune TEST DOUBLE; no actual measurements")
    sys.exit(0)
result = Path(args[args.index("-result-dir") + 1])
if "-report" in args:
    assert result.is_dir()
    print("TEST DOUBLE report for", result)
    sys.exit(0)
result = Path(str(result) + ".test-node")
result.mkdir()
(result / "test.vtune").write_text("test fixture")
application = args[args.index("--") + 1:]
sys.exit(subprocess.run(application).returncode)
''')
        self.tool("lscpu", 'print("TEST DOUBLE CPU topology")')
        self.binary = self.tool("lulesh2.0", '''
import os
print("LULESH TEST DOUBLE; no numerical calculation")
print("threads:", os.environ.get("OMP_NUM_THREADS"))
print("Elapsed time = 1.0 (s)")
''')
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {"PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
                                "PBS_NCPUS": "12", "PBS_NODEFILE": "",
                                "PBS_JOBID": "test-are-session",
                                "LOADEDMODULES": "lulesh/test:intel-vtune/test",
                                "LULESH_SOURCE": ""}).start()
        patch("lab.os.sched_getaffinity", return_value=set(range(16))).start()
        self.lab = Lab(self.binary, self.root / "results", allocated_cores=4)
        self.output = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def tool(self, name, source):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n" + source)
        path.chmod(0o755)
        return path

    def test_baselines_keep_separate_logs_and_metadata(self):
        first = self.lab.run(threads=2)
        second = self.lab.run(threads=2)
        self.assertNotEqual(first["directory"], second["directory"])
        record = json.loads((Path(first["directory"]) / "run.json").read_text())
        self.assertEqual(record["returncode"], 0)
        self.assertEqual(record["environment"]["OMP_NUM_THREADS"], "2")
        self.assertEqual(record["environment"]["OMP_PROC_BIND"], "close")
        self.assertEqual(len(record["binary_sha256"]), 64)
        self.assertIn("lulesh/test", record["loaded_modules"])
        self.assertIn("threads: 2", (Path(first["directory"]) / "run.log").read_text())
        self.assertGreater(record["launcher_wall_seconds"], 0)

    def test_profile_discovers_hostname_result_and_exports_reports(self):
        record = self.lab.run(threads=4, analysis="hotspots")
        self.assertIn("sampling-mode=sw", record["command"])
        self.assertLess(record["command"].index("mpirun"), record["command"].index("vtune"))
        self.assertEqual([p.name for p in result_dirs(record)], ["vtune.test-node"])
        report(record, "summary")
        report(record, "hotspots")
        self.assertTrue((Path(record["directory"]) / "vtune.test-node-summary.txt").is_file())
        self.assertTrue((Path(record["directory"]) / "vtune.test-node-hotspots.txt").is_file())

    def test_hardware_analyses_do_not_request_software_sampling(self):
        for kind in ("hpc-performance", "memory-access"):
            record = self.lab.run(threads=1, analysis=kind)
            self.assertNotIn("sampling-mode=sw", record["command"])
            self.assertEqual(len(result_dirs(record)), 1)

    def test_rejects_invalid_ranks_and_resource_overcommit(self):
        with self.assertRaisesRegex(ValueError, "allocation"):
            self.lab.run(threads=8)
        self.lab.ranks = 4
        with self.assertRaisesRegex(ValueError, "cubic"):
            self.lab.run()
        self.lab.ranks = 8
        self.lab.allocated_cores = 8
        record = self.lab.run(threads=1)
        self.assertEqual(record["ranks"], 8)

    def test_failure_preserves_diagnostics_and_raises(self):
        self.binary.write_text(f"#!{sys.executable}\nimport sys\nprint('intentional failure')\nsys.exit(7)\n")
        with self.assertRaisesRegex(RuntimeError, "Run failed"):
            self.lab.run()
        dirs = list(self.lab.results.iterdir())
        self.assertEqual(len(dirs), 1)
        self.assertEqual(json.loads((dirs[0] / "run.json").read_text())["returncode"], 7)
        self.assertIn("intentional failure", (dirs[0] / "run.log").read_text())

    def test_twelve_core_session_accepts_twelve_threads_and_caps_mpi(self):
        self.lab.allocated_cores = 12
        record = self.lab.run(threads=12, analysis="hotspots")
        self.assertEqual(record["allocated_cores"], 12)
        self.assertEqual(record["threads"], 12)
        self.assertIn("slot:PE=12", record["command"])
        with self.assertRaisesRegex(ValueError, "allocation"):
            self.lab.run(threads=13)
        self.lab.ranks = 8
        with self.assertRaisesRegex(ValueError, "allocation"):
            self.lab.run(threads=2)
        self.lab.ranks = 12
        with self.assertRaisesRegex(ValueError, "cubic"):
            self.lab.run(threads=1)

    def test_node_visibility_does_not_expand_session_budget(self):
        self.lab.allocated_cores = 12
        with patch.dict(os.environ, {"PBS_NCPUS": "96"}), \
                patch("lab.os.sched_getaffinity", return_value=set(range(96))):
            with self.assertRaisesRegex(ValueError, "allocation"):
                self.lab.run(threads=13)

    def test_notebook_rejects_wrong_are_allocation(self):
        notebook = json.loads((LAB_DIR / "vtune_lab.ipynb").read_text())
        source = next("".join(c["source"]) for c in notebook["cells"]
                      if c["id"] == "are-allocation")
        namespace = {"ALLOCATED_CORES": 12, "os": os, "socket": socket, "Path": Path}
        with patch.dict(os.environ, {"PBS_NCPUS": "4"}):
            with self.assertRaisesRegex(RuntimeError, "12 CPU cores"):
                exec(source, namespace)
        nodefile = self.root / "nodes"
        nodefile.write_text("node-a\nnode-b\n")
        with patch.dict(os.environ, {"PBS_NODEFILE": str(nodefile)}):
            with self.assertRaisesRegex(RuntimeError, "one node"):
                exec(source, namespace)

    def test_missing_result_does_not_silently_succeed(self):
        record = self.lab.run()
        with self.assertRaisesRegex(FileNotFoundError, "No VTune results"):
            result_dirs(record)

    def test_notebook_cells_in_order_including_optional_branches(self):
        # Run every Python cell against test doubles in a temporary repository.
        # This checks cell dependencies and orchestration, not VTune compatibility.
        repo = self.root / "repository"
        (repo / "vtune").mkdir(parents=True)
        shutil.copy(LAB_DIR / "lab.py", repo / "vtune/lab.py")
        lulesh = self.root / "shared source"
        lulesh.mkdir()
        (lulesh / "lulesh.cc").write_text("// TEST DOUBLE: CalcForceForNodes\n")
        patch.dict(os.environ, {"LULESH_SOURCE": str(lulesh)}).start()
        original_which = shutil.which

        def runtime_only(command, *args, **kwargs):
            # Compilation must not be a participant dependency.
            if command in ("mpicxx", "cmake", "ninja", "git"):
                return None
            return original_which(command, *args, **kwargs)

        patch("shutil.which", side_effect=runtime_only).start()
        notebook = json.loads((LAB_DIR / "vtune_lab.ipynb").read_text())
        namespace = {"__name__": "__main__"}
        old_cwd = Path.cwd()
        old_path = sys.path[:]
        try:
            os.chdir(repo)
            for cell in notebook["cells"]:
                if cell["cell_type"] != "code":
                    continue
                source = "".join(cell["source"])
                source = source.replace(
                    'Path(f"/scratch/{PROJECT}/{getpass.getuser()}")',
                    f"Path({str(self.root / 'participant scratch')!r})")
                source = source.replace("RUN_HARDWARE = False", "RUN_HARDWARE = True")
                source = source.replace("RUN_MPI_EXTENSION = False", "RUN_MPI_EXTENSION = True")
                exec(compile(source, f"notebook:{cell['id']}", "exec"), namespace)
            self.assertEqual(namespace["ALLOCATED_CORES"], 12)
            self.assertEqual(list(namespace["measurements"]), [1, 2, 4, 6, 12])
            self.assertEqual(namespace["hotspots_12"]["threads"], 12)
            self.assertIn("memory", namespace)
            self.assertIn("mpi_hotspots", namespace)
            self.assertEqual(namespace["memory"]["threads"], 12)
            self.assertEqual(namespace["mpi_hotspots"]["ranks"], 8)
            self.assertEqual(namespace["lab"].binary, self.binary)
            self.assertEqual(namespace["LULESH_SOURCE"], lulesh)
            self.assertEqual(namespace["lab"].results,
                             self.root / "participant scratch/vtune-results")
            self.assertEqual(list(lulesh.iterdir()), [lulesh / "lulesh.cc"])
            self.assertFalse((repo / "vtune/results").exists())
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path

    def test_notebook_reports_missing_module_executable(self):
        notebook = json.loads((LAB_DIR / "vtune_lab.ipynb").read_text())
        setup = next("".join(c["source"]) for c in notebook["cells"]
                     if c["id"] == "vtune-07")
        old_cwd = Path.cwd()
        try:
            os.chdir(LAB_DIR)
            with patch("shutil.which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "lulesh2.0 is missing"):
                    exec(setup, {})
        finally:
            os.chdir(old_cwd)

    def test_source_inspection_is_optional(self):
        notebook = json.loads((LAB_DIR / "vtune_lab.ipynb").read_text())
        source = next("".join(c["source"]) for c in notebook["cells"]
                      if c["id"] == "vtune-24")
        record = self.lab.run(threads=1, analysis="hotspots")
        import shlex
        for directory in (None, self.root / "nonexistent-source"):
            exec(source, {"LULESH_SOURCE": directory, "hotspots_1": record,
                          "result_dirs": result_dirs, "shlex": shlex})
        self.assertIn("Source inspection is unavailable", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
