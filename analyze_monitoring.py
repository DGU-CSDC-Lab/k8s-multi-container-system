#!/usr/bin/env python3
import pandas as pd
import re
import os

def parse_gpu_data(file_path):
    """Parse GPU CSV data and return max values"""
    try:
        df = pd.read_csv(file_path)
        gpu_util = df['utilization.gpu [%]'].str.replace(' %', '').astype(float).max()
        gpu_mem_util = df['utilization.memory [%]'].str.replace(' %', '').astype(float).max()
        gpu_mem_used = df['memory.used [MiB]'].str.replace(' MiB', '').astype(float).max()
        return gpu_util, gpu_mem_util, gpu_mem_used
    except:
        return 0, 0, 0

def parse_system_data(file_path):
    """Parse system log data and return max CPU usage and memory usage"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract CPU usage percentages
        cpu_pattern = r'%Cpu:\s*(\d+\.\d+)\s*us'
        cpu_matches = re.findall(cpu_pattern, content)
        max_cpu = max([float(x) for x in cpu_matches]) if cpu_matches else 0
        
        # Extract memory usage from process lines
        mem_pattern = r'\s+\d+\s+\w+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\w+\s+[\d.]+\s+([\d.]+)'
        mem_matches = re.findall(mem_pattern, content)
        max_mem = max([float(x) for x in mem_matches]) if mem_matches else 0
        
        return max_cpu, max_mem
    except:
        return 0, 0

# Data format mappings
formats = {
    'single': ('gpu_bm_single.csv', 'system_bm_single.log'),
    'optimized': ('gpu_bm_optimized.csv', 'system_bm_optimized.log'),
    'parquet_final': ('gpu_bm_parquet_final.csv', 'system_bm_single.log'),  # Using single as fallback
    'npy': ('gpu_npy_methodology_test.csv', 'system_mem_npy_methodology_test.log')
}

base_path = '/Users/eunji/Desktop/Project/k8s-multi-container-system/proto-gcn/monitoring_logs'
results = []

for format_name, (gpu_file, sys_file) in formats.items():
    gpu_path = os.path.join(base_path, gpu_file)
    sys_path = os.path.join(base_path, sys_file)
    
    # Get GPU data
    gpu_util, gpu_mem_util, gpu_mem_used = parse_gpu_data(gpu_path)
    
    # Get system data
    cpu_util, cpu_mem_util = parse_system_data(sys_path)
    
    results.append({
        'Format': format_name,
        'GPU MEM 사용 %': f"{gpu_mem_util:.1f}%",
        'GPU MEM 사용량': f"{gpu_mem_used:.0f} MiB",
        'CPU 코어 사용 %': f"{cpu_util:.1f}%",
        'CPU MEM 사용 %': f"{cpu_mem_util:.1f}%"
    })

# Create and display table
df = pd.DataFrame(results)
print("=" * 80)
print("데이터 포맷별 리소스 사용량 비교")
print("=" * 80)
print(df.to_string(index=False))
print("=" * 80)
