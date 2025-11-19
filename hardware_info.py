#!/usr/bin/env python3
"""
Advanced Hardware Info with Real-time Monitoring
"""

import subprocess
import json
from datetime import datetime
import os
def get_real_time_metrics():
    """Get real-time system metrics"""
    metrics = {}
    
    # CPU usage from /proc/stat
    try:
        with open('/proc/stat', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('cpu '):
                    parts = line.split()
                    total = sum(int(x) for x in parts[1:])
                    idle = int(parts[4])
                    usage = ((total - idle) / total) * 100
                    metrics['cpu_usage_percent'] = round(usage, 2)
                    break
    except:
        pass
    
    # Memory usage in percentage
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    meminfo[key.strip()] = value.strip()
            
            total = int(meminfo['MemTotal'].split()[0])
            available = int(meminfo['MemAvailable'].split()[0])
            usage_percent = ((total - available) / total) * 100
            metrics['memory_usage_percent'] = round(usage_percent, 2)
    except:
        pass
    
    # Disk I/O
    try:
        with open('/proc/diskstats', 'r') as f:
            metrics['disk_activity'] = len(f.readlines())
    except:
        pass
    
    return metrics

def get_environment_info():
    """Get GitHub Actions environment info"""
    env_info = {
        'runner_os': subprocess.getoutput('uname -a'),
        'github_actions': os.environ.get('GITHUB_ACTIONS', 'false'),
        'workflow_name': os.environ.get('GITHUB_WORKFLOW', 'unknown'),
        'run_id': os.environ.get('GITHUB_RUN_ID', 'unknown'),
        'timestamp': datetime.now().isoformat()
    }
    return env_info

# اجرای کسری برای اطلاعات بیشتر
if __name__ == "__main__":
    real_time = get_real_time_metrics()
    env_info = get_environment_info()
    
    print("🚀 REAL-TIME METRICS:")
    print(f"📊 CPU Usage: {real_time.get('cpu_usage_percent', 'N/A')}%")
    print(f"💾 Memory Usage: {real_time.get('memory_usage_percent', 'N/A')}%")
    print(f"⏰ Timestamp: {env_info['timestamp']}")
