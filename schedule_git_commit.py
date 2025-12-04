#!/usr/bin/env python3
"""
Interactive script to schedule a git commit for any folder at any time.
"""

import subprocess
import sys
import os
from datetime import datetime
import plistlib

def commit_folder(folder_path, repo_path):
    """Commit the specified folder to git."""
    # Change to the repository directory
    os.chdir(repo_path)
    
    # Get relative path of folder from repo root
    folder_name = os.path.basename(os.path.abspath(folder_path))
    relative_path = os.path.relpath(os.path.abspath(folder_path), os.path.abspath(repo_path))
    
    try:
        # Check if we're in a git repository
        subprocess.run(["git", "status"], check=True, capture_output=True)
        
        # Add the folder
        result = subprocess.run(
            ["git", "add", relative_path + "/"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error adding files: {result.stderr}", file=sys.stderr)
            return False
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True
        )
        if result.returncode == 0:
            print("No changes to commit.")
            return True
        
        # Commit with a message
        commit_message = f"Auto-commit {folder_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error committing: {result.stderr}", file=sys.stderr)
            return False
        
        print(f"Successfully committed {folder_name}!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

def find_git_repo(path):
    """Find the git repository root containing the given path."""
    current = os.path.abspath(path)
    while current != os.path.dirname(current):  # Stop at filesystem root
        if os.path.exists(os.path.join(current, ".git")):
            return current
        current = os.path.dirname(current)
    return None

def get_user_input():
    """Get folder path and schedule from user."""
    print("=" * 60)
    print("Git Commit Scheduler")
    print("=" * 60)
    print()
    
    # Get folder path
    while True:
        folder_input = input("Enter the folder path to commit: ").strip()
        if not folder_input:
            print("Please enter a valid folder path.")
            continue
        
        # Expand ~ and resolve path
        folder_path = os.path.expanduser(folder_input)
        folder_path = os.path.abspath(folder_path)
        
        if not os.path.exists(folder_path):
            print(f"Error: Path '{folder_path}' does not exist.")
            continue
        
        if not os.path.isdir(folder_path):
            print(f"Error: '{folder_path}' is not a directory.")
            continue
        
        # Find git repository
        repo_path = find_git_repo(folder_path)
        if not repo_path:
            print(f"Error: No git repository found containing '{folder_path}'")
            print("Please make sure the folder is inside a git repository.")
            continue
        
        print(f"✓ Found git repository at: {repo_path}")
        break
    
    # Get date
    while True:
        date_input = input("\nEnter date (YYYY-MM-DD) or press Enter for today: ").strip()
        if not date_input:
            target_date = datetime.now().date()
        else:
            try:
                target_date = datetime.strptime(date_input, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD (e.g., 2024-12-04)")
                continue
        
        if target_date < datetime.now().date():
            print("Date must be today or in the future.")
            continue
        
        break
    
    # Get time
    while True:
        time_input = input("Enter time (HH:MM) in 24-hour format (e.g., 04:00): ").strip()
        try:
            hour, minute = map(int, time_input.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            print("Invalid time format. Please use HH:MM (e.g., 04:00)")
            continue
        
        break
    
    # Combine date and time
    target_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
    
    if target_datetime < datetime.now():
        print(f"Warning: {target_datetime} is in the past. Using tomorrow instead.")
        target_datetime = target_datetime.replace(day=target_datetime.day + 1)
    
    return folder_path, repo_path, target_datetime

def create_launchd_plist(folder_path, repo_path, target_datetime, script_path):
    """Create a launchd plist file for scheduling the commit."""
    folder_name = os.path.basename(os.path.abspath(folder_path))
    relative_path = os.path.relpath(os.path.abspath(folder_path), os.path.abspath(repo_path))
    
    # Create a unique label based on folder and timestamp
    label = f"com.gitcommit.{folder_name.lower().replace(' ', '').replace('-', '')}.{target_datetime.strftime('%Y%m%d%H%M')}"
    
    # Find the actual python3 path
    try:
        python3_path = subprocess.check_output(["which", "python3"], text=True).strip()
    except subprocess.CalledProcessError:
        # Fallback to common paths
        python3_path = "/usr/bin/python3"
    
    # Ensure all paths are absolute
    script_path = os.path.abspath(script_path)
    folder_path = os.path.abspath(folder_path)
    repo_path = os.path.abspath(repo_path)
    script_dir = os.path.dirname(script_path)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    plist_data = {
        "Label": label,
        "ProgramArguments": [
            python3_path,
            script_path,
            folder_path,
            repo_path
        ],
        "StartCalendarInterval": {
            "Month": target_datetime.month,
            "Day": target_datetime.day,
            "Hour": target_datetime.hour,
            "Minute": target_datetime.minute
        },
        "StandardOutPath": os.path.join(logs_dir, f"commit_{folder_name}_{target_datetime.strftime('%Y%m%d_%H%M')}.log"),
        "StandardErrorPath": os.path.join(logs_dir, f"commit_{folder_name}_{target_datetime.strftime('%Y%m%d_%H%M')}_error.log"),
        "RunAtLoad": False
    }
    
    # Save plist to LaunchAgents
    launchd_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(launchd_dir, exist_ok=True)
    plist_path = os.path.join(launchd_dir, f"{label}.plist")
    
    with open(plist_path, "wb") as f:
        plistlib.dump(plist_data, f)
    
    return plist_path, label

def main():
    """Main function."""
    # Get user input
    folder_path, repo_path, target_datetime = get_user_input()
    
    # Create the commit script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    commit_script = os.path.join(script_dir, "git_commit_executor.py")
    
    # Create executor script if it doesn't exist
    if not os.path.exists(commit_script):
        executor_content = '''#!/usr/bin/env python3
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
'''
        with open(commit_script, "w") as f:
            f.write(executor_content)
        os.chmod(commit_script, 0o755)
    
    # Create launchd plist
    plist_path, label = create_launchd_plist(folder_path, repo_path, target_datetime, commit_script)
    
    # Load the launchd job
    try:
        result = subprocess.run(
            ["launchctl", "load", plist_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"\nError loading scheduler: {result.stderr}")
            return False
    except Exception as e:
        print(f"\nError loading scheduler: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Scheduler installed successfully!")
    print("=" * 60)
    print(f"Folder: {folder_path}")
    print(f"Scheduled for: {target_datetime.strftime('%Y-%m-%d %H:%M')}")
    print(f"Plist: {plist_path}")
    print()
    print("To check status: launchctl list | grep " + label)
    print("To uninstall: launchctl unload " + plist_path)
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)

