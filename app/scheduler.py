#!/usr/bin/env python3
"""
Python-based scheduler for TSSK.
Replaces cron to allow running without root privileges.

This script schedules tssk.py to run at configured intervals.
"""

import os
import sys
import subprocess
import shutil
import yaml
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import re

# Ensure unbuffered output for real-time logging in Docker
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
else:
    os.environ['PYTHONUNBUFFERED'] = '1'

# Environment variables
APP_TIMES = os.getenv("APP_TIMES", "02:00")
RUN_AT_START = os.getenv("RUN_AT_START", "true").lower() in ("true", "1", "yes")

# Hardcoded log file location
LOG_FILE = "/app/logs/tssk.log"

def load_config():
    """Load config file to get log_retention_runs"""
    config_path = "/app/data/config.yml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def get_log_retention_runs():
    """Get log retention runs from config, default to 7"""
    config = load_config()
    retention = config.get('log_retention_runs', 7)
    try:
        retention = int(retention)
        if retention < 1:
            retention = 7
    except (ValueError, TypeError):
        retention = 7
    return retention

def rotate_logs():
    """Rotate log file before each run."""
    log_path = Path(LOG_FILE)
    log_retention_runs = get_log_retention_runs()
    
    if not log_path.exists():
        # Ensure log directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return
    
    log_dir = log_path.parent
    log_base = log_path.stem  # filename without extension
    log_ext = log_path.suffix  # .log
    
    # Remove oldest log if we're at the retention limit
    oldest_log = log_dir / f"{log_base}-{log_retention_runs}{log_ext}"
    if oldest_log.exists():
        oldest_log.unlink()
    
    # Shift existing rotated logs backwards (move .2 to .3, .1 to .2, etc.)
    for i in range(log_retention_runs, 1, -1):
        prev = i - 1
        prev_log = log_dir / f"{log_base}-{prev}{log_ext}"
        curr_log = log_dir / f"{log_base}-{i}{log_ext}"
        
        # Move previous to current position
        if prev_log.exists():
            shutil.move(str(prev_log), str(curr_log))
    
    # Move the current log to -1.log
    if log_path.exists():
        rotated_log = log_dir / f"{log_base}-1{log_ext}"
        shutil.move(str(log_path), str(rotated_log))

def log_message(message):
    """Append a message to the log file with timestamp."""
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    
    # Write to log file
    try:
        with open(log_path, 'a') as f:
            f.write(log_line)
            f.flush()
    except Exception:
        pass  # Silently fail if we can't write to log file
    
    # Also print to stdout for Docker logs
    print(log_line.rstrip(), flush=True)

def run_tssk():
    """Run the tssk.py script."""
    # Rotate logs before running
    rotate_logs()
    
    # Log run start
    log_message("=" * 60)
    log_message(f"Started scheduled run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message("=" * 60)
    
    # Print to stdout for Docker logs visibility
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"{timestamp}| Starting TSSK run...", flush=True)
    
    # Change to app directory
    os.chdir("/app")
    
    # Build command
    cmd = [sys.executable, "-u", "tssk.py"]
    
    # Run the script and capture output
    try:
        log_path = Path(LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run with unbuffered output - write to both log file and stdout for visibility
        with open(LOG_FILE, 'a') as log_f:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Stream output to both log file and stdout
            for line in process.stdout:
                log_f.write(line)
                log_f.flush()
                print(line.rstrip(), flush=True)
            
            exit_code = process.wait()
        
        # Log completion
        log_message(f"Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_message(f"Exit code: {exit_code}")
        log_message("")
        
        # Print completion to stdout
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"{timestamp}| Run completed with exit code: {exit_code}", flush=True)
        
        return exit_code
    except Exception as e:
        error_msg = f"ERROR running script: {e}"
        log_message(error_msg)
        log_message("")
        
        # Print error to stdout
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"{timestamp}| {error_msg}", flush=True)
        
        return 1

