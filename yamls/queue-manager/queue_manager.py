#!/usr/bin/env python3
import json
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import subprocess

class JobQueue:
    def __init__(self):
        self.queue = []
        self.running_jobs = {}
    
    def add_job(self, job):
        job['timestamp'] = time.time()
        job['status'] = 'queued'
        self.queue.append(job)
        print(f"Job added to queue: {job['user']}")
    
    def get_next_job(self):
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def check_resources(self):
        try:
            response = requests.get('http://resource-monitor:8080/status', timeout=5)
            return response.json().get('available', False)
        except:
            return False
    
    def submit_workflow(self, job):
        cmd = [
            'argo', 'submit', '/workflows/proto-gcn-workflow.yaml',
            '-n', 'argo',
            '--serviceaccount', 'argo-server',
            '-p', f"user={job['user']}",
            '-p', f"config-file={job['config_file']}",
            '-p', f"ann-file={job['ann_file']}",
            '-p', f"work-dir={job['work_dir']}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            workflow_name = result.stdout.strip().split()[-1]
            self.running_jobs[workflow_name] = job
            print(f"Workflow submitted: {workflow_name} for user {job['user']}")
            return workflow_name
        else:
            print(f"Failed to submit workflow: {result.stderr}")
            return None

class QueueHandler(BaseHTTPRequestHandler):
    queue = JobQueue()
    
    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            job = json.loads(post_data.decode('utf-8'))
            
            self.queue.add_job(job)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'queued'}).encode())
    
    def do_GET(self):
        if self.path == '/status':
            status = {
                'queue_length': len(self.queue.queue),
                'running_jobs': len(self.queue.running_jobs),
                'queued_jobs': [{'user': job['user'], 'timestamp': job['timestamp']} for job in self.queue.queue]
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())

def scheduler_loop(queue):
    print("Scheduler started")
    while True:
        print(f"Checking resources... Queue length: {len(queue.queue)}")
        if queue.check_resources():
            print("Resources available")
            job = queue.get_next_job()
            if job:
                print(f"Submitting job for user: {job['user']}")
                queue.submit_workflow(job)
        time.sleep(10)

if __name__ == '__main__':
    print("=== Queue Manager Starting ===")
    queue = JobQueue()
    print("JobQueue created")
    
    # 스케줄러 스레드 시작
    print("Starting scheduler thread...")
    scheduler_thread = Thread(target=scheduler_loop, args=(queue,))
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("Scheduler thread started")
    
    # HTTP 서버 시작
    QueueHandler.queue = queue
    server = HTTPServer(('0.0.0.0', 8081), QueueHandler)
    print('Queue manager started on port 8081')
    server.serve_forever()
