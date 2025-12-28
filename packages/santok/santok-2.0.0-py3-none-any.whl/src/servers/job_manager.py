"""
Job Manager for Asynchronous Code Execution
Allows code to continue running even if the browser tab is closed
"""

import json
import sys
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Progress calculation constants
PROGRESS_START = 10
PROGRESS_MAX = 90
PROGRESS_COMPLETE = 100
PROGRESS_UPDATE_INTERVAL = 5  # seconds
STDOUT_MAX_LINES = 100  # Maximum lines to keep in stdout

class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobManager:
    """Manages background job execution with persistent storage"""
    
    def __init__(self, jobs_dir: str = "jobs"):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(exist_ok=True)
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()
        # Cleanup old jobs on initialization
        self.cleanup_old_jobs()
    
    def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new job and return job ID"""
        job_id = str(uuid.uuid4())
        # Sanitize job_id to prevent path injection
        job_id_safe = job_id.replace('/', '_').replace('\\', '_').replace('..', '_')
        job_info = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress": 0,
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "execution_time": None,
            "error": None,
            "data": job_data  # Store the original request data
        }
        
        job_file = self.jobs_dir / f"{job_id_safe}.json"
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(job_info, f, indent=2)
        
        logger.info(f"Created job {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job information"""
        # Sanitize job_id to prevent path injection
        job_id_safe = job_id.replace('/', '_').replace('\\', '_').replace('..', '_')
        job_file = self.jobs_dir / f"{job_id_safe}.json"
        if not job_file.exists():
            return None
        
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON for job {job_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading job file {job_id}: {e}")
            return None
    
    def update_job(self, job_id: str, updates: Dict[str, Any]):
        """Update job information with thread-safe file locking"""
        # Sanitize job_id to prevent path injection
        job_id_safe = job_id.replace('/', '_').replace('\\', '_').replace('..', '_')
        job_file = self.jobs_dir / f"{job_id_safe}.json"
        if not job_file.exists():
            return
        
        # Use lock to prevent race conditions during read-modify-write
        with self.lock:
            try:
                # Read existing job info
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_info = json.load(f)
                
                # Merge updates
                job_info.update(updates)
                
                # Atomically write back (create temp file first, then rename)
                temp_file = job_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(job_info, f, indent=2)
                
                # Atomic rename (cross-platform)
                temp_file.replace(job_file)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON for job {job_id} during update: {e}")
            except Exception as e:
                logger.error(f"Error updating job file {job_id}: {e}")
    
    def start_job(self, job_id: str, script_path: str, work_dir: str, timeout: int = 86400):
        """Start executing a job in background thread"""
        # Validate timeout parameter
        if timeout <= 0:
            logger.error(f"Invalid timeout for job {job_id}: {timeout}. Using default 86400.")
            timeout = 86400
        
        def run_job():
            start_time = None
            process = None
            try:
                self.update_job(job_id, {
                    "status": JobStatus.RUNNING,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "progress": PROGRESS_START
                })
                
                start_time = time.time()
                
                # Start subprocess
                process = subprocess.Popen(
                    [sys.executable, "-u", script_path],
                    cwd=work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # Store process reference
                with self.lock:
                    self.active_processes[job_id] = process
                
                # Read output in real-time
                stdout_lines = []
                stderr_lines = []
                max_lines = STDOUT_MAX_LINES * 2  # Keep more in memory, but update with last N
                
                # Update progress periodically
                last_update = time.time()
                
                while True:
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    # Check timeout - enforce it properly
                    if elapsed > timeout:
                        logger.warning(f"Job {job_id} exceeded timeout of {timeout}s, killing process")
                        with self.lock:
                            if job_id in self.active_processes and process:
                                try:
                                    process.terminate()
                                    try:
                                        process.wait(timeout=5)
                                    except subprocess.TimeoutExpired:
                                        process.kill()
                                except Exception as e:
                                    logger.error(f"Error killing process for job {job_id}: {e}")
                                finally:
                                    self.active_processes.pop(job_id, None)
                        
                        self.update_job(job_id, {
                            "status": JobStatus.FAILED,
                            "completed_at": datetime.now(timezone.utc).isoformat(),
                            "error": f"Execution timed out after {timeout} seconds",
                            "exit_code": -1,
                            "execution_time": elapsed,
                            "progress": PROGRESS_COMPLETE,
                            "stdout": "".join(stdout_lines[-STDOUT_MAX_LINES:]),
                            "stderr": "".join(stderr_lines[-STDOUT_MAX_LINES:])
                        })
                        logger.warning(f"Job {job_id} timed out after {elapsed:.2f}s")
                        return
                    
                    # Check if process finished
                    return_code = process.poll()
                    if return_code is not None:
                        # Process finished - read any remaining output
                        # Don't use communicate() here - already reading line by line
                        # Just read any remaining buffered lines
                        try:
                            if process.stdout:
                                remaining = process.stdout.read()
                                if remaining:
                                    stdout_lines.extend(remaining.splitlines(keepends=True))
                            if process.stderr:
                                remaining = process.stderr.read()
                                if remaining:
                                    stderr_lines.extend(remaining.splitlines(keepends=True))
                        except ValueError:
                            # Pipe is closed, which is fine - process is done
                            pass
                        break
                    
                    # Read available output (non-blocking with timeout check)
                    try:
                        if process.stdout and process.returncode is None:
                            line = process.stdout.readline()
                            if line:
                                stdout_lines.append(line)
                                # Limit memory usage - keep last N lines
                                if len(stdout_lines) > max_lines:
                                    stdout_lines = stdout_lines[-max_lines:]
                                
                                # Update job with output every few lines
                                if len(stdout_lines) % 10 == 0:
                                    progress = min(PROGRESS_MAX, PROGRESS_START + (len(stdout_lines) // 10))
                                    self.update_job(job_id, {
                                        "stdout": "".join(stdout_lines[-STDOUT_MAX_LINES:]),
                                        "progress": progress
                                    })
                    except ValueError:
                        # Pipe closed, process might be finishing
                        pass
                    
                    try:
                        if process.stderr and process.returncode is None:
                            line = process.stderr.readline()
                            if line:
                                stderr_lines.append(line)
                                # Limit memory usage
                                if len(stderr_lines) > max_lines:
                                    stderr_lines = stderr_lines[-max_lines:]
                    except ValueError:
                        # Pipe closed, process might be finishing
                        pass
                    
                    # Periodic progress update based on elapsed time
                    if current_time - last_update >= PROGRESS_UPDATE_INTERVAL:
                        if timeout > 0:
                            progress = min(PROGRESS_MAX, PROGRESS_START + int((elapsed / timeout) * (PROGRESS_MAX - PROGRESS_START)))
                        else:
                            progress = PROGRESS_MAX
                        
                        self.update_job(job_id, {
                            "progress": progress,
                            "stdout": "".join(stdout_lines[-STDOUT_MAX_LINES:])
                        })
                        last_update = current_time
                    
                    time.sleep(0.1)  # Small delay to prevent CPU spinning
                
                # Process finished - get final output
                stdout = "".join(stdout_lines[-STDOUT_MAX_LINES:])
                stderr = "".join(stderr_lines[-STDOUT_MAX_LINES:])
                execution_time = time.time() - start_time
                
                # Remove process reference safely
                with self.lock:
                    self.active_processes.pop(job_id, None)
                
                # Update job with final results
                status = JobStatus.COMPLETED if return_code == 0 else JobStatus.FAILED
                self.update_job(job_id, {
                    "status": status,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": return_code,
                    "execution_time": execution_time,
                    "progress": PROGRESS_COMPLETE
                })
                
                logger.info(f"Job {job_id} completed with exit code {return_code}")
                
            except Exception as e:
                # Remove process reference safely
                with self.lock:
                    self.active_processes.pop(job_id, None)
                
                # Clean up process if still running
                if process and process.poll() is None:
                    try:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                    except Exception:
                        pass
                
                self.update_job(job_id, {
                    "status": JobStatus.FAILED,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                    "exit_code": -1,
                    "execution_time": time.time() - start_time if start_time else 0,
                    "progress": PROGRESS_COMPLETE
                })
                logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        
        # Start job in background thread
        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
        logger.info(f"Started execution thread for job {job_id}")
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        with self.lock:
            process = self.active_processes.pop(job_id, None)
            if process is None:
                return False
            
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)  # Wait for kill to complete
            except Exception as e:
                logger.error(f"Error cancelling process for job {job_id}: {e}")
            
            self.update_job(job_id, {
                "status": JobStatus.CANCELLED,
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Job {job_id} cancelled")
            return True
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old job files"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            for job_file in self.jobs_dir.glob("*.json"):
                # Skip temp files
                if job_file.suffix == '.tmp':
                    continue
                try:
                    if job_file.stat().st_mtime < cutoff_time:
                        job_file.unlink()
                        logger.info(f"Cleaned up old job file: {job_file}")
                except FileNotFoundError:
                    # File was already deleted, skip
                    pass
                except Exception as e:
                    logger.warning(f"Failed to clean up {job_file}: {e}")
        except Exception as e:
            logger.warning(f"Error during job cleanup: {e}")


# Global job manager instance
_job_manager: Optional[JobManager] = None

def get_job_manager() -> JobManager:
    """Get or create global job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager