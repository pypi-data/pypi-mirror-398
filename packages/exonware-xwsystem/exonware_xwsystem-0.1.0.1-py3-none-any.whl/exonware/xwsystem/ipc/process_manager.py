"""
Process Management Utilities
============================

Production-grade process management for XSystem.

Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Company: eXonware.com
Generation Date: September 05, 2025
"""

import os
import sys
import time
import signal
import subprocess
import multiprocessing as mp
from typing import Optional, Callable, Any, Union
from dataclasses import dataclass
from threading import Lock, Event
import logging
import psutil
logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a managed process."""
    pid: int
    name: str
    command: list[str]
    started_at: float
    status: str  # 'running', 'stopped', 'failed', 'terminated'
    exit_code: Optional[int] = None
    memory_usage: Optional[float] = None
    cpu_percent: Optional[float] = None


class ProcessManager:
    """
    Production-grade process manager with monitoring and lifecycle management.
    
    Features:
    - Process spawning and monitoring
    - Graceful shutdown with fallback to force-kill
    - Resource usage tracking
    - Process health checks
    - Signal handling
    - Cross-platform compatibility
    """
    
    def __init__(self, max_processes: int = None, monitor_interval: float = 1.0):
        """
        Initialize process manager.
        
        Args:
            max_processes: Maximum number of processes to manage
            monitor_interval: Interval between health checks (seconds)
        """
        self.max_processes = max_processes or mp.cpu_count() * 2
        self.monitor_interval = monitor_interval
        self.processes: dict[str, subprocess.Popen] = {}
        self.process_info: dict[str, ProcessInfo] = {}
        self._lock = Lock()
        self._shutdown_event = Event()
        self._monitor_thread = None
        
        # Signal handlers for graceful shutdown
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def start_process(self, 
                     name: str, 
                     command: Union[str, list[str]], 
                     cwd: Optional[str] = None,
                     env: Optional[dict[str, str]] = None,
                     shell: bool = False) -> bool:
        """
        Start a new managed process.
        
        Args:
            name: Unique name for the process
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            shell: Whether to use shell
            
        Returns:
            True if process started successfully
        """
        with self._lock:
            if len(self.processes) >= self.max_processes:
                logger.error(f"Cannot start process '{name}': max processes ({self.max_processes}) reached")
                return False
                
            if name in self.processes:
                logger.error(f"Process '{name}' already exists")
                return False
            
            try:
                # Prepare command
                if isinstance(command, str):
                    cmd = command.split() if not shell else command
                else:
                    cmd = command
                
                # Start process
                process = subprocess.Popen(
                    cmd,
                    cwd=cwd,
                    env=env,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=None if sys.platform == 'win32' else os.setsid
                )
                
                # Store process info
                self.processes[name] = process
                self.process_info[name] = ProcessInfo(
                    pid=process.pid,
                    name=name,
                    command=cmd if isinstance(cmd, list) else [cmd],
                    started_at=time.time(),
                    status='running'
                )
                
                logger.info(f"Started process '{name}' with PID {process.pid}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start process '{name}': {e}")
                return False
    
    def stop_process(self, name: str, timeout: float = 10.0) -> bool:
        """
        Stop a managed process gracefully.
        
        Args:
            name: Name of the process to stop
            timeout: Timeout for graceful shutdown
            
        Returns:
            True if process stopped successfully
        """
        with self._lock:
            if name not in self.processes:
                logger.warning(f"Process '{name}' not found")
                return False
            
            process = self.processes[name]
            info = self.process_info[name]
            
            try:
                # Check if already terminated
                if process.poll() is not None:
                    info.status = 'stopped'
                    info.exit_code = process.returncode
                    return True
                
                # Try graceful shutdown first
                if sys.platform != 'win32':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=timeout)
                    info.status = 'stopped'
                    info.exit_code = process.returncode
                    logger.info(f"Process '{name}' stopped gracefully")
                    return True
                    
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    logger.warning(f"Process '{name}' did not stop gracefully, force killing")
                    if sys.platform != 'win32':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                    
                    process.wait()
                    info.status = 'terminated'
                    info.exit_code = process.returncode
                    return True
                    
            except Exception as e:
                logger.error(f"Failed to stop process '{name}': {e}")
                info.status = 'failed'
                return False
    
    def restart_process(self, name: str, timeout: float = 10.0) -> bool:
        """
        Restart a managed process.
        
        Args:
            name: Name of the process to restart
            timeout: Timeout for shutdown
            
        Returns:
            True if process restarted successfully
        """
        if name not in self.process_info:
            logger.error(f"Cannot restart unknown process '{name}'")
            return False
        
        info = self.process_info[name]
        command = info.command
        
        # Stop the process
        if not self.stop_process(name, timeout):
            logger.error(f"Failed to stop process '{name}' for restart")
            return False
        
        # Clean up
        self._cleanup_process(name)
        
        # Start again
        return self.start_process(name, command)
    
    def get_process_info(self, name: str) -> Optional[ProcessInfo]:
        """Get information about a managed process."""
        with self._lock:
            return self.process_info.get(name)
    
    def list_processes(self) -> list[ProcessInfo]:
        """List all managed processes."""
        with self._lock:
            return list(self.process_info.values())
    
    def is_running(self, name: str) -> bool:
        """Check if a process is running."""
        with self._lock:
            if name not in self.processes:
                return False
            
            process = self.processes[name]
            return process.poll() is None
    
    def get_output(self, name: str, timeout: float = 1.0) -> tuple[str, str]:
        """
        Get stdout and stderr from a process.
        
        Returns:
            Tuple of (stdout, stderr)
        """
        with self._lock:
            if name not in self.processes:
                return "", ""
            
            process = self.processes[name]
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore')
            except subprocess.TimeoutExpired:
                return "", ""
    
    def shutdown_all(self, timeout: float = 10.0) -> bool:
        """
        Shutdown all managed processes.
        
        Args:
            timeout: Timeout for each process shutdown
            
        Returns:
            True if all processes stopped successfully
        """
        self._shutdown_event.set()
        
        with self._lock:
            success = True
            process_names = list(self.processes.keys())
            
            for name in process_names:
                if not self.stop_process(name, timeout):
                    success = False
                else:
                    self._cleanup_process(name)
        
        return success
    
    def _cleanup_process(self, name: str):
        """Clean up process references."""
        if name in self.processes:
            del self.processes[name]
        # Keep process info for history
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down processes")
        self.shutdown_all()
        sys.exit(0)
    
    def _update_process_stats(self):
        """Update process statistics (memory, CPU usage)."""

        with self._lock:
                for name, process in self.processes.items():
                    if process.poll() is None:  # Still running
                        try:
                            ps_process = psutil.Process(process.pid)
                            info = self.process_info[name]
                            info.memory_usage = ps_process.memory_info().rss / 1024 / 1024  # MB
                            info.cpu_percent = ps_process.cpu_percent()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown_all()


    def get_process_status(self, process_id: str) -> str:
        """
        Get the status of a process.
        
        Args:
            process_id: Process ID
            
        Returns:
            Process status
        """
        process_info = self.get_process_info(process_id)
        if process_info:
            return process_info.status
        return "unknown"  # Default status when process is not tracked


def is_ipc_available() -> bool:
    """Check if IPC functionality is available."""
    # multiprocessing and subprocess are built-in Python modules
    import multiprocessing
    import subprocess
    return True
