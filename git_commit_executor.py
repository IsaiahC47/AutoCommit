#!/usr/bin/env python3
"""
Executor script for scheduled git commits.
Called by launchd with folder and repo paths as arguments.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schedule_git_commit import commit_folder

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: git_commit_executor.py <folder_path> <repo_path>")
        sys.exit(1)
    folder_path = sys.argv[1]
    repo_path = sys.argv[2]
    commit_folder(folder_path, repo_path)

