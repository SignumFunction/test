#!/usr/bin/env python3
"""
Comprehensive Linux Hardware Information Script for GitHub Actions
"""

import os
import re
import subprocess
import json
from datetime import datetime
from pathlib import Path

class LinuxHardwareInfo:
    def __init__(self):
        self.emoji = {
            "cpu": "🖥️", "ram": "💾", "disk": "💽", "network": "🌐", 
            "system": "🐧", "success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"
        }
        self.hardware_data = {}
    
    def run_command(self, cmd, timeout=10):
        """Execute shell command safely"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout, executable='/bin/bash')
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception as e:
            return None
    
    def read_file(self, filepath):
        """Read file content safely"""
        try:
            with open(filepath, 'r') as f:
                return f.read().strip()
        except Exception as e:
            return None
    
    def get_system_info(self):
        """Get system information"""
        system_info = {}
        try:
            system_info['kernel'] = self.read_file('/proc/version')
            system_info['hostname'] = self.run_command('hostname')
            system_info['os_release'] = self.read_file('/etc/os-release')
            
            # Uptime
            uptime_str = self.read_file('/proc/uptime')
            if uptime_str:
                uptime_seconds = float(uptime_str.split()[0])
                system_info['uptime_seconds'] = uptime_seconds
                system_info['uptime_days'] = round(uptime_seconds / 86400, 2)
            
            # GitHub Environment
            system_info['github_actions'] = os.environ.get('GITHUB_ACTIONS', 'false')
            system_info['workflow'] = os.environ.get('GITHUB_WORKFLOW', 'unknown')
            system_info['repository'] = os.environ.get('GITHUB_REPOSITORY', 'unknown')
            system_info['runner_os'] = self.run_command('uname -a')
            system_info['timestamp'] = datetime.now().isoformat()
            
        except Exception as e:
            system_info['error'] = str(e)
        
        return system_info
    
    def get_cpu_info(self):
        """Get comprehensive CPU information"""
        cpu_info = {}
        try:
            # From /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
            
            processors = content.split('\n\n')
            cpu_info['logical_cpus'] = len([p for p in processors if p.strip()])
            
            # Parse first CPU
            first_cpu = processors[0]
            fields = {}
            for line in first_cpu.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    fields[key.strip()] = value.strip()
            
            cpu_info.update({
                'model_name': fields.get('model name', 'Unknown'),
                'vendor_id': fields.get('vendor_id', 'Unknown'),
                'cpu_family': fields.get('cpu family', 'Unknown'),
                'model': fields.get('model', 'Unknown'),
                'stepping': fields.get('stepping', 'Unknown'),
                'cpu_cores': fields.get('cpu cores', 'Unknown'),
                'siblings': fields.get('siblings', 'Unknown'),
                'cpu_mhz': fields.get('cpu MHz', 'Unknown'),
                'cache_size': fields.get('cache size', 'Unknown'),
                'flags': fields.get('flags', '').split()[:10]  # First 10 flags
            })
            
            # From lscpu
            lscpu_output = self.run_command('lscpu')
            if lscpu_output:
                lscpu_info = {}
                for line in lscpu_output.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        lscpu_info[key.strip()] = value.strip()
                cpu_info['lscpu'] = lscpu_info
            
            # CPU usage from /proc/stat
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('cpu '):
                        parts = line.split()
                        total = sum(int(x) for x in parts[1:])
                        idle = int(parts[4])
                        usage = ((total - idle) / total) * 100
                        cpu_info['usage_percent'] = round(usage, 2)
                        break
            
            # Load average
            loadavg = self.read_file('/proc/loadavg')
            if loadavg:
                load_parts = loadavg.split()
                cpu_info['load_1min'] = load_parts[0]
                cpu_info['load_5min'] = load_parts[1]
                cpu_info['load_15min'] = load_parts[2]
            
        except Exception as e:
            cpu_info['error'] = str(e)
        
        return cpu_info
    
    def get_memory_info(self):
        """Get comprehensive memory information"""
        memory_info = {}
        try:
            # From /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        memory_info[key.strip()] = value.strip()
            
            # Calculate usage percentage
            if 'MemTotal' in memory_info and 'MemAvailable' in memory_info:
                total_kb = int(memory_info['MemTotal'].split()[0])
                available_kb = int(memory_info['MemAvailable'].split()[0])
                used_kb = total_kb - available_kb
                usage_percent = (used_kb / total_kb) * 100
                
                memory_info['usage_percent'] = round(usage_percent, 2)
                memory_info['total_gb'] = round(total_kb / 1024 / 1024, 2)
                memory_info['used_gb'] = round(used_kb / 1024 / 1024, 2)
                memory_info['available_gb'] = round(available_kb / 1024 / 1024, 2)
            
            # From free command
            free_output = self.run_command('free -h')
            if free_output:
                memory_info['free_command'] = free_output
            
            # From free in bytes for precise calculation
            free_bytes = self.run_command('free -b')
            if free_bytes:
                lines = free_bytes.split('\n')
                if len(lines) >= 2:
                    memory_line = lines[1].split()
                    if len(memory_line) >= 7:
                        memory_info['detailed'] = {
                            'total_bytes': memory_line[1],
                            'used_bytes': memory_line[2],
                            'free_bytes': memory_line[3],
                            'shared_bytes': memory_line[4],
                            'buff_cache_bytes': memory_line[5],
                            'available_bytes': memory_line[6]
                        }
            
        except Exception as e:
            memory_info['error'] = str(e)
        
        return memory_info
    
    def get_disk_info(self):
        """Get disk information"""
        disk_info = {}
        try:
            # Disk space
            df_output = self.run_command('df -h /')
            if df_output:
                disk_info['root_filesystem'] = df_output
            
            # Disk info
            lsblk_output = self.run_command('lsblk')
            if lsblk_output:
                disk_info['block_devices'] = lsblk_output
            
            # Mount info
            mount_output = self.run_command('mount')
            if mount_output:
                disk_info['mounts'] = mount_output.split('\n')[:10]  # First 10 mounts
            
        except Exception as e:
            disk_info['error'] = str(e)
        
        return disk_info
    
    def get_network_info(self):
        """Get network information"""
        network_info = {}
        try:
            # IP addresses
            ip_addr = self.run_command('ip addr show')
            if ip_addr:
                network_info['ip_addresses'] = ip_addr
            
            # Network interfaces
            interfaces = self.run_command('cat /proc/net/dev')
            if interfaces:
                network_info['network_interfaces'] = interfaces
            
            # Routing
            route = self.run_command('ip route')
            if route:
                network_info['routing_table'] = route
            
        except Exception as e:
            network_info['error'] = str(e)
        
        return network_info
    
    def get_additional_info(self):
        """Get additional hardware information"""
        additional = {}
        try:
            # CPU vulnerabilities
            vuln_dir = Path('/sys/devices/system/cpu/vulnerabilities')
            if vuln_dir.exists():
                vulnerabilities = {}
                for vuln_file in vuln_dir.iterdir():
                    if vuln_file.is_file():
                        content = self.read_file(vuln_file)
                        if content:
                            vulnerabilities[vuln_file.name] = content
                additional['vulnerabilities'] = vulnerabilities
            
            # Hardware info from dmidecode (if available)
            dmidecode = self.run_command('sudo dmidecode -t system 2>/dev/null || echo "dmidecode not available"')
            if dmidecode:
                additional['system_dmi'] = dmidecode
            
            # PCI devices
            lspci = self.run_command('lspci')
            if lspci:
                additional['pci_devices'] = lspci.split('\n')[:20]  # First 20 devices
            
        except Exception as e:
            additional['error'] = str(e)
        
        return additional
    
    def collect_all_info(self):
        """Collect all hardware information"""
        print(f"{self.emoji['system']} Starting comprehensive hardware detection...")
        
        self.hardware_data = {
            'system': self.get_system_info(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'additional': self.get_additional_info()
        }
        
        return self.hardware_data
    
    def generate_text_report(self):
        """Generate human-readable text report"""
        report = []
        report.append("=" * 80)
        report.append("🐧 COMPREHENSIVE LINUX HARDWARE REPORT - GitHub Actions")
        report.append("=" * 80)
        
        # System Information
        system = self.hardware_data.get('system', {})
        report.append(f"\n🌍 SYSTEM INFORMATION")
        report.append("-" * 50)
        report.append(f"Hostname: {system.get('hostname', 'Unknown')}")
        report.append(f"Kernel: {system.get('kernel', 'Unknown').split(' ')[0] if system.get('kernel') else 'Unknown'}")
        report.append(f"Uptime: {system.get('uptime_days', 'Unknown')} days")
        report.append(f"GitHub Workflow: {system.get('workflow', 'Unknown')}")
        report.append(f"Timestamp: {system.get('timestamp', 'Unknown')}")
        
        # CPU Information
        cpu = self.hardware_data.get('cpu', {})
        report.append(f"\n🖥️ CPU INFORMATION")
        report.append("-" * 50)
        report.append(f"Processor: {cpu.get('model_name', 'Unknown')}")
        report.append(f"Logical CPUs: {cpu.get('logical_cpus', 'Unknown')}")
        report.append(f"CPU Cores: {cpu.get('cpu_cores', 'Unknown')}")
        report.append(f"Frequency: {cpu.get('cpu_mhz', 'Unknown')} MHz")
        report.append(f"CPU Usage: {cpu.get('usage_percent', 'Unknown')}%")
        report.append(f"Load Average (1min): {cpu.get('load_1min', 'Unknown')}")
        
        # Memory Information
        memory = self.hardware_data.get('memory', {})
        report.append(f"\n💾 MEMORY INFORMATION")
        report.append("-" * 50)
        report.append(f"Total Memory: {memory.get('MemTotal', 'Unknown')}")
        report.append(f"Available Memory: {memory.get('MemAvailable', 'Unknown')}")
        report.append(f"Memory Usage: {memory.get('usage_percent', 'Unknown')}%")
        if 'total_gb' in memory:
            report.append(f"Total: {memory['total_gb']} GB | Used: {memory.get('used_gb', 'Unknown')} GB | Available: {memory.get('available_gb', 'Unknown')} GB")
        
        # Additional Information
        additional = self.hardware_data.get('additional', {})
        if 'vulnerabilities' in additional:
            report.append(f"\n🔒 SECURITY VULNERABILITIES")
            report.append("-" * 50)
            for vuln, status in additional['vulnerabilities'].items():
                report.append(f"{vuln}: {status}")
        
        report.append("\n" + "=" * 80)
        report.append("✅ Hardware detection completed successfully!")
        report.append("=" * 80)
        
        return '\n'.join(report)
    
    def save_reports(self):
        """Save reports to files"""
        # Save JSON report
        with open('hardware_detailed.json', 'w') as f:
            json.dump(self.hardware_data, f, indent=2, ensure_ascii=False)
        
        # Save text report
        text_report = self.generate_text_report()
        with open('hardware_report.txt', 'w') as f:
            f.write(text_report)
        
        print(f"\n{self.emoji['success']} Reports saved:")
        print(f"   📄 hardware_detailed.json (Structured data)")
        print(f"   📄 hardware_report.txt (Human readable report)")

def main():
    """Main execution function"""
    hardware = LinuxHardwareInfo()
    
    # Collect all information
    print("🚀 Starting comprehensive hardware detection...")
    all_info = hardware.collect_all_info()
    
    # Generate and display report
    print("\n" + "=" * 80)
    text_report = hardware.generate_text_report()
    print(text_report)
    
    # Save reports to files
    hardware.save_reports()
    
    # GitHub Actions output
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f'report_generated=true', file=fh)
            print(f'cpu_model={all_info["cpu"].get("model_name", "unknown")}', file=fh)
            print(f'memory_total={all_info["memory"].get("MemTotal", "unknown")}', file=fh)
            print(f'cpu_usage={all_info["cpu"].get("usage_percent", "unknown")}', file=fh)
            print(f'memory_usage={all_info["memory"].get("usage_percent", "unknown")}', file=fh)
    
    print(f"\n✅ Hardware information collection completed successfully!")

if __name__ == "__main__":
    main()
