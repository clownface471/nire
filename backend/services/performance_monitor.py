"""
Performance Monitor
Tracks latency and throughput.
"""
import time
import structlog

logger = structlog.get_logger()

class PerformanceMonitor:
    def __init__(self):
        self.start_time = 0
        self.metrics = {}

    def start(self, task_name: str):
        self.start_time = time.time()
        self.metrics[task_name] = {"start": self.start_time}

    def stop(self, task_name: str, tokens: int = 0):
        if task_name in self.metrics:
            end_time = time.time()
            duration = end_time - self.metrics[task_name]["start"]
            self.metrics[task_name]["duration"] = duration
            
            if tokens > 0:
                self.metrics[task_name]["tokens_per_sec"] = tokens / duration
                
            return duration
        return 0