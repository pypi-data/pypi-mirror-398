#!/usr/bin/env python
"""
Snapshot Viewer Tool

This tool generates an HTML report that displays test code and its corresponding
snapshots side by side, making it easier to review snapshot tests.

Usage:
  python tools/snapshot_viewer.py [--output report.html] [--test-dir tests/unit/]
"""

import argparse
import os
import tempfile
import webbrowser
import subprocess
from dataclasses import dataclass
from typing import List, Optional, cast
import json

@dataclass
class TestInfo:
    """Information about a test function."""
    file_path: str
    function_name: str
    class_name: Optional[str]
    code: str
    line_number: int
    snapshot_names: List[str]

@dataclass
class SnapshotInfo:
    """Information about a snapshot file."""
    file_path: str
    content: str
    original_content: Optional[str] = None
    test_info: Optional[TestInfo] = None
    is_modified: bool = False

def generate_html_report(tests, snapshots, output_path):
    """Generate an HTML report of the tests and their snapshots."""
    print("Generating HTML report...")

    # Create HTML content
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Snapshot Test Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background-color: #333;
                color: white;
                padding: 10px 20px;
                margin-bottom: 20px;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            .test-container {
                background-color: white;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                overflow: hidden;
            }
            .test-header {
                background-color: #f0f0f0;
                padding: 10px 15px;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            .test-content {
                display: flex;
                flex-wrap: wrap;
            }
            .test-code {
                flex: 1;
                min-width: 300px;
                padding: 15px;
                border-right: 1px solid #eee;
                white-space: pre-wrap;
                font-family: monospace;
                overflow-x: auto;
            }
            .snapshot-container {
                flex: 1;
                min-width: 300px;
                padding: 15px;
            }
            .snapshot {
                margin-bottom: 20px;
                border: 1px solid #eee;
                border-radius: 3px;
                overflow: hidden;
            }
            .snapshot-header {
                background-color: #f9f9f9;
                padding: 8px 12px;
                border-bottom: 1px solid #eee;
                font-size: 14px;
                font-weight: bold;
                display: flex;
                flex-direction: row;
                justify-content: space-between;
                align-items: center;
            }
            .snapshot-content {
                padding: 12px;
                white-space: pre-wrap;
                font-family: monospace;
                overflow-x: auto;
                max-height: 500px;
                overflow-y: auto;
            }
            .modified {
                background-color: #fff8e1;
            }
            .no-snapshots {
                padding: 15px;
                color: #999;
                font-style: italic;
            }
            .search-container {
                margin-bottom: 20px;
            }
            #search {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
            }
            .nav-button {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 15px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            }
            .nav-button:hover {
                background-color: #45a049;
            }
            .nav-button:disabled {
                background-color: #cccccc;
                cursor: not-allowed;
            }
            .fixed-nav {
                position: fixed;
                bottom: 20px;
                right: 20px;
                display: flex;
                gap: 10px;
                z-index: 100;
            }
            .toggle-version-btn {
                padding: 5px 10px;
                background-color: #555;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
            }
            .toggle-version-btn:hover {
                background-color: #333;
            }
            .toggle-version-btn.active {
                background-color: #4CAF50;
            }
            .original-content {
                display: none;
            }
            .button-pair {
                display: flex;
                gap: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Snapshot Test Report</h1>

            <div class="search-container">
                <input type="text" id="search" placeholder="Search for tests or snapshots...">
            </div>
            <div id="tests">
    """

    # Sort tests by file path and function name
    sorted_tests = sorted(tests, key=lambda t: (t.file_path, t.function_name))

    # Add each test to the HTML
    for test in sorted_tests:
        # Find snapshots for this test
        test_snapshots = []
        for path, info in snapshots.items():
            if info.test_info and info.test_info.file_path == test.file_path and info.test_info.function_name == test.function_name:
                test_snapshots.append(info)

        # Create test container
        html += f"""
        <div class="test-container" data-test="{test.function_name}" data-file="{os.path.basename(test.file_path)}">
            <div class="test-header">
                {"".join(test.file_path.split("/tests/")[1:])} - {test.function_name}
            </div>
            <div class="test-content">
                <div class="test-code">{test.code}</div>
                <div class="snapshot-container">
        """

        # Add each snapshot for this test
        for snapshot_name in test.snapshot_names:
            # Find the snapshot file
            snapshot_file = None
            for path, info in snapshots.items():
                if info.test_info and info.test_info.file_path == test.file_path and info.test_info.function_name == test.function_name:
                    if os.path.splitext(os.path.basename(path))[0] == snapshot_name:
                        snapshot_file = path
                        break

            if snapshot_file:
                snapshot_info = snapshots[snapshot_file]
                is_modified = snapshot_info.is_modified
                has_original = is_modified and snapshot_info.original_content is not None

                snapshot_id = f"snapshot_{test.function_name}_{snapshot_name}".replace('.', '_')

                buttons = f"""<div class="button-pair"><button id="toggle-original-{snapshot_id}" class="toggle-version-btn" onclick="toggleVersion('{snapshot_id}', 'original')">Original</button><button id="toggle-current-{snapshot_id}" class="toggle-version-btn active" onclick="toggleVersion('{snapshot_id}', 'current')">Current</button></div>"""

                html += f"""
                <div class="snapshot">
                    <div class="snapshot-header{' modified' if is_modified else ''}">
                        {snapshot_name}{' (Modified)' if is_modified else ''}
                        {buttons if has_original else ''}
                    </div>
                """

                # If the snapshot is modified and we have the original content, add toggle button
                if has_original:
                    html += f"""

                    <div id="{snapshot_id}_original" class="snapshot-content original-content">
                        {html_escape(snapshot_info.original_content)}
                    </div>
                    <div id="{snapshot_id}_current" class="snapshot-content">
                        {html_escape(snapshot_info.content)}
                    </div>
                    """
                else:
                    # Just show the current content
                    html += f"""
                    <div class="snapshot-content">{html_escape(snapshot_info.content)}</div>
                    """

                html += """
                </div>
                """

        html += """
                </div>
            </div>
        </div>
        """

    html += """
            </div>
        </div>
        <div class="fixed-nav">
            <button id="prevButton" class="nav-button">Previous</button>
            <button id="nextButton" class="nav-button">Next</button>
        </div>
        <script>
            document.getElementById('search').addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                const tests = document.querySelectorAll('.test-container');

                tests.forEach(test => {
                    const testName = test.getAttribute('data-test').toLowerCase();
                    const fileName = test.getAttribute('data-file').toLowerCase();
                    const content = test.textContent.toLowerCase();

                    if (testName.includes(searchTerm) || fileName.includes(searchTerm) || content.includes(searchTerm)) {
                        test.style.display = '';
                    } else {
                        test.style.display = 'none';
                    }
                });
            });

            // Navigation functionality
            const snapshots = document.querySelectorAll('.snapshot');
            let currentIndex = -1;

            function navigateToSnapshot(index) {
                if (index >= 0 && index < snapshots.length) {
                    if (currentIndex >= 0 && currentIndex < snapshots.length) {
                        snapshots[currentIndex].style.border = '1px solid #eee';
                    }

                    currentIndex = index;
                    const snapshot = snapshots[currentIndex];
                    snapshot.style.border = '2px solid #4CAF50';
                    snapshot.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }

                // Update button states
                const prevButton = document.getElementById('prevButton');
                if (prevButton) {
                    prevButton.disabled = currentIndex <= 0;
                }
                const nextButton = document.getElementById('nextButton');
                if (nextButton) {
                    nextButton.disabled = currentIndex >= snapshots.length - 1;
                }
            }

            function navigateNext() {
                navigateToSnapshot(currentIndex + 1);
            }

            function navigatePrevious() {
                navigateToSnapshot(currentIndex - 1);
            }

            // Initialize navigation
            document.getElementById('prevButton')?.addEventListener('click', navigatePrevious);
            document.getElementById('nextButton')?.addEventListener('click', navigateNext);

            // Start at the first snapshot
            if (snapshots.length > 0) {
                navigateToSnapshot(0);
            } else {
                const prevButton = document.getElementById('prevButton');
                if (prevButton) {
                    prevButton.disabled = true;
                }
                const nextButton = document.getElementById('nextButton');
                if (nextButton) {
                    nextButton.disabled = true;
                }
            }

            // Toggle between original and current version
            function toggleVersion(snapshotId, version) {
                const originalElement = document.getElementById(snapshotId + '_original');
                const currentElement = document.getElementById(snapshotId + '_current');

                if (version === 'original') {
                    originalElement.style.display = 'block';
                    currentElement.style.display = 'none';
                } else {
                    originalElement.style.display = 'none';
                    currentElement.style.display = 'block';
                }
                const button = document.getElementById("toggle-" + version + "-" + snapshotId);
                const otherButton = document.getElementById("toggle-" + (version === 'original' ? 'current' : 'original') + "-" + snapshotId);
                button.classList.add('active');
                otherButton.classList.remove('active');
            }
        </script>
    </body>
    </html>
    """

    # Write the HTML to the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def mark_modified_snapshots(snapshots):
    """Mark snapshots that are modified according to git."""
    try:
        # Get both staged and unstaged changes
        staged = subprocess.check_output(['git', 'diff', '--name-only', '--cached']).decode('utf-8').splitlines()
        unstaged = subprocess.check_output(['git', 'diff', '--name-only']).decode('utf-8').splitlines()
        untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard']).decode('utf-8').splitlines()

        # Combine all changes
        modified_files = set(staged + unstaged + untracked)

        # Mark modified snapshots
        for name, info in snapshots.items():
            info.is_modified = info.file_path in modified_files

        return True
    except subprocess.CalledProcessError:
        return False

def load_snapshot_registry():
    """Load the snapshot registry from the .pytest_snapshot_data directory."""
    registry_path = os.path.join(os.getcwd(), ".pytest_snapshot_data", "registry.json")
    print(f"Looking for registry at: {registry_path}")

    if not os.path.exists(registry_path):
        print(f"Registry file not found at {registry_path}")
        return None

    try:
        with open(registry_path, 'r') as f:
            registry = json.load(f)

        print(f"Loaded registry with {len(registry)} test entries")

        return registry
    except Exception as e:
        print(f"Error loading registry: {e}")
        return None

def extract_test_info_from_registry(registry):
    """Extract test information from the registry."""
    tests = []
    for test_id, test_data in registry.items():
        # Skip tests with no snapshots
        if not test_data["snapshots"]:
            continue

        # Read the test code from the file
        try:
            with open(test_data["file_path"], 'r') as f:
                file_content = f.read()

            # Extract the function code - get the whole function
            line_number = test_data["line_number"]
            lines = file_content.splitlines()

            # Find the end of the function
            function_lines = []
            indent_level = None
            for i in range(line_number - 1, len(lines)):
                line = lines[i]

                # Skip empty lines at the beginning
                if not line.strip() and not function_lines:
                    continue

                # Determine the indentation level of the function
                if indent_level is None and line.strip():
                    indent_level = len(line) - len(line.lstrip())

                # Add the line to the function
                function_lines.append(line)

                # Check if we've reached the end of the function
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= cast(int, indent_level):
                        break

            function_code = '\n'.join(function_lines)

            # Create a TestInfo object with normalized snapshot paths
            snapshot_names = []
            for snapshot_path in test_data["snapshots"]:
                # Extract just the filename without extension
                snapshot_file = os.path.basename(snapshot_path)
                snapshot_name = os.path.splitext(snapshot_file)[0]
                snapshot_names.append(snapshot_name)

            test = TestInfo(
                file_path=test_data["file_path"],
                function_name=test_data["function_name"],
                class_name=test_data["class_name"],
                code=function_code,
                line_number=test_data["line_number"],
                snapshot_names=snapshot_names
            )
            tests.append(test)
        except Exception as e:
            print(f"Error extracting test info for {test_id}: {e}")

    return tests

def match_tests_with_snapshots_from_registry(tests, snapshots, registry):
    """Match tests with snapshots using the registry."""
    matched_tests = []
    matched_snapshots = {}

    # Create a mapping of snapshot filenames to their full paths
    snapshot_filename_map = {}
    for snapshot_file, info in snapshots.items():
        filename = os.path.basename(snapshot_file)
        snapshot_filename_map[filename] = snapshot_file

    # For each test, find its snapshots
    for test in tests:
        has_snapshot = False

        # Get the test's registry entry
        test_id = None
        for tid, data in registry.items():
            if (data["function_name"] == test.function_name and
                data["file_path"] == test.file_path and
                data["class_name"] == test.class_name):
                test_id = tid
                break

        if test_id:
            # Get the snapshots for this test
            for snapshot_path in registry[test_id]["snapshots"]:
                snapshot_file = os.path.basename(snapshot_path)

                # Find the snapshot in our snapshots dict
                if snapshot_file in snapshot_filename_map:
                    full_path = snapshot_filename_map[snapshot_file]
                    has_snapshot = True
                    snapshots[full_path].test_info = test
                    matched_snapshots[full_path] = snapshots[full_path]

        if has_snapshot:
            matched_tests.append(test)

    return matched_tests, matched_snapshots

def process_snapshots_from_registry(registry, test_dir):
    """Process snapshots using the registry information directly."""
    all_tests = []
    matched_snapshots = {}

    # First, find all snapshot files
    all_snapshots = {}
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.snapshot'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    all_snapshots[file_path] = SnapshotInfo(file_path=file_path, content=content)
                except Exception as e:
                    print(f"Error reading snapshot file {file_path}: {e}")

    # Process each test in the registry
    for test_id, test_data in registry.items():
        # Skip tests with no snapshots
        if not test_data["snapshots"]:
            continue

        # Extract test information
        try:
            with open(test_data["file_path"], 'r') as f:
                file_content = f.read()

            # Extract the function code
            line_number = test_data["line_number"]
            lines = file_content.splitlines()

            # Find the end of the function
            function_lines = []
            indent_level = None
            for i in range(line_number - 1, len(lines)):
                line = lines[i]

                # Skip empty lines at the beginning
                if not line.strip() and not function_lines:
                    continue

                # Determine the indentation level of the function
                if indent_level is None and line.strip():
                    indent_level = len(line) - len(line.lstrip())

                # Add the line to the function
                function_lines.append(line)

                # Check if we've reached the end of the function
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= cast(int, indent_level):
                        break

            function_code = '\n'.join(function_lines)

            # Create a TestInfo object
            test = TestInfo(
                file_path=test_data["file_path"],
                function_name=test_data["function_name"],
                class_name=test_data["class_name"],
                code=function_code,
                line_number=test_data["line_number"],
                snapshot_names=[os.path.splitext(os.path.basename(s))[0] for s in test_data["snapshots"]]
            )

            # Add the test to our list
            all_tests.append(test)

            # Match the test with its snapshots
            for snapshot_path in test_data["snapshots"]:
                # Normalize the path to handle different path formats
                normalized_path = os.path.normpath(snapshot_path)

                # Try to find the snapshot in all_snapshots
                if normalized_path in all_snapshots:
                    all_snapshots[normalized_path].test_info = test
                    matched_snapshots[normalized_path] = all_snapshots[normalized_path]
                else:
                    # Try to match by basename
                    basename = os.path.basename(normalized_path)
                    for path, info in all_snapshots.items():
                        if os.path.basename(path) == basename:
                            info.test_info = test
                            matched_snapshots[path] = info
                            break

        except Exception as e:
            print(f"Error processing test {test_id}: {e}")

    return all_tests, matched_snapshots

def generate_report_from_registry(registry, snapshot_files, output_path):
    """Generate an HTML report using the registry information."""
    print("Generating report from registry...")

    def from_repo(file_path):
        return "".join(file_path.split("/relationalai-python/")[1])

    # Load all snapshot files
    all_snapshots = {}
    for file_path in snapshot_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            all_snapshots[file_path] = SnapshotInfo(file_path=from_repo(file_path), content=content)
            # Also add with normalized path
            norm_path = os.path.normpath(file_path)
            all_snapshots[norm_path] = SnapshotInfo(file_path=from_repo(file_path), content=content)
        except Exception as e:
            print(f"Error reading snapshot file {file_path}: {e}")

    print(f"Loaded {len(snapshot_files)} snapshot files")
    # Mark modified snapshots and get original content
    mark_modified_snapshots(all_snapshots)
    for path, info in all_snapshots.items():
        if info.is_modified:
            info.original_content = get_original_snapshot_content(info.file_path)

    # Process each test in the registry
    all_tests = []
    matched_snapshots = {}

    for test_id, test_data in registry.items():
        # Skip tests with no snapshots
        if not test_data.get("snapshots") or len(test_data["snapshots"]) == 0:
            continue

        # Extract test information
        try:
            with open(test_data["file_path"], 'r') as f:
                file_content = f.read()

            # Extract the function code
            line_number = test_data["line_number"]
            lines = file_content.splitlines()

            # Find the end of the function
            function_lines = []
            indent_level = None
            for i in range(line_number - 1, len(lines)):
                line = lines[i]

                # Skip empty lines at the beginning
                if not line.strip() and not function_lines:
                    continue

                # Determine the indentation level of the function
                if indent_level is None and line.strip():
                    indent_level = len(line) - len(line.lstrip())

                # Add the line to the function
                function_lines.append(line)

                # Check if we've reached the end of the function
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= cast(int, indent_level):
                        break

            function_code = '\n'.join(function_lines)

            # Create a TestInfo object
            test = TestInfo(
                file_path=test_data["file_path"],
                function_name=test_data["function_name"],
                class_name=test_data.get("class_name"),
                code=function_code,
                line_number=line_number,
                snapshot_names=[]
            )

            # Process each snapshot for this test
            found_snapshots = False
            for snapshot_path in test_data["snapshots"]:
                # Check if this snapshot is in our filtered list
                norm_path = os.path.normpath(snapshot_path)

                if norm_path in all_snapshots:
                    # Add the snapshot to the test
                    name_without_ext = os.path.splitext(os.path.basename(norm_path))[0]
                    test.snapshot_names.append(name_without_ext)
                    all_snapshots[norm_path].test_info = test
                    matched_snapshots[norm_path] = all_snapshots[norm_path]
                    found_snapshots = True

            # If we found snapshots, add the test
            if found_snapshots:
                all_tests.append(test)

        except Exception as e:
            print(f"Error processing test {test_id}: {e}")

    print(f"Found {len(all_tests)} tests with {len(matched_snapshots)} snapshots")

    # Generate HTML report
    generate_html_report(all_tests, matched_snapshots, output_path)

def html_escape(text):
    """Escape HTML special characters."""
    if text is None:
        return ""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def get_original_snapshot_content(snapshot_path):
    """Get the original content of a snapshot from Git."""
    try:
        # Try to get the content from the last commit
        original_content = subprocess.check_output(
            ['git', 'show', f'HEAD:{snapshot_path}'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8')
        return original_content
    except subprocess.CalledProcessError:
        # File might be new and not in Git yet
        return None

def main():
    parser = argparse.ArgumentParser(description='Generate an HTML report of snapshot tests')
    parser.add_argument('--output', default=None, help='Output HTML file (defaults to a temp file)')
    parser.add_argument('--test-dir', default='tests/unit/', help='Test directory to scan')

    args = parser.parse_args()

    # Create a temporary file for the HTML report if not specified
    if not args.output:
        temp_dir = tempfile.mkdtemp()
        args.output = os.path.join(temp_dir, "snapshot_report.html")

    # Use the registry to get test information
    registry = load_snapshot_registry()
    if not registry:
        print("No snapshot registry found. Run tests first to create it.")
        return

    # Generate the report using the registry
    generate_report_from_registry(registry, args.test_dir, args.output)

    print(f"Report generated: {args.output}")

    # Open the report in the default browser
    webbrowser.open(f"file://{os.path.abspath(args.output)}")

if __name__ == '__main__':
    main()