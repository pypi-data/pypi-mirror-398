#!/usr/bin/env python
"""
Snapshot Cleanup Tool

This tool provides a simple way to clean up unused snapshot files by:
1. Removing all existing snapshots (with --remove)
2. Running the tests to regenerate needed snapshots (with --regenerate)

Usage:
  python tools/cleanup_snapshots.py [--test-dir tests/early_access/unit] [--remove] [--regenerate]
"""

import argparse
import os
import subprocess

def find_all_snapshot_files(test_dir: str):
    """Find all snapshot files in the test directory."""
    snapshots = []
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.snapshot'):
                file_path = os.path.join(root, file)
                snapshots.append(file_path)
    return snapshots

def remove_snapshots(test_dir: str):
    """Remove all snapshot files in the test directory."""
    snapshots = find_all_snapshot_files(test_dir)
    print(f"Found {len(snapshots)} snapshot files")

    if snapshots:
        print("\nRemoving snapshot files...")
        for snapshot_path in snapshots:
            os.remove(snapshot_path)
            print(f"  Removed {snapshot_path}")
        print(f"Removed {len(snapshots)} snapshot files")
    else:
        print("No snapshot files found to remove")

    return len(snapshots)

def regenerate_snapshots(test_dir: str):
    """Run tests to regenerate snapshots."""
    print("\nRegenerating snapshots by running tests...")

    # Build the pytest command
    cmd = ["pytest", test_dir, "--snapshot-update"]

    # Run the command
    try:
        subprocess.run(cmd, check=True)
        print("Tests completed successfully, snapshots regenerated")
    except subprocess.CalledProcessError:
        pass

    cmd = ["pytest", test_dir]

    # Run pytest again so we can see if there are errors
    try:
        subprocess.run(cmd, check=True)
        print("Tests completed successfully")
    except subprocess.CalledProcessError:
        print("Tests not regenerated successfully")


    # Count how many snapshots were regenerated
    new_snapshots = find_all_snapshot_files(test_dir)
    print(f"Regenerated {len(new_snapshots)} snapshot files")

    return len(new_snapshots)

def main():
    parser = argparse.ArgumentParser(description='Clean up unused snapshot files')
    parser.add_argument('--test-dir', default='tests/early_access/unit', help='Test directory to scan')
    parser.add_argument('--remove', action='store_true', help='Remove all snapshot files')
    parser.add_argument('--regenerate', action='store_true', help='Regenerate snapshots by running tests')

    args = parser.parse_args()

    if not args.remove and not args.regenerate:
        # Just count and report
        snapshots = find_all_snapshot_files(args.test_dir)
        print(f"Found {len(snapshots)} snapshot files")
        print("\nUse --remove to remove all snapshots")
        print("Use --regenerate to regenerate snapshots by running tests")
        return

    removed = 0
    if args.remove:
        removed = remove_snapshots(args.test_dir)

    regenerated = 0
    if args.regenerate:
        regenerated = regenerate_snapshots(args.test_dir)

    if args.remove and args.regenerate:
        print(f"\nSummary: Removed {removed} snapshots, regenerated {regenerated} snapshots")
        if removed > regenerated:
            print(f"Cleaned up {removed - regenerated} unused snapshots")

if __name__ == '__main__':
    main()