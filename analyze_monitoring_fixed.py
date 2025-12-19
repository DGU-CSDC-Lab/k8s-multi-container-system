#!/usr/bin/env python3
import re
import os

def parse_gpu_data(file_path):
    """Parse GPU CSV data and return max values"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
        
        gpu_utils = []
        gpu_mem_utils = []
        gpu_mem_used = []
        
        for line in lines:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:
                gpu_utils.append(float(parts[2].replace(' %', '')))
                gpu_mem_utils.append(float(parts[3].replace(' %', '')))
                gpu_mem_used.append(float(parts[4].replace(' MiB', '')))
        
        return max(gpu_utils), max(gpu_mem_utils), max(gpu_mem_used)
    except Exception as e:
        return 0, 0, 0

def parse_system_data(file_path):
    """Parse system log data and return max CPU usage and memory usage"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # CPU 사용률: us + sy 값들의 합계 중 최대값
        cpu_us_pattern = r'%Cpu:\s*(\d+\.\d+)\s*us,\s*(\d+\.\d+)\s*sy'
        cpu_matches = re.findall(cpu_us_pattern, content)
        max_cpu = max([float(us) + float(sy) for us, sy in cpu_matches]) if cpu_matches else 0
        
        # 메모리 사용률: 프로세스 라인에서 %MEM 컬럼 (9번째 컬럼)
        # 형식: PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
        mem_pattern = r'\s+\d+\s+\w+\s+\d+\s+\d+\s+[\d.]+[gm]?\s+[\d.]+[gm]?\s+\d+\s+\w+\s+[\d.]+\s+([\d.]+)'
        mem_matches = re.findall(mem_pattern, content)
        max_mem = max([float(x) for x in mem_matches]) if mem_matches else 0
        
        return max_cpu, max_mem
    except Exception as e:
        return 0, 0

# Data format mappings
formats = {
    'single': ('gpu_bm_single.csv', 'system_bm_single.log'),
    'optimized': ('gpu_bm_optimized.csv', 'system_bm_optimized.log'),
    'parquet_final': ('gpu_bm_parquet_final.csv', 'system_bm_single.log'),
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
    
    results.append([
        format_name,
        f"{gpu_mem_util:.1f}%",
        f"{gpu_mem_used:.0f} MiB",
        f"{cpu_util:.1f}%",
        f"{cpu_mem_util:.1f}%"
    ])

# Display table
print("=" * 85)
print("데이터 포맷별 리소스 사용량 비교 (수정됨)")
print("=" * 85)
print(f"{'Format':<15} {'GPU MEM 사용 %':<15} {'GPU MEM 사용량':<15} {'CPU 코어 사용 %':<15} {'CPU MEM 사용 %':<15}")
print("-" * 85)
for row in results:
    print(f"{row[0]:<15} {row[1]:<15} {row[2]:<15} {row[3]:<15} {row[4]:<15}")
print("=" * 85)
