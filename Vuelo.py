from locust import HttpUser, between, task, events
from tasks import SierraDimensionsTasks
from utils import CredentialManager
from dotenv import load_dotenv
import os
import multiprocessing
import time

# Load environment variables
load_dotenv()

# Global worker variables
worker_id = 0
total_workers = 1
process_initialized = False

# We'll use a file-based counter for process-safe unique IDs
COUNTER_FILE = "/tmp/locust_user_counter.txt"

def get_next_user_id():
    """Get a unique user ID using file locking"""
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'w') as f:
            f.write('0')
    
    for _ in range(10):  # Retry mechanism
        try:
            with open(COUNTER_FILE, 'r+') as f:
                # Simple file locking by checking file size
                if os.fstat(f.fileno()).st_size > 10:
                    time.sleep(0.1)
                    continue
                    
                current_id = int(f.read() or 0)
                f.seek(0)
                f.write(str(current_id + 1))
                f.truncate()
                return current_id
        except (BlockingIOError, ValueError):
            time.sleep(0.1)
    return int(time.time() * 1000) % 1000000  # Fallback

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global worker_id, total_workers, process_initialized
    
    if process_initialized:
        return
        
    if hasattr(environment.runner, "worker_index"):
        worker_id = environment.runner.worker_index
        is_worker = True
    else:
        worker_id = int(os.environ.get("LOCUST_WORKER_INDEX", "0"))
        is_worker = os.environ.get("LOCUST_MODE") == "worker" or bool(os.environ.get("LOCUST_WORKER_INDEX"))
    
    if hasattr(environment.parsed_options, 'processes'):
        if environment.parsed_options.processes == -1:
            total_workers = multiprocessing.cpu_count()
        else:
            total_workers = environment.parsed_options.processes or 1
    elif hasattr(environment.runner, "worker_count"):
        total_workers = environment.runner.worker_count
    else:
        total_workers = 1
    
    if is_worker:
        print(f"Worker {worker_id} initialized (Total workers: {total_workers}, PID: {os.getpid()})")
    else:
        print(f"Master process initialized (PID: {os.getpid()})")
    
    process_initialized = True


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global worker_id, total_workers
    
    if not hasattr(environment.runner, "worker_index") and not os.environ.get("LOCUST_WORKER_INDEX"):
        return
        
    if hasattr(environment.runner, "worker_count"):
        total_workers = environment.runner.worker_count
    elif hasattr(environment.runner, "workers"):
        total_workers = len(environment.runner.workers) or 1
    
    CredentialManager.configure_for_worker(worker_id, total_workers)
    print(f"Worker {worker_id}: CredentialManager configured with {total_workers} workers")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Clean up counter file when test stops"""
    if os.path.exists(COUNTER_FILE):
        try:
            os.remove(COUNTER_FILE)
        except:
            pass

class SierraDimensionsUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("HOST")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.environment.runner, "worker_index") and not os.environ.get("LOCUST_WORKER_INDEX"):
            return
            
        self.user_id = get_next_user_id()
        self.worker_id = worker_id
        self.email = None
        self.password = None
        self.session_cookies = {}
        self.auth_token = None
        self.tasks_impl = SierraDimensionsTasks(self)
        print(f"Worker {self.worker_id}: User {self.user_id} initialized (PID: {os.getpid()})")

    def on_start(self):
        if not hasattr(self.environment.runner, "worker_index") and not os.environ.get("LOCUST_WORKER_INDEX"):
            return
        print(f"\nWorker {self.worker_id}: User {self.user_id} started")


    @task(1)
    def test_user_registration_flow(self):
        if not hasattr(self.environment.runner, "worker_index") and not os.environ.get("LOCUST_WORKER_INDEX"):
            return
        print(f"Worker {self.worker_id}: User {self.user_id} executing signup flow")
        self.tasks_impl.test_user_registration_flow()

    @task(1)
    def test_user_login_flow(self):
        if not hasattr(self.environment.runner, "worker_index") and not os.environ.get("LOCUST_WORKER_INDEX"):
            return
        print(f"Worker {self.worker_id}: User {self.user_id} executing login flow")
        self.tasks_impl.test_user_login_flow()

    