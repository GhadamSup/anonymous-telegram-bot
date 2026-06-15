import psutil
import os
import platform
from datetime import datetime, timedelta

class SystemService:
    """Service for system resource monitoring"""
    
    @staticmethod
    def get_cpu_usage() -> dict:
        """Get CPU usage statistics"""
        return {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
    
    @staticmethod
    def get_memory_usage() -> dict:
        """Get memory usage statistics"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
            'total_gb': round(memory.total / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2)
        }
    
    @staticmethod
    def get_disk_usage() -> dict:
        """Get disk usage statistics"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent,
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2)
        }
    
    @staticmethod
    def get_network_usage() -> dict:
        """Get network statistics"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'sent_mb': round(net_io.bytes_sent / (1024**2), 2),
            'recv_mb': round(net_io.bytes_recv / (1024**2), 2)
        }
    
    @staticmethod
    def get_process_info() -> dict:
        """Get current process information"""
        process = psutil.Process(os.getpid())
        with process.oneshot():
            return {
                'pid': process.pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': round(process.memory_percent(), 2),
                'memory_used_mb': round(process.memory_info().rss / (1024**2), 2),
                'threads': process.num_threads(),
                'created': datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                'uptime': str(timedelta(seconds=int(datetime.now().timestamp() - process.create_time())))
            }
    
    @staticmethod
    def get_system_info() -> dict:
        """Get system information"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'python_version': platform.python_version(),
            'hostname': platform.node(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'uptime': str(timedelta(seconds=int(datetime.now().timestamp() - psutil.boot_time())))
        }
    
    @staticmethod
    def get_all_stats() -> dict:
        """Get all system statistics"""
        return {
            'system': SystemService.get_system_info(),
            'cpu': SystemService.get_cpu_usage(),
            'memory': SystemService.get_memory_usage(),
            'disk': SystemService.get_disk_usage(),
            'network': SystemService.get_network_usage(),
            'process': SystemService.get_process_info(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }