#!/usr/bin/env python3
"""
Comprehensive Linux Hardware Information Script
Gathers all possible CPU and RAM details using multiple methods
"""

import os
import re
import subprocess
import json
from pathlib import Path
from collections import OrderedDict

class LinuxHardwareDetective:
    def __init__(self):
        self.hardware_info = OrderedDict()
        self.emoji = {
            "cpu": "🖥️",
            "ram": "💾",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "disk": "💽",
            "network": "🌐",
            "system": "🐧"
        }
    
    def run_command(self, cmd, timeout=10):
        """Execute shell command safely"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout, executable='/bin/bash')
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def read_file(self, filepath):
        """Read file content safely"""
        try:
            with open(filepath, 'r') as f:
                return f.read().strip()
        except:
            return None
    
    def get_cpu_info_proc(self):
        """Extract CPU info from /proc/cpuinfo"""
        cpu_info = {}
        try:
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
            
            # Parse individual processors
            processors = content.split('\n\n')
            cpu_info['processors'] = len([p for p in processors if p.strip()])
            
            # Extract common fields from first processor
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
                'microcode': fields.get('microcode', 'Unknown'),
                'cpu_mhz': fields.get('cpu MHz', 'Unknown'),
                'cache_size': fields.get('cache size', 'Unknown'),
                'physical_cores': fields.get('cpu cores', 'Unknown'),
                'siblings': fields.get('siblings', 'Unknown'),
                'flags': fields.get('flags', '').split()
            })
            
        except Exception as e:
            cpu_info['error'] = str(e)
        
        return cpu_info
    
    def get_cpu_info_lscpu(self):
        """Get detailed CPU info using lscpu"""
        lscpu_info = {}
        try:
            output = self.run_command('lscpu')
            if output:
                for line in output.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        lscpu_info[key.strip()] = value.strip()
        except Exception as e:
            lscpu_info['error'] = str(e)
        
        return lscpu_info
    
    def get_cpu_info_sysfs(self):
        """Get CPU info from sysfs"""
        sysfs_info = {}
        try:
            # CPU topology
            cpu_dirs = list(Path('/sys/devices/system/cpu').glob('cpu[0-9]*'))
            sysfs_info['online_cpus'] = len([c for c in cpu_dirs if self.read_file(c / 'online') != '0'])
            sysfs_info['total_cpus'] = len(cpu_dirs)
            
            # CPU frequencies
            freq_files = list(Path('/sys/devices/system/cpu/cpu0/cpufreq').glob('*'))
            if freq_files:
                freq_info = {}
                for freq_file in freq_files:
                    if freq_file.is_file():
                        content = self.read_file(freq_file)
                        if content:
                            freq_info[freq_file.name] = content
                sysfs_info['frequency_info'] = freq_info
            
            # CPU topology details
            topology = {}
            for cpu_dir in cpu_dirs[:1]:  # Just check first CPU
                if (cpu_dir / 'topology').exists():
                    for topo_file in (cpu_dir / 'topology').iterdir():
                        if topo_file.is_file():
                            content = self.read_file(topo_file)
                            if content:
                                topology[topo_file.name] = content
                break
            sysfs_info['topology'] = topology
            
        except Exception as e:
            sysfs_info['error'] = str(e)
        
        return sysfs_info
    
    def get_cpu_info_proc_stat(self):
        """Get CPU utilization from /proc/stat"""
        cpu_stats = {}
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('cpu '):
                        parts = line.split()
                        cpu_stats = {
                            'user': parts[1],
                            'nice': parts[2],
                            'system': parts[3],
                            'idle': parts[4],
                            'iowait': parts[5],
                            'irq': parts[6],
                            'softirq': parts[7],
                            'steal': parts[8] if len(parts) > 8 else '0',
                            'guest': parts[9] if len(parts) > 9 else '0'
                        }
                        break
        except Exception as e:
            cpu_stats['error'] = str(e)
        
        return cpu_stats
    
    def get_ram_info_proc(self):
        """Get RAM info from /proc/meminfo"""
        mem_info = {}
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        mem_info[key.strip()] = value.strip()
        except Exception as e:
            mem_info['error'] = str(e)
        
        return mem_info
    
    def get_ram_info_free(self):
        """Get RAM info using free command"""
        free_info = {}
        try:
            # Human readable
            output = self.run_command('free -h')
            if output:
                free_info['human_readable'] = output
            
            # Detailed in bytes
            output_bytes = self.run_command('free -b')
            if output_bytes:
                lines = output_bytes.split('\n')
                if len(lines) >= 2:
                    headers = lines[0].split()
                    memory_line = lines[1].split()
                    if len(memory_line) >= 6:
                        free_info['detailed'] = {
                            'total_bytes': memory_line[1],
                            'used_bytes': memory_line[2],
                            'free_bytes': memory_line[3],
                            'shared_bytes': memory_line[4],
                            'buff_cache_bytes': memory_line[5],
                            'available_bytes': memory_line[6]
                        }
        except Exception as e:
            free_info['error'] = str(e)
        
        return free_info
    
    def get_ram_info_dmidecode(self):
        """Get detailed RAM info using dmidecode"""
        ram_details = {}
        try:
            # Get memory device info
            output = self.run_command('sudo dmidecode -t memory 2>/dev/null || dmidecode -t memory 2>/dev/null')
            if output:
                ram_details['raw_dmidecode'] = output
                
                # Parse memory devices
                devices = output.split('Memory Device')
                ram_details['memory_modules'] = len(devices) - 1
                
                # Parse first memory device for details
                if len(devices) > 1:
                    first_device = devices[1]
                    module_info = {}
                    for line in first_device.split('\n'):
                        line = line.strip()
                        if ':' in line:
                            key, value = line.split(':', 1)
                            module_info[key.strip()] = value.strip()
                    ram_details['sample_module'] = module_info
                    
        except Exception as e:
            ram_details['error'] = str(e)
        
        return ram_details
    
    def get_ram_info_sysfs(self):
        """Get RAM info from sysfs"""
        sysfs_ram = {}
        try:
            # Memory block information
            memory_blocks = list(Path('/sys/devices/system/memory').glob('memory*'))
            sysfs_ram['memory_blocks'] = len(memory_blocks)
            
            # Check if blocks are online
            online_blocks = 0
            for block in memory_blocks:
                state = self.read_file(block / 'state')
                if state == 'online':
                    online_blocks += 1
            sysfs_ram['online_blocks'] = online_blocks
            
        except Exception as e:
            sysfs_ram['error'] = str(e)
        
        return sysfs_ram
    
    def get_ram_info_vmstat(self):
        """Get virtual memory statistics"""
        vmstat = {}
        try:
            with open('/proc/vmstat', 'r') as f:
                for line in f:
                    if line.strip():
                        key, value = line.split()
                        vmstat[key] = value
        except Exception as e:
            vmstat['error'] = str(e)
        
        return vmstat
    
    def get_system_info(self):
        """Get general system information"""
        system_info = {}
        try:
            # Kernel info
            system_info['kernel'] = self.read_file('/proc/version')
            system_info['hostname'] = self.read_file('/proc/sys/kernel/hostname')
            system_info['os_release'] = self.read_file('/etc/os-release')
            system_info['uptime'] = self.read_file('/proc/uptime')
            
            # Hardware info
            model = self.read_file('/proc/device-tree/model')
            if model:
                system_info['device_model'] = model
            
        except Exception as e:
            system_info['error'] = str(e)
        
        return system_info
    
    def get_additional_info(self):
        """Get additional hardware-related information"""
        additional = {}
        
        # CPU vulnerabilities
        try:
            vuln_dir = Path('/sys/devices/system/cpu/vulnerabilities')
            if vuln_dir.exists():
                vulnerabilities = {}
                for vuln_file in vuln_dir.iterdir():
                    if vuln_file.is_file():
                        content = self.read_file(vuln_file)
                        if content:
                            vulnerabilities[vuln_file.name] = content
                additional['vulnerabilities'] = vulnerabilities
        except:
            pass
        
        # CPU scaling driver
        try:
            scaling_driver = self.read_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver')
            if scaling_driver:
                additional['scaling_driver'] = scaling_driver
        except:
            pass
        
        return additional
    
    def collect_all_info(self):
        """Collect all hardware information"""
        print(f"{self.emoji['system']} Starting Comprehensive Linux Hardware Detection...")
        print("=" * 80)
        
        # System Information
        print(f"\n{self.emoji['system']} SYSTEM INFORMATION")
        print("-" * 50)
        self.hardware_info['system'] = self.get_system_info()
        
        # CPU Information from multiple sources
        print(f"\n{self.emoji['cpu']} CPU INFORMATION")
        print("-" * 50)
        
        print(f"{self.emoji['info']} Gathering CPU info from /proc/cpuinfo...")
        self.hardware_info['cpu_proc'] = self.get_cpu_info_proc()
        
        print(f"{self.emoji['info']} Gathering CPU info from lscpu...")
        self.hardware_info['cpu_lscpu'] = self.get_cpu_info_lscpu()
        
        print(f"{self.emoji['info']} Gathering CPU info from sysfs...")
        self.hardware_info['cpu_sysfs'] = self.get_cpu_info_sysfs()
        
        print(f"{self.emoji['info']} Gathering CPU stats from /proc/stat...")
        self.hardware_info['cpu_stat'] = self.get_cpu_info_proc_stat()
        
        # RAM Information from multiple sources
        print(f"\n{self.emoji['ram']} RAM INFORMATION")
        print("-" * 50)
        
        print(f"{self.emoji['info']} Gathering RAM info from /proc/meminfo...")
        self.hardware_info['ram_proc'] = self.get_ram_info_proc()
        
        print(f"{self.emoji['info']} Gathering RAM info from free command...")
        self.hardware_info['ram_free'] = self.get_ram_info_free()
        
        print(f"{self.emoji['info']} Gathering RAM info from dmidecode...")
        self.hardware_info['ram_dmidecode'] = self.get_ram_info_dmidecode()
        
        print(f"{self.emoji['info']} Gathering RAM info from sysfs...")
        self.hardware_info['ram_sysfs'] = self.get_ram_info_sysfs()
        
        print(f"{self.emoji['info']} Gathering VM statistics...")
        self.hardware_info['vmstat'] = self.get_ram_info_vmstat()
        
        # Additional information
        print(f"{self.emoji['info']} Gathering additional hardware info...")
        self.hardware_info['additional'] = self.get_additional_info()
        
        return self.hardware_info
    
    def generate_comprehensive_report(self):
        """Generate a comprehensive human-readable report"""
        report = []
        report.append("=" * 80)
        report.append("🐧 COMPREHENSIVE LINUX HARDWARE REPORT")
        report.append("=" * 80)
        
        # System Summary
        report.append("\n📊 SYSTEM SUMMARY")
        report.append("-" * 50)
        if 'system' in self.hardware_info:
            sys_info = self.hardware_info['system']
            if 'hostname' in sys_info and sys_info['hostname']:
                report.append(f"Hostname: {sys_info['hostname']}")
            if 'kernel' in sys_info and sys_info['kernel']:
                report.append(f"Kernel: {sys_info['kernel'].split(' ')[0]}")
        
        # CPU Summary
        report.append("\n🖥️ CPU SUMMARY")
        report.append("-" * 50)
        
        # From /proc/cpuinfo
        if 'cpu_proc' in self.hardware_info:
            cpu_proc = self.hardware_info['cpu_proc']
            if 'model_name' in cpu_proc:
                report.append(f"Processor: {cpu_proc['model_name']}")
            if 'processors' in cpu_proc:
                report.append(f"Logical CPUs: {cpu_proc['processors']}")
            if 'physical_cores' in cpu_proc:
                report.append(f"Physical Cores: {cpu_proc['physical_cores']}")
            if 'cpu_mhz' in cpu_proc:
                report.append(f"Frequency: {cpu_proc['cpu_mhz']} MHz")
        
        # From lscpu
        if 'cpu_lscpu' in self.hardware_info:
            lscpu = self.hardware_info['cpu_lscpu']
            if 'Architecture' in lscpu:
                report.append(f"Architecture: {lscpu['Architecture']}")
            if 'CPU(s)' in lscpu:
                report.append(f"Total CPUs: {lscpu['CPU(s)']}")
            if 'Thread(s) per core' in lscpu:
                report.append(f"Threads per Core: {lscpu['Thread(s) per core']}")
            if 'CPU max MHz' in lscpu:
                report.append(f"Max Frequency: {lscpu['CPU max MHz']} MHz")
        
        # RAM Summary
        report.append("\n💾 RAM SUMMARY")
        report.append("-" * 50)
        
        # From /proc/meminfo
        if 'ram_proc' in self.hardware_info:
            meminfo = self.hardware_info['ram_proc']
            if 'MemTotal' in meminfo:
                report.append(f"Total Memory: {meminfo['MemTotal']}")
            if 'MemAvailable' in meminfo:
                report.append(f"Available Memory: {meminfo['MemAvailable']}")
            if 'SwapTotal' in meminfo and meminfo['SwapTotal'] != '0 kB':
                report.append(f"Swap Total: {meminfo['SwapTotal']}")
        
        # From free command
        if 'ram_free' in self.hardware_info and 'detailed' in self.hardware_info['ram_free']:
            free_detailed = self.hardware_info['ram_free']['detailed']
            total_gb = int(free_detailed['total_bytes']) / (1024**3)
            available_gb = int(free_detailed['available_bytes']) / (1024**3)
            report.append(f"Total Memory: {total_gb:.2f} GB")
            report.append(f"Available Memory: {available_gb:.2f} GB")
        
        # Detailed Information Sections
        report.append("\n" + "=" * 80)
        report.append("📋 DETAILED INFORMATION")
        report.append("=" * 80)
        
        # CPU Details
        report.append("\n🔧 CPU DETAILS")
        report.append("-" * 30)
        if 'cpu_proc' in self.hardware_info:
            cpu_proc = self.hardware_info['cpu_proc']
            for key, value in cpu_proc.items():
                if key not in ['processors', 'model_name', 'physical_cores', 'cpu_mhz']:
                    if isinstance(value, list):
                        report.append(f"{key}: {', '.join(value[:5])}..." if len(value) > 5 else f"{key}: {', '.join(value)}")
                    else:
                        report.append(f"{key}: {value}")
        
        # RAM Details
        report.append("\n🔧 RAM DETAILS")
        report.append("-" * 30)
        if 'ram_proc' in self.hardware_info:
            meminfo = self.hardware_info['ram_proc']
            important_mem_keys = ['MemFree', 'Buffers', 'Cached', 'Active', 'Inactive', 
                                 'SwapCached', 'SwapTotal', 'SwapFree', 'Dirty', 'Writeback']
            for key in important_mem_keys:
                if key in meminfo:
                    report.append(f"{key}: {meminfo[key]}")
        
        # Additional Info
        report.append("\n🔧 ADDITIONAL INFORMATION")
        report.append("-" * 30)
        if 'additional' in self.hardware_info:
            additional = self.hardware_info['additional']
            for category, info in additional.items():
                report.append(f"{category}:")
                if isinstance(info, dict):
                    for k, v in info.items():
                        report.append(f"  {k}: {v}")
                else:
                    report.append(f"  {info}")
        
        return '\n'.join(report)
    
    def save_to_files(self):
        """Save results to JSON and text files"""
        # Save JSON
        with open('hardware_detailed.json', 'w') as f:
            json.dump(self.hardware_info, f, indent=2)
        
        # Save comprehensive report
        report = self.generate_comprehensive_report()
        with open('hardware_report.txt', 'w') as f:
            f.write(report)
        
        print(f"\n{self.emoji['success']} Results saved to:")
        print(f"   📄 hardware_detailed.json (Structured data)")
        print(f"   📄 hardware_report.txt (Human readable report)")

def main():
    """Main execution function"""
    detective = LinuxHardwareDetective()
    
    # Collect all hardware information
    print("🚀 Starting comprehensive hardware detection...")
    all_info = detective.collect_all_info()
    
    # Generate and display report
    print("\n" + "=" * 80)
    print("📊 GENERATING COMPREHENSIVE REPORT")
    print("=" * 80)
    
    report = detective.generate_comprehensive_report()
    print(report)
    
    # Save to files
    detective.save_to_files()
    
    # GitHub Actions output (modern method)
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f'hardware_status=completed', file=fh)
    
    print(f"\n{detective.emoji['success']} Hardware detection completed successfully!")

if __name__ == "__main__":
    main()
