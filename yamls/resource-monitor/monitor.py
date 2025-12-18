#!/usr/bin/env python3
import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class ResourceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            status = self.get_resource_status()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
    
    def get_resource_status(self):
        try:
            gpu = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
                                '--format=csv,noheader,nounits'], capture_output=True, text=True)
            gpu_util, gpu_mem_used, gpu_mem_total = gpu.stdout.strip().split(',')
            
            mem = subprocess.run(['free', '-m'], capture_output=True, text=True)
            mem_line = mem.stdout.split('\n')[1].split()
            mem_total, mem_used = int(mem_line[1]), int(mem_line[2])
            
            gpu_util_val = int(float(gpu_util.strip()))
            mem_util_val = int(mem_used * 100 / mem_total)
            
            return {
                'gpu_utilization': gpu_util_val,
                'gpu_memory_used': int(float(gpu_mem_used.strip())),
                'gpu_memory_total': int(float(gpu_mem_total.strip())),
                'memory_utilization': mem_util_val,
                'available': gpu_util_val < 80 and mem_util_val < 85
            }
        except Exception as e:
            return {'error': str(e), 'available': False}

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), ResourceHandler)
    print('Resource monitor started on port 8080')
    server.serve_forever()
