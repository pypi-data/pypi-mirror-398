"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

System-wide monitoring and hardware introspection utilities.
"""

import os
import platform
import time
from dataclasses import dataclass
from typing import Optional, Any, Union
from pathlib import Path

# Import psutil - lazy installation system will handle it if missing
import psutil

from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.monitoring.system_monitor")


@dataclass
class ProcessInfo:
    """Process information structure."""
    
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # Resident Set Size in bytes
    memory_vms: int  # Virtual Memory Size in bytes
    create_time: float
    num_threads: int
    username: Optional[str] = None
    cmdline: Optional[list[str]] = None
    cwd: Optional[str] = None
    exe: Optional[str] = None


@dataclass
class SystemInfo:
    """System information structure."""
    
    # Platform info
    system: str
    node: str
    release: str
    version: str
    machine: str
    processor: str
    
    # Boot time
    boot_time: float
    
    # CPU info
    cpu_count_logical: int
    cpu_count_physical: int
    cpu_freq_current: Optional[float]
    cpu_freq_min: Optional[float]
    cpu_freq_max: Optional[float]
    
    # Memory info
    memory_total: int
    memory_available: int
    memory_used: int
    memory_percent: float
    
    # Swap info
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float


@dataclass
class DiskInfo:
    """Disk information structure."""
    
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class NetworkInfo:
    """Network interface information structure."""
    
    interface: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errin: int
    errout: int
    dropin: int
    dropout: int
    is_up: bool


@dataclass
class NetworkConnection:
    """Network connection information."""
    
    fd: int
    family: str
    type: str
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    status: str
    pid: Optional[int] = None


class SystemMonitor:
    """
    System-wide monitoring and hardware introspection.
    
    Features:
    - Process introspection and management
    - System resource monitoring
    - Hardware information
    - Network monitoring
    - Cross-platform compatibility
    """
    
    def __init__(self):
        """Initialize system monitor."""
        # Lazy installation system will handle psutil if missing
        
        self._boot_time = None
        logger.debug("System monitor initialized")
    
    def is_available(self) -> bool:
        """Check if full system monitoring is available."""
        # Lazy installation system ensures psutil is always available
        return True
    
    # =============================================================================
    # PROCESS MONITORING
    # =============================================================================
    
    def list_processes(self, attrs: Optional[list[str]] = None) -> list[ProcessInfo]:
        """
        List all running processes.
        
        Args:
            attrs: Optional list of attributes to retrieve
            
        Returns:
            List of ProcessInfo objects
        """
        # Lazy installation system will handle psutil if missing
        
        processes = []
        
        if attrs is None:
            attrs = ['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 
                    'memory_info', 'create_time', 'num_threads', 'username']
        
        for proc in psutil.process_iter(attrs=attrs, ad_value=None):
            try:
                pinfo = proc.info
                
                memory_info = pinfo.get('memory_info')
                process_info = ProcessInfo(
                    pid=pinfo['pid'],
                    name=pinfo.get('name', 'Unknown'),
                    status=pinfo.get('status', 'Unknown'),
                    cpu_percent=pinfo.get('cpu_percent', 0.0),
                    memory_percent=pinfo.get('memory_percent', 0.0),
                    memory_rss=memory_info.rss if memory_info else 0,
                    memory_vms=memory_info.vms if memory_info else 0,
                    create_time=pinfo.get('create_time', 0.0),
                    num_threads=pinfo.get('num_threads', 0),
                    username=pinfo.get('username'),
                )
                
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process disappeared or access denied
                continue
        
        return processes
    
    def get_process(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get detailed information about a specific process.
        
        Args:
            pid: Process ID
            
        Returns:
            ProcessInfo object or None if process not found
        """
        # Lazy installation system will handle psutil if missing
        
        try:
            proc = psutil.Process(pid)
            
            # Get memory info
            memory_info = proc.memory_info()
            
            # Get additional details
            try:
                cmdline = proc.cmdline()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                cmdline = None
            
            try:
                cwd = proc.cwd()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                cwd = None
            
            try:
                exe = proc.exe()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                exe = None
            
            try:
                username = proc.username()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                username = None
            
            return ProcessInfo(
                pid=proc.pid,
                name=proc.name(),
                status=proc.status(),
                cpu_percent=proc.cpu_percent(),
                memory_percent=proc.memory_percent(),
                memory_rss=memory_info.rss,
                memory_vms=memory_info.vms,
                create_time=proc.create_time(),
                num_threads=proc.num_threads(),
                username=username,
                cmdline=cmdline,
                cwd=cwd,
                exe=exe,
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
    
    def find_processes_by_name(self, name: str) -> list[ProcessInfo]:
        """
        Find processes by name.
        
        Args:
            name: Process name to search for
            
        Returns:
            List of matching ProcessInfo objects
        """
        all_processes = self.list_processes()
        return [proc for proc in all_processes if name.lower() in proc.name.lower()]
    
    def kill_process(self, pid: int, timeout: float = 3.0) -> bool:
        """
        Kill a process gracefully, then forcefully if needed.
        
        Args:
            pid: Process ID to kill
            timeout: Timeout for graceful termination
            
        Returns:
            True if process was killed
        """
        try:
            proc = psutil.Process(pid)
            
            # Try graceful termination first
            proc.terminate()
            
            try:
                proc.wait(timeout=timeout)
                logger.debug(f"Process {pid} terminated gracefully")
                return True
            except psutil.TimeoutExpired:
                # Force kill
                proc.kill()
                proc.wait()
                logger.debug(f"Process {pid} killed forcefully")
                return True
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    # =============================================================================
    # SYSTEM INFORMATION
    # =============================================================================
    
    def get_system_info(self) -> SystemInfo:
        """
        Get comprehensive system information.
        
        Returns:
            SystemInfo object with system details
        """
        # Platform information
        system_info = {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
        }
        
        # Lazy installation ensures psutil is available
        # Boot time
        boot_time = psutil.boot_time()
        
        # CPU information
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_current = cpu_freq.current if cpu_freq else None
            cpu_freq_min = cpu_freq.min if cpu_freq else None
            cpu_freq_max = cpu_freq.max if cpu_freq else None
        except (AttributeError, OSError):
            cpu_freq_current = cpu_freq_min = cpu_freq_max = None
        
        # Memory information
        memory = psutil.virtual_memory()
        
        # Swap information
        swap = psutil.swap_memory()
        
        system_info.update({
            'boot_time': boot_time,
            'cpu_count_logical': cpu_count_logical,
            'cpu_count_physical': cpu_count_physical or cpu_count_logical,
            'cpu_freq_current': cpu_freq_current,
            'cpu_freq_min': cpu_freq_min,
            'cpu_freq_max': cpu_freq_max,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_free': swap.free,
            'swap_percent': swap.percent,
        })
        
        return SystemInfo(**system_info)
    
    def get_cpu_usage(self, interval: float = 1.0, per_cpu: bool = False) -> Union[float, list[float]]:
        """
        Get CPU usage percentage.
        
        Args:
            interval: Measurement interval in seconds
            per_cpu: Return per-CPU usage if True
            
        Returns:
            CPU usage percentage (or list if per_cpu=True)
        """
        # Lazy installation system will handle psutil if missing
        
        return psutil.cpu_percent(interval=interval, percpu=per_cpu)
    
    def get_memory_usage(self) -> dict[str, Any]:
        """
        Get memory usage information.
        
        Returns:
            Dictionary with memory statistics
        """
        # Lazy installation system will handle psutil if missing
        
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
            'free': memory.free,
            'active': getattr(memory, 'active', 0),
            'inactive': getattr(memory, 'inactive', 0),
            'buffers': getattr(memory, 'buffers', 0),
            'cached': getattr(memory, 'cached', 0),
        }
    
    def get_disk_usage(self) -> list[DiskInfo]:
        """
        Get disk usage information for all mounted disks.
        
        Returns:
            List of DiskInfo objects
        """
        # Lazy installation system will handle psutil if missing
        
        disks = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                disk_info = DiskInfo(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    fstype=partition.fstype,
                    total=usage.total,
                    used=usage.used,
                    free=usage.free,
                    percent=(usage.used / usage.total) * 100 if usage.total > 0 else 0.0
                )
                
                disks.append(disk_info)
                
            except (PermissionError, OSError):
                # Skip inaccessible partitions
                continue
        
        return disks
    
    def get_network_interfaces(self) -> list[NetworkInfo]:
        """
        Get network interface statistics.
        
        Returns:
            List of NetworkInfo objects
        """
        # Lazy installation system will handle psutil if missing
        
        interfaces = []
        
        # Get interface statistics
        net_io = psutil.net_io_counters(pernic=True)
        
        # Get interface addresses to check if interface is up
        net_addrs = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()
        
        for interface, stats in net_io.items():
            # Check if interface is up
            is_up = False
            if interface in net_stats:
                is_up = net_stats[interface].isup
            
            network_info = NetworkInfo(
                interface=interface,
                bytes_sent=stats.bytes_sent,
                bytes_recv=stats.bytes_recv,
                packets_sent=stats.packets_sent,
                packets_recv=stats.packets_recv,
                errin=stats.errin,
                errout=stats.errout,
                dropin=stats.dropin,
                dropout=stats.dropout,
                is_up=is_up,
            )
            
            interfaces.append(network_info)
        
        return interfaces
    
    def get_network_connections(self, kind: str = 'inet') -> list[NetworkConnection]:
        """
        Get network connections.
        
        Args:
            kind: Connection kind ('inet', 'inet4', 'inet6', 'tcp', 'udp', 'unix', 'all')
            
        Returns:
            List of NetworkConnection objects
        """
        # Lazy installation system will handle psutil if missing
        
        connections = []
        
        try:
            for conn in psutil.net_connections(kind=kind):
                # Handle address tuples
                local_addr = conn.laddr
                remote_addr = conn.raddr
                
                local_address = local_addr.ip if local_addr else ''
                local_port = local_addr.port if local_addr else 0
                
                remote_address = remote_addr.ip if remote_addr else ''
                remote_port = remote_addr.port if remote_addr else 0
                
                connection = NetworkConnection(
                    fd=conn.fd,
                    family=conn.family.name,
                    type=conn.type.name,
                    local_address=local_address,
                    local_port=local_port,
                    remote_address=remote_address,
                    remote_port=remote_port,
                    status=conn.status,
                    pid=conn.pid,
                )
                
                connections.append(connection)
                
        except (psutil.AccessDenied, OSError):
            # May require elevated privileges
            logger.warning("Access denied when retrieving network connections")
        
        return connections
    
    # =============================================================================
    # HARDWARE INFORMATION
    # =============================================================================
    
    def get_hardware_info(self) -> dict[str, Any]:
        """
        Get detailed hardware information.
        
        Returns:
            Dictionary with hardware details
        """
        hardware_info = {}
        
        # Basic platform info
        hardware_info.update({
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
        })
        
        # Lazy installation ensures psutil is available
        # CPU information
        hardware_info['cpu'] = {
            'logical_cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
        }
        
        # Try to get CPU frequency
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                hardware_info['cpu'].update({
                    'current_freq_mhz': cpu_freq.current,
                    'min_freq_mhz': cpu_freq.min,
                    'max_freq_mhz': cpu_freq.max,
                })
        except (AttributeError, OSError):
            pass
        
        # Memory information
        memory = psutil.virtual_memory()
        hardware_info['memory'] = {
            'total_bytes': memory.total,
            'total_gb': round(memory.total / (1024**3), 2),
        }
        
        # Disk information
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_bytes': usage.total,
                    'total_gb': round(usage.total / (1024**3), 2),
                })
            except (PermissionError, OSError):
                continue
        
        hardware_info['disks'] = disks
        
        # Network interfaces
        interfaces = []
        net_addrs = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()
        
        for interface, addrs in net_addrs.items():
            interface_info = {
                'name': interface,
                'addresses': [],
            }
            
            for addr in addrs:
                interface_info['addresses'].append({
                    'family': addr.family.name,
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast,
                })
            
            if interface in net_stats:
                stats = net_stats[interface]
                interface_info.update({
                    'is_up': stats.isup,
                    'duplex': stats.duplex.name if stats.duplex else 'unknown',
                    'speed_mbps': stats.speed,
                    'mtu': stats.mtu,
                })
            
            interfaces.append(interface_info)
        
        hardware_info['network_interfaces'] = interfaces
        
        return hardware_info
    
    def get_boot_time(self) -> float:
        """
        Get system boot time as timestamp.
        
        Returns:
            Boot time timestamp
        """
        # Lazy installation ensures psutil is available
        return psutil.boot_time()
    
    def get_uptime(self) -> float:
        """
        Get system uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        boot_time = self.get_boot_time()
        if boot_time > 0:
            return time.time() - boot_time
        else:
            return 0.0
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_current_user(self) -> str:
        """Get current username."""
        # Lazy installation ensures psutil is available
        try:
            return psutil.Process().username()
        except (psutil.AccessDenied, AttributeError):
            # Fallback to environment variables
            return os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
    
    def get_environment_variables(self) -> dict[str, str]:
        """Get all environment variables."""
        return dict(os.environ)
    
    def get_python_info(self) -> dict[str, Any]:
        """Get Python runtime information."""
        import sys
        
        return {
            'version': sys.version,
            'version_info': sys.version_info,
            'executable': sys.executable,
            'platform': sys.platform,
            'prefix': sys.prefix,
            'path': sys.path,
        }


# Global system monitor instance
_system_monitor = SystemMonitor()

# Convenience functions
def list_processes() -> list[ProcessInfo]:
    """List all running processes."""
    return _system_monitor.list_processes()

def get_process(pid: int) -> Optional[ProcessInfo]:
    """Get process information by PID."""
    return _system_monitor.get_process(pid)

def get_system_info() -> SystemInfo:
    """Get system information."""
    return _system_monitor.get_system_info()

def get_cpu_usage(interval: float = 1.0) -> float:
    """Get CPU usage percentage."""
    return _system_monitor.get_cpu_usage(interval)

def get_memory_usage() -> dict[str, Any]:
    """Get memory usage information."""
    return _system_monitor.get_memory_usage()

def get_hardware_info() -> dict[str, Any]:
    """Get hardware information."""
    return _system_monitor.get_hardware_info()

def is_monitoring_available() -> bool:
    """Check if full system monitoring is available."""
    # Lazy installation system ensures psutil is always available
    return True
