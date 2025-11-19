#!/usr/bin/env python3
"""
Script to get CPU and RAM information using multiple methods
Compatible with GitHub Actions workflows
"""

import os
import platform
import subprocess
import sys
import json

class HardwareInfo:
    def __init__(self):
        self.system = platform.system().lower()
    
    def get_cpu_info_method1(self):
        """Method 1: Using platform and os modules"""
        try:
            cpu_info = {
                "architecture": platform.architecture()[0],
                "machine": platform.machine(),
                "processor": platform.processor(),
                "system": platform.system(),
                "cpu_count": os.cpu_count(),
                "platform": platform.platform()
            }
            return cpu_info
        except Exception as e:
            return {"error": f"Method 1 failed: {str(e)}"}
    
    def get_cpu_info_method2(self):
        """Method 2: Using /proc/cpuinfo on Linux systems"""
        try:
            if self.system != "linux":
                return {"error": "Method 2 only works on Linux systems"}
            
            cpu_info = {}
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.strip():
                        if ':' in line:
                            key, value = line.split(':', 1)
                            cpu_info[key.strip()] = value.strip()
            
            # Extract key information
            result = {
                "model_name": cpu_info.get('model name', 'Unknown'),
                "cores": int(cpu_info.get('cpu cores', 1)),
                "threads": len([k for k in cpu_info.keys() if k.startswith('processor')]),
                "vendor_id": cpu_info.get('vendor_id', 'Unknown')
            }
            return result
        except Exception as e:
            return {"error": f"Method 2 failed: {str(e)}"}
    
    def get_cpu_info_method3(self):
        """Method 3: Using subprocess and system commands"""
        try:
            if self.system == "linux":
                # Get CPU info using lscpu
                result = subprocess.run(['lscpu'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    cpu_info = {}
                    for line in result.stdout.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            cpu_info[key.strip()] = value.strip()
                    return cpu_info
            elif self.system == "darwin":  # macOS
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return {"cpu_model": result.stdout.strip()}
            
            return {"error": f"Method 3 not supported on {self.system}"}
        except Exception as e:
            return {"error": f"Method 3 failed: {str(e)}"}
    
    def get_ram_info_method1(self):
        """Method 1: Using /proc/meminfo on Linux"""
        try:
            if self.system != "linux":
                return {"error": "Method 1 only works on Linux systems"}
            
            mem_info = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        mem_info[key.strip()] = value.strip()
            
            return {
                "total_memory": mem_info.get('MemTotal', 'Unknown'),
                "free_memory": mem_info.get('MemFree', 'Unknown'),
                "available_memory": mem_info.get('MemAvailable', 'Unknown')
            }
        except Exception as e:
            return {"error": f"RAM Method 1 failed: {str(e)}"}
    
    def get_ram_info_method2(self):
        """Method 2: Using subprocess and free command"""
        try:
            if self.system != "linux":
                return {"error": "Method 2 only works on Linux systems"}
            
            result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                if len(lines) >= 2:
                    headers = lines[0].split()
                    memory_line = lines[1].split()
                    return {
                        "total": memory_line[1] if len(memory_line) > 1 else 'Unknown',
                        "used": memory_line[2] if len(memory_line) > 2 else 'Unknown',
                        "free": memory_line[3] if len(memory_line) > 3 else 'Unknown'
                    }
            return {"error": "Failed to parse free command output"}
        except Exception as e:
            return {"error": f"RAM Method 2 failed: {str(e)}"}
    
    def get_ram_info_method3(self):
        """Method 3: Using psutil if available, otherwise fallback"""
        try:
            # Try to import psutil
            import psutil
            memory = psutil.virtual_memory()
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent_used": memory.percent
            }
        except ImportError:
            return {"error": "psutil not available, using alternative methods"}
        except Exception as e:
            return {"error": f"RAM Method 3 failed: {str(e)}"}
    
    def collect_all_info(self):
        """Collect all hardware information using multiple methods"""
        print("🔍 Collecting Hardware Information...")
        print(f"🏷️  System: {platform.system()} {platform.release()}")
        print("\n" + "="*50)
        
        # CPU Information
        print("\n🖥️  CPU INFORMATION:")
        print("-" * 30)
        
        cpu_methods = [
            ("Platform Module", self.get_cpu_info_method1()),
            ("/proc/cpuinfo", self.get_cpu_info_method2()),
            ("System Commands", self.get_cpu_info_method3())
        ]
        
        for method_name, info in cpu_methods:
            print(f"\n📋 {method_name}:")
            if "error" in info:
                print(f"   ❌ {info['error']}")
            else:
                for key, value in info.items():
                    print(f"   • {key}: {value}")
        
        # RAM Information
        print("\n💾 RAM INFORMATION:")
        print("-" * 30)
        
        ram_methods = [
            ("/proc/meminfo", self.get_ram_info_method1()),
            ("free command", self.get_ram_info_method2()),
            ("psutil", self.get_ram_info_method3())
        ]
        
        for method_name, info in ram_methods:
            print(f"\n📋 {method_name}:")
            if "error" in info:
                print(f"   ❌ {info['error']}")
            else:
                for key, value in info.items():
                    print(f"   • {key}: {value}")
        
        return {
            "cpu_methods": cpu_methods,
            "ram_methods": ram_methods
        }

def main():
    """Main function"""
    hardware = HardwareInfo()
    
    # Collect all information
    all_info = hardware.collect_all_info()
    
    # Save to JSON file for GitHub Actions
    output_file = "hardware_info.json"
    with open(output_file, 'w') as f:
        json.dump(all_info, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Print GitHub Actions format
    print("\n🚀 GitHub Actions Output Format:")
    print("::set-output name=hardware_info::" + json.dumps({"status": "completed"}))

if __name__ == "__main__":
    main()