def parse_schedule(time_str):
    """
    Parse military time format (HH:MM) into CronTrigger parameters.
    
    Format: HH:MM (24-hour format)
    Examples:
        "02:00"         -> daily at 2 AM
        "14:00"         -> daily at 2 PM
        "00:30"         -> daily at 12:30 AM
    
    Returns dict with fields for apscheduler CronTrigger.
    """
    time_str = time_str.strip()
    
    # Match HH:MM format where HH is 00-23 and MM is 00-59
    pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
    if not re.match(pattern, time_str):
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM format (e.g., 02:00, 14:00)")
    
    hour_str, minute_str = time_str.split(':')
    hour = int(hour_str)
    minute = int(minute_str)
    
    # Validate ranges (should already be validated by regex, but double-check)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid time values: hour={hour}, minute={minute}")
    
    # Return parameters for daily schedule (minute hour day month weekday)
    # Use None for "*" (any value) for day, month, and weekday
    return {
        "minute": str(minute),
        "hour": str(hour),
        "day": None,  # "*" -> None for any day
        "month": None,  # "*" -> None for any month
        "day_of_week": None,  # "*" -> None for any weekday
    }

def format_time_display(time_str):
    """
    Convert military time (HH:MM) to readable format.
    Examples: "02:00" -> "Daily at 02:00", "14:30" -> "Daily at 14:30"
    """
    return f"Daily at {time_str}"

def main():
    """Main scheduler entry point."""
    # Parse APP_TIMES - support comma-separated multiple schedules
    # Split by comma and strip whitespace
    schedule_strings = [s.strip() for s in APP_TIMES.split(",") if s.strip()]
    
    if not schedule_strings:
        print(f"ERROR: APP_TIMES is empty or invalid: '{APP_TIMES}'", file=sys.stderr)
        sys.exit(1)
    
    triggers = []
    for idx, schedule_str in enumerate(schedule_strings):
        try:
            # Store original format for display
            original_format = schedule_str
            schedule_params = parse_schedule(schedule_str)
            # Create CronTrigger - apscheduler accepts None for "*" (any value)
            trigger = CronTrigger(
                minute=schedule_params["minute"],
                hour=schedule_params["hour"],
                day=schedule_params["day"],
                month=schedule_params["month"],
                day_of_week=schedule_params["day_of_week"],
            )
            triggers.append((trigger, original_format))
        except Exception as e:
            print(f"ERROR: Failed to parse schedule '{schedule_str}' in APP_TIMES: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Display formatted startup banner
    banner_width = 100
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    content_width = banner_width - len(timestamp) - 1  # -1 for the pipe at the end
    
    # First border line (no timestamp)
    print("|" + "=" * (banner_width - 2) + "|", flush=True)
    
    # Title line (with timestamp)
    title = "TSSK Continuous Scheduled"
    title_padding = (content_width - len(title)) // 2
    print(f"{timestamp}|{' ' * title_padding}{title}{' ' * (content_width - len(title) - title_padding)}|", flush=True)
    
    # Second border line (with timestamp)
    print(f"{timestamp}|{'=' * (banner_width - len(timestamp) - 2)}|", flush=True)
    
    # Empty line
    print(f"{timestamp}|{' ' * content_width}|", flush=True)
    
    # Scheduled Runs header
    print(f"{timestamp}|{'Scheduled Runs:':<{content_width}}|", flush=True)
    
    # Display each scheduled run
    for trigger, schedule_str in triggers:
        display_text = format_time_display(schedule_str)
        print(f"{timestamp}| * {display_text:<{content_width - 3}}|", flush=True)
    
    # Empty line
    print(f"{timestamp}|{' ' * content_width}|", flush=True)
    
    # Final border line (with timestamp)
    print(f"{timestamp}|{'=' * (banner_width - len(timestamp) - 2)}|", flush=True)
    
    # Final empty line
    print(f"{timestamp}|{' ' * content_width}|", flush=True)
    
    # Run at start if configured
    if RUN_AT_START:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"{timestamp}| Running initial scan at startup...", flush=True)
        run_tssk()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"{timestamp}| Initial run complete. Scheduler will continue on schedule.", flush=True)
        print(flush=True)
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Add scheduled jobs for each trigger
    for idx, (trigger, schedule_str) in enumerate(triggers):
        job_id = f"tssk-{idx}"
        scheduler.add_job(
            run_tssk,
            trigger=trigger,
            id=job_id,
            name=f"Run TSSK ({schedule_str})",
            replace_existing=True
        )
    
    # Flush all output before starting the blocking scheduler
    sys.stdout.flush()
    sys.stderr.flush()
    
    try:
        # Run scheduler (blocks until stopped)
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"\n{timestamp}| Scheduler stopped.", flush=True)
        scheduler.shutdown()
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        print(f"{timestamp}| ERROR: Scheduler failed: {e}", flush=True, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

