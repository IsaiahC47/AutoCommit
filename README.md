# AutoCommit

A Python-based tool for scheduling automatic git commits on macOS. This program allows you to schedule git commits for specific folders at any future date and time using macOS's `launchd` scheduler.

## Overview

AutoCommit consists of two main components:

1. **`schedule_git_commit.py`** - An interactive script that prompts for folder paths and schedules commits
2. **`git_commit_executor.py`** - An executor script that performs the actual git commit when triggered by launchd

## How It Works

### 1. Interactive Scheduling (`schedule_git_commit.py`)

When you run `schedule_git_commit.py`, it will:

1. **Prompt for folder path**: Enter the path to the folder you want to commit
   - The script automatically finds the git repository containing that folder
   - Validates that the path exists and is within a git repository

2. **Prompt for date and time**: 
   - Enter a date in `YYYY-MM-DD` format (or press Enter for today)
   - Enter a time in `HH:MM` 24-hour format (e.g., `04:00` for 4:00 AM)
   - The script validates that the scheduled time is in the future

3. **Create launchd plist**: 
   - Generates a unique launchd plist file in `~/Library/LaunchAgents/`
   - The plist is configured to run the executor script at the specified time
   - Logs are created for both standard output and errors

4. **Load the scheduler**: 
   - Automatically loads the plist into launchd using `launchctl load`
   - The commit will execute automatically at the scheduled time

### 2. Commit Execution (`git_commit_executor.py`)

When launchd triggers the scheduled job:

1. **Changes to repository directory**: Navigates to the git repository root
2. **Adds files**: Stages all files in the specified folder using `git add`
3. **Checks for changes**: Verifies there are actually changes to commit
4. **Creates commit**: Commits with an automatic message like:
   ```
   Auto-commit <folder_name> - 2024-12-04 14:30:00
   ```

## Requirements

- **macOS**: Uses `launchd` and `launchctl` (macOS-specific)
- **Python 3**: Requires Python 3 with standard library modules
- **Git**: Must have git installed and the target folder must be within a git repository

## Usage

### Basic Usage

```bash
python3 schedule_git_commit.py
```

Follow the interactive prompts:
1. Enter the folder path to commit
2. Enter the date (YYYY-MM-DD) or press Enter for today
3. Enter the time (HH:MM) in 24-hour format

### Example Session

```
============================================================
Git Commit Scheduler
============================================================

Enter the folder path to commit: ~/Documents/myproject/src
✓ Found git repository at: /Users/username/Documents/myproject

Enter date (YYYY-MM-DD) or press Enter for today: 2024-12-05
Enter time (HH:MM) in 24-hour format (e.g., 04:00): 14:30

============================================================
✓ Scheduler installed successfully!
============================================================
Folder: /Users/username/Documents/myproject/src
Scheduled for: 2024-12-05 14:30
Plist: ~/Library/LaunchAgents/com.gitcommit.src.202412051430.plist

To check status: launchctl list | grep com.gitcommit.src.202412051430
To uninstall: launchctl unload ~/Library/LaunchAgents/com.gitcommit.src.202412051430.plist
============================================================
```

## Managing Scheduled Commits

### Check Status

```bash
launchctl list | grep com.gitcommit
```

### Uninstall a Scheduled Commit

```bash
launchctl unload ~/Library/LaunchAgents/<plist_name>.plist
```

### View Logs

Logs are automatically created in the AutoCommit directory:
- `commit_<folder>_<timestamp>.log` - Standard output
- `commit_<folder>_<timestamp>_error.log` - Error output

## Features

- ✅ Automatic git repository detection
- ✅ Validates folder paths and git repository existence
- ✅ Prevents scheduling commits in the past
- ✅ Automatic commit message generation with timestamp
- ✅ Skips commits if there are no changes
- ✅ Comprehensive error handling
- ✅ Logging for debugging

## File Structure

```
AutoCommit/
├── schedule_git_commit.py    # Main interactive scheduling script
├── git_commit_executor.py    # Executor script called by launchd
└── README.md                 # This file
```

## Notes

- The commit only happens once at the scheduled time (not recurring)
- If there are no changes to commit, the script will skip the commit gracefully
- The script must have write permissions to the git repository
- Each scheduled commit creates a unique launchd job with a timestamp-based label

