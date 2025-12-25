import time

class PerfLogger:
    def __init__(self):
        self.last_time = time.time()
    
    def log(self, msg=""):
        current = time.time()
        delta = current - self.last_time
        print(f"{msg} Δt: {delta:.6f}s")
        self.last_time = current