#!/usr/bin/env python3
import json
import time
import redis
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

class RedisJobQueue:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        self.queue_key = 'job_queue'
        self.running_key = 'running_jobs'
    
    def add_job(self, job):
        job['timestamp'] = time.time()
        job['status'] = 'queued'
        self.redis_client.lpush(self.queue_key, json.dumps(job))
        print(f"Job added to Redis queue: {job['user']}")
    
    def get_next_job(self):
        job_data = self.redis_client.rpop(self.queue_key)
        if job_data:
            job = json.loads(job_data)
            self.redis_client.hset(self.running_key, job['user'], json.dumps(job))
            return job
        return None
    
    def complete_job(self, user):
        self.redis_client.hdel(self.running_key, user)
    
    def get_status(self):
        queue_length = self.redis_client.llen(self.queue_key)
        running_jobs = self.redis_client.hlen(self.running_key)
        queued_jobs = []
        
        # 큐에 있는 작업들 조회
        for i in range(min(queue_length, 10)):  # 최대 10개만
            job_data = self.redis_client.lindex(self.queue_key, i)
            if job_data:
                job = json.loads(job_data)
                queued_jobs.append({'user': job['user'], 'timestamp': job['timestamp']})
        
        return {
            'queue_length': queue_length,
            'running_jobs': running_jobs,
            'queued_jobs': queued_jobs
        }

class QueueHandler(BaseHTTPRequestHandler):
    queue = None
    
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
            status = self.queue.get_status()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())

def scheduler_loop(queue):
    print("Redis Scheduler started")
    while True:
        try:
            # GPU 사용 가능한지 확인
            running_jobs = queue.redis_client.hlen('running_jobs')
            if running_jobs == 0:  # GPU 사용 가능
                job = queue.get_next_job()
                if job:
                    print(f"Processing job for user: {job['user']}")
                    
                    # Argo Workflow 실행
                    cmd = [
                        'argo', 'submit', '/workflows/proto-gcn-workflow.yaml',
                        '-n', 'argo',
                        '--serviceaccount', 'argo-server',
                        '-p', f"user={job['user']}",
                        '-p', f"data-url={job.get('data_url', 'dummy')}",
                        '-p', f"config-file={job['config_file']}",
                        '-p', f"work-dir={job['work_dir']}"
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Workflow submitted successfully for {job['user']}")
                    else:
                        print(f"Workflow submission failed: {result.stderr}")
                        queue.complete_job(job['user'])  # 실패시 running에서 제거
            
            time.sleep(5)
        except Exception as e:
            print(f"Scheduler error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    print("=== Redis Queue Manager Starting ===")
    
    # Redis 연결 대기
    while True:
        try:
            queue = RedisJobQueue()
            queue.redis_client.ping()
            print("Redis connection established")
            break
        except Exception as e:
            print(f"Waiting for Redis... {e}")
            time.sleep(5)
    
    # 스케줄러 스레드 시작
    scheduler_thread = Thread(target=scheduler_loop, args=(queue,))
    scheduler_thread.daemon = True
    scheduler_thread.start()
    print("Scheduler thread started")
    
    # HTTP 서버 시작
    QueueHandler.queue = queue
    server = HTTPServer(('0.0.0.0', 8081), QueueHandler)
    print('Redis Queue manager started on port 8081')
    server.serve_forever()
