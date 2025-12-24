import json
import sys
import time
import threading
import subprocess
from typing import cast, Optional
import click
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os
import rich
import multiprocessing
from v0.relationalai import metagen
import tempfile
import webbrowser
import shutil

from . import snapshot_viewer as viewer
from . import cleanup_snapshots as cleanup


from .cli_controls import divider, Spinner

#--------------------------------------------------
# Root
#--------------------------------------------------

@click.group()
def cli():
    pass

#--------------------------------------------------
# Watch
#--------------------------------------------------

def clear():
    print("\033c", end="")
    os.system('cls' if os.name == 'nt' else 'clear')

class ChangeHandler(PatternMatchingEventHandler):

    def __init__(self):
        super().__init__(patterns = ["*.py", "*.rel", "raiconfig.toml"])
        self.script = None
        self.process = None
        self.event_lock = threading.Lock()
        self.has_queued_events = False

    def check_event(self, event):
        if not event.src_path.endswith(".py"):
            return

        if "examples/" in event.src_path \
            or "tests/end2end/test_cases/" in event.src_path \
            or "tests/snowflake_integration/test_cases/" in event.src_path \
            or "tests/early_access/unified/tests/" in event.src_path \
            or "metagen.py" in event.src_path:
            self.script = event.src_path

    def on_any_event(self, event):
        self.check_event(event)
        with self.event_lock:
            if self.process and self.process.poll() is None:
                # Mark that there are queued events
                self.has_queued_events = True
            else:
                self.start_process()

    def start_process(self):
        if self.script is None:
            return

        clear()
        rich.print(f"[yellow bold]{os.path.basename(self.script)}")
        rich.print("[yellow]------------------------------------------------------")
        rich.print("")

        # Start or restart the script
        self.process = subprocess.Popen(['python', self.script], shell=False)
        # Use a thread to wait for the process to finish without blocking
        wait_thread = threading.Thread(target=self.wait_and_restart_if_needed)
        wait_thread.start()

    def wait_and_restart_if_needed(self):
        if self.process is not None:
            self.process.wait()

        with self.event_lock:
            if self.has_queued_events:
                # Reset the flag and restart the process for batched events
                self.has_queued_events = False
                # Delay added to allow for potentially more events to accumulate
                # Adjust or remove the delay as needed
                time.sleep(0.5)
                self.start_process()

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
def watch(directory):
    """Watch a DIRECTORY and re-run a SCRIPT on file changes."""
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=directory, recursive=True)  # Now recursive
    observer.start()

    clear()
    rich.print(f"[yellow]Watching for changes in '{directory}'.")
    rich.print("[yellow]Save a script in examples/ to run it.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

#--------------------------------------------------
# Code stats
#--------------------------------------------------

def cloc(paths):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    src_dir = os.path.join(script_dir, '..')
    core_paths = [os.path.join(src_dir, f) for f in paths]
    process = subprocess.Popen(['cloc', '--json', *core_paths], stdout=subprocess.PIPE, text=True)
    output, _ = process.communicate()

    try:
        # Parse the JSON output
        data = json.loads(output)
        # The total number of source lines is under 'SUM'/'code'
        total_lines = data['SUM']['code'] if 'SUM' in data else 0
        return cast(int, total_lines)
    except Exception as e:
        print(f"Error while parsing cloc output: {e}")
        return 0

@cli.command()
def stats():
    dsl = cloc(["dsl.py"])
    compiler = cloc(["compiler.py"])
    metamodel = cloc(["metamodel.py"])
    emitter = cloc(["rel_emitter.py"])
    rel = cloc(["rel.py"])
    metagen = cloc(["metagen.py"])
    gentest = cloc(["metagen.py"])
    tools = cloc(["tools/"])
    clients = cloc(["clients/"])
    std = cloc(["std/"])
    non_test_total = cloc(["."]) - metagen
    total = non_test_total + gentest
    core = dsl + compiler + metamodel + emitter + rel

    max_width = len(f"{total:,}")

    # Print statements with numbers right-aligned
    divider()
    rich.print(f"[yellow]RelationalAI  {non_test_total:>{max_width},} loc")
    rich.print(f"[yellow]  Core        {core:>{max_width},} loc")
    rich.print(f"[yellow]    dsl       {dsl:>{max_width},} loc")
    rich.print(f"[yellow]    rel       {rel:>{max_width},} loc")
    rich.print(f"[yellow]    emitter   {emitter:>{max_width},} loc")
    rich.print(f"[yellow]    metamodel {metamodel:>{max_width},} loc")
    rich.print(f"[yellow]    compiler  {compiler:>{max_width},} loc")
    rich.print(f"[yellow]  Clients     {clients:>{max_width},} loc")
    rich.print(f"[yellow]  Std         {std:>{max_width},} loc")
    rich.print(f"[yellow]  Tools       {tools:>{max_width},} loc")
    rich.print("")
    rich.print(f"[cyan]Gentest       {gentest:>{max_width},} loc")
    rich.print("")
    rich.print(f"[magenta]All           {total:>{max_width},} loc")
    divider()


#--------------------------------------------------
# Metagen
#--------------------------------------------------

@cli.command("gen")
@click.option('--total', default=50000, help='Total number of models to generate.')
@click.option('--threads', default=multiprocessing.cpu_count(), help='Threads to use, default is CPU count.')
@click.option('--internal', default=False, is_flag=True)
def gen(total, threads, internal):
    if not internal:
        divider()
    with Spinner(f"Testing {total:,.0f} models on {threads:,.0f} threads", f"Tested {total:,.0f} models"):
        if threads > 1:
            (elapsed, results) = metagen.batches(total, threads)
        else:
            gen = metagen.batch(total)
            results = [gen]
            elapsed = gen.elapsed

    rich.print("")

    for result in results:
        rich.print(result)

    failed = False
    for result in results:
        if len(result.failures) > 0:
            failed = True
            rich.print()
            result.print_failures(1)
            rich.print("")
            break

    rich.print("")
    rich.print(f"[yellow bold]Total time: {elapsed:,.3f}s")
    rich.print("")
    if not internal:
        divider()
        sys.exit(failed)

#--------------------------------------------------
# Metagen Watch
#--------------------------------------------------

class MetagenWatcher(PatternMatchingEventHandler):

    def __init__(self, total, threads):
        super().__init__(patterns = ["*.py"])
        self.process = None
        self.event_lock = threading.Lock()
        self.has_queued_events = False
        self.total = total
        self.threads = threads
        self.start_process()

    def on_any_event(self, event):
        with self.event_lock:
            if self.process and self.process.poll() is None:
                # Mark that there are queued events
                self.has_queued_events = True
            else:
                self.start_process()

    def start_process(self):
        clear()
        rich.print("[yellow bold]Metagen")
        rich.print("[yellow]------------------------------------------------------")
        rich.print("")

        # Start or restart the script
        self.process = subprocess.Popen(['rai-dev', 'gen', '--total', str(self.total), '--threads', str(self.threads), "--internal"], shell=False)
        # Use a thread to wait for the process to finish without blocking
        wait_thread = threading.Thread(target=self.wait_and_restart_if_needed)
        wait_thread.start()

    def wait_and_restart_if_needed(self):
        if self.process is not None:
            self.process.wait()

        with self.event_lock:
            if self.has_queued_events:
                # Reset the flag and restart the process for batched events
                self.has_queued_events = False
                # Delay added to allow for potentially more events to accumulate
                # Adjust or remove the delay as needed
                time.sleep(0.5)
                self.start_process()


@cli.command("gen:watch")
@click.argument('directory', type=click.Path(exists=True))
@click.option('--total', default=20000, help='Total number of models to generate')
@click.option('--threads', default=multiprocessing.cpu_count(), help='Threads to use')
def gen_watch(directory, total, threads):
    clear()
    event_handler = MetagenWatcher(total, threads)
    observer = Observer()
    observer.schedule(event_handler, path=directory, recursive=True)  # Now recursive
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

#--------------------------------------------------
# Snapshot Management
#--------------------------------------------------

def get_modified_files():
    """Get a list of files that are modified according to git."""
    try:
        # Get both staged and unstaged changes
        staged = subprocess.check_output(['git', 'diff', '--name-only', '--cached']).decode('utf-8').splitlines()
        unstaged = subprocess.check_output(['git', 'diff', '--name-only']).decode('utf-8').splitlines()
        untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard']).decode('utf-8').splitlines()

        # Combine all changes
        return set(staged + unstaged + untracked)
    except subprocess.CalledProcessError:
        print("Warning: Failed to get modified files from git. Showing all files.")
        return None

@cli.group()
def snapshots():
    """Manage snapshot tests."""
    pass

def get_repo_root():
    """Get the root directory of the repository."""
    repo_root = os.getcwd()
    if not os.path.exists(os.path.join(repo_root, ".git")):
        print("Error: Please run this command from the repository root.")
        sys.exit(1)
    return repo_root

@snapshots.command("view")
@click.option('--test-dir', default='tests/early_access/unit', help='Test directory to scan')
@click.option('--output', default=None, help='Output HTML file (defaults to a temp file)')
@click.option('--all', is_flag=True, help='Show all snapshots, not just modified ones')
def snapshots_view(test_dir, output, all):
    """Generate an HTML report of snapshot tests and open it in a browser."""
    repo_root = get_repo_root()

    # Make sure the test_dir is an absolute path
    if not os.path.isabs(test_dir):
        test_dir = os.path.join(repo_root, test_dir)

    # Check if the test directory exists
    if not os.path.exists(test_dir):
        print(f"Error: Test directory {test_dir} does not exist")
        return

    # Create a temporary file for the HTML report if not specified
    if not output:
        temp_dir = tempfile.mkdtemp()
        output = os.path.join(temp_dir, "snapshot_report.html")
    elif not os.path.isabs(output):
        output = os.path.join(repo_root, output)

    # Find all snapshot files
    snapshot_files = []
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.snapshot'):
                snapshot_files.append(os.path.join(root, file))

    # Filter to only show modified snapshots if needed
    if not all:
        modified_files = get_modified_files()
        if modified_files:
            # Filter to only include modified snapshot files
            modified_snapshots = []
            for path in snapshot_files:
                if any(path.endswith(f) for f in modified_files if f.endswith('.snapshot')):
                    modified_snapshots.append(path)

            if modified_snapshots:
                snapshot_files = modified_snapshots
                print(f"Filtered to {len(snapshot_files)} modified snapshot files")
            else:
                print("No modified snapshot files found. Use --all to see all snapshots.")

    # Use the registry to get test information
    registry = viewer.load_snapshot_registry()
    if not registry:
        print("No snapshot registry found. Run tests first to create it.")
        return

    # Generate the report using the registry
    viewer.generate_report_from_registry(registry, snapshot_files, output)

    print(f"Report generated: {output}")

    # Open the report in the default browser
    webbrowser.open(f"file://{os.path.abspath(output)}")

@snapshots.command("cleanup")
@click.option('--test-dir', default='tests/early_access/unit', help='Test directory to scan')
@click.option('--remove', is_flag=True, help='Remove unused snapshot files')
@click.option('--regenerate', is_flag=True, help='Regenerate snapshots by running tests')
def snapshots_cleanup(test_dir, remove, regenerate):
    """Identify and optionally remove unused snapshot files."""
    repo_root = get_repo_root()

    # Make sure the test_dir is an absolute path
    if not os.path.isabs(test_dir):
        test_dir = os.path.join(repo_root, test_dir)

    if remove and regenerate:
        # Remove and regenerate
        removed = cleanup.remove_snapshots(test_dir)
        regenerated = cleanup.regenerate_snapshots(test_dir)

        print(f"\nSummary: Removed {removed} snapshots, regenerated {regenerated} snapshots")
        if removed > regenerated:
            print(f"Cleaned up {removed - regenerated} unused snapshots")
    elif remove:
        # Just remove
        cleanup.remove_snapshots(test_dir)
    elif regenerate:
        # Just regenerate
        cleanup.regenerate_snapshots(test_dir)
    else:
        # Just count and report
        snapshots = cleanup.find_all_snapshot_files(test_dir)
        print(f"Found {len(snapshots)} snapshot files")
        print("\nUse --remove to remove all snapshots")
        print("Use --regenerate to regenerate snapshots by running tests")

#--------------------------------------------------
# Test Runner
#--------------------------------------------------

@cli.group("test")
def test_group():
    """Run tests with optional snapshot updates."""
    pass

@test_group.command("unit")
@click.argument('test_path', required=False)
@click.option('--update', is_flag=True, help='Update snapshot files')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run_unit_tests(test_path, update, verbose):
    """Run unit tests with optional snapshot updates."""
    repo_root = get_repo_root()

    # Determine the test path
    if not test_path:
        test_path = "tests/unit"
    elif test_path == "early_access":
        test_path = "tests/early_access/unit"
    elif test_path == "builder":
        test_path = "tests/early_access/unit/builder"
    elif test_path == "ir":
        test_path = "tests/early_access/unit/ir"
    elif test_path == "rel":
        test_path = "tests/early_access/unit/rel"
    elif test_path == "sql":
        test_path = "tests/early_access/unit/sql"

    # Make sure the test_path is an absolute path
    if not os.path.isabs(test_path):
        test_path = os.path.join(repo_root, test_path)

    # Build the command
    cmd = ["pytest", test_path]

    # Add options
    if update:
        cmd.append("--snapshot-update")
    if verbose:
        cmd.append("-v")

    divider()
    rich.print("[yellow bold]Running unit tests")
    rich.print(f"[yellow]Test path: {test_path}")
    rich.print("")

    # Run the command
    result = subprocess.run(cmd)

    divider()
    sys.exit(result.returncode)

@test_group.command("e2e")
@click.argument('test_path', required=False)
@click.option('--update', is_flag=True, help='Update snapshot files')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run_e2e_tests(test_path, update, verbose):
    """Run end-to-end tests with Snowflake configuration."""
    repo_root = get_repo_root()

    # Determine the test path
    if not test_path:
        test_path = "tests/end2end"
    elif test_path == "early_access":
        test_path = "tests/early_access/end2end"

    # Make sure the test_path is an absolute path
    if not os.path.isabs(test_path):
        test_path = os.path.join(repo_root, test_path)

    # Build the command
    cmd = ["pytest", test_path]

    # Add options
    if update:
        cmd.append("--snapshot-update")
    if verbose:
        cmd.append("-v")

    divider()
    rich.print("[yellow bold]Running end-to-end tests")
    rich.print(f"[yellow]Test path: {test_path}")
    rich.print("")

    # Run the command
    result = subprocess.run(cmd)

    divider()
    sys.exit(result.returncode)

@test_group.command("all")
@click.argument('test_path', required=False)
@click.option('--update', is_flag=True, help='Update snapshot files')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run_all_tests(test_path, update, verbose):
    """Run both unit and end-to-end tests."""
    # First run unit tests
    unit_result = subprocess.run(
        ["rai-dev", "test", "unit"] +
        ([test_path] if test_path else []) +
        (["--update"] if update else []) +
        (["--verbose"] if verbose else [])
    ).returncode

    # Then run e2e tests
    e2e_result = subprocess.run(
        ["rai-dev", "test", "e2e"] +
        ([test_path] if test_path else []) +
        (["--update"] if update else []) +
        (["--verbose"] if verbose else [])
    ).returncode

    # Exit with non-zero if either test suite failed
    if unit_result != 0 or e2e_result != 0:
        sys.exit(1)
    return 0

#--------------------------------------------------
# Build Commands
#--------------------------------------------------

@cli.command("build")
def build_command():
    """Build the package."""
    result = subprocess.run(["python", "-m", "build"])
    sys.exit(result.returncode)

@cli.command("build:zip")
def build_zip_command():
    """Build the Snowflake notebook zip file."""
    result = subprocess.run(["python", "-m", "tools.snowflake_notebook.stage_zip"])
    sys.exit(result.returncode)

#--------------------------------------------------
# Type Checking
#--------------------------------------------------

@cli.command("typecheck")
@click.option('--path', default='', help='Path to typecheck')
def typecheck(path):
    """Run pyright type checking."""
    divider()
    rich.print("[yellow bold]Running type checking with pyright")
    rich.print("")

    result = subprocess.run(["pyright"] + ([path] if path else []))

    divider()
    sys.exit(result.returncode)

#--------------------------------------------------
# Linting
#--------------------------------------------------

@cli.command("lint")
@click.option('--path', default='', help='Path to lint')
def lint(path):
    """Run ruff linting."""
    divider()
    rich.print("[yellow bold]Running linting with ruff")
    rich.print("")

    result = subprocess.run(["ruff", "check"] + ([path] if path else []))

    divider()
    sys.exit(result.returncode)

#--------------------------------------------------
# Syncing Dependencies
#--------------------------------------------------

@cli.command("sync")
def sync():
    """Sync dependencies."""
    divider()
    rich.print("[yellow bold]Syncing dependencies")
    rich.print("")

    result = subprocess.run(["python", "-m", "pip", "install", "-r", "requirements.lock"])

    divider()
    sys.exit(result.returncode)

#--------------------------------------------------
# Update Lockfile
#--------------------------------------------------

@cli.command("lockfile", help="Update requirements.lock file with latest dependencies.")
@click.argument("update", required=True, default=None)
def update_lockfile(update):
    LOCKFILE = "requirements.lock"
    if update != "update":
        rich.print(f"[yellow]Do `rai-dev lockfile update` to update {LOCKFILE}")
        return
    """Update requirements lockfile with latest dependencies."""
    divider()
    rich.print(f"[yellow bold]Updating {LOCKFILE}")
    rich.print("")

    PYPROJECT_FILE = "pyproject.toml"
    REQUIREMENTS_LOCK = LOCKFILE

    # Ensure pip-tools is installed
    if shutil.which("pip-compile") is None:
        rich.print("pip-tools not found, installing it...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pip-tools"], check=True)

    # Run pip-compile to generate requirements.lock
    rich.print(f"Running pip-compile to generate {REQUIREMENTS_LOCK}...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "piptools",
            "compile",
            "--quiet",
            "--no-strip-extras",
            "--upgrade",
            "--resolver=backtracking",
            "--extra",
            "dev",
            "--extra",
            "ea",
            "-o",
            REQUIREMENTS_LOCK,
            PYPROJECT_FILE,
        ],
        check=True
    )

    # Append -e . to the requirements file
    with open(REQUIREMENTS_LOCK, "a") as f:
        f.write("\n\n# Add the project root as a local package\n")
        f.write("-e .\n")

    rich.print(f"✔ Updated {REQUIREMENTS_LOCK}")

    divider()

#--------------------------------------------------
# TPCH Commands
#--------------------------------------------------

@cli.group("tpch")
def tpch_group():
    """Run TPCH benchmark queries."""
    pass

@tpch_group.command()
@click.argument("query_num", type=int, required=False)
@click.option("--all", "run_all", is_flag=True, help="Run all TPCH queries")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def run(query_num: Optional[int], run_all: bool, verbose: bool):
    """Run TPCH queries. If no query number is provided, runs all queries."""
    repo_root = get_repo_root()
    tpch_path = os.path.join(repo_root, "examples/builder/tpch/runner.py")

    # Build pytest arguments
    pytest_args = [tpch_path, "-s"]  # -s shows output in real-time
    if verbose:
        pytest_args.append("-v")

    if query_num is not None:
        pytest_args.extend(["-k", f"test_query[{query_num}]"])

    divider()
    rich.print("[yellow bold]Running TPCH queries")
    rich.print(f"[yellow]Query: {'All' if query_num is None else query_num}")
    rich.print("")

    # Run pytest
    result = subprocess.run(["pytest"] + pytest_args)

    divider()
    sys.exit(result.returncode)
