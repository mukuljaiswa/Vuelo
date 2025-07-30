import threading
import os
import csv
from locust import events
import random
from datetime import datetime, timezone
import uuid
import string

class CredentialManager:
    _lock = threading.Lock()
    _index_lock = threading.Lock()
    _counter_lock = threading.Lock()

    # These will be per-process
    _user_counter = 0
    _user_credentials = []
    _local_credentials = []
    _local_credential_index = 0
    _worker_index = 0
    _worker_count = 1

    @classmethod
    def assign_user_id(cls):
        """Assign a unique user ID per thread."""
        with cls._counter_lock:
            uid = cls._user_counter
            cls._user_counter += 1
            return uid

    @classmethod
    def configure_for_worker(cls, worker_index=None, worker_count=None):
        """Configure the credential range for a specific worker."""
        if worker_index is None:
            worker_index = int(os.environ.get("LOCUST_WORKER_INDEX", "0"))
        if worker_count is None:
            worker_count = int(os.environ.get("LOCUST_PROCESS_COUNT", "1"))

        cls._worker_index = worker_index
        cls._worker_count = worker_count
        cls._local_credential_index = 0

        print(f"[Worker {cls._worker_index}] Configuring with {cls._worker_count} total workers")
        cls.load_user_credentials()
    

    @classmethod
    def init_csv_files(cls):
        os.makedirs('users', exist_ok=True)
        csv_path = 'users/users.csv'
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            print("Initializing new users.csv file")
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow(['email', 'password'])


    @classmethod
    def save_credentials(cls, email, password, user_id):
        with cls._lock:
            print(f"User {user_id} saving credentials for {email}")
            with open('users/users.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow([email, password])
            cls.load_user_credentials()
    

    @classmethod
    def load_user_credentials(cls):
        """Load and split credentials among workers."""
        csv_path = 'users/login_credentials.csv'
        if not os.path.exists(csv_path):
            print(f"[Worker {cls._worker_index}] WARNING: CSV file not found at {csv_path}")
            return

        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            all_creds = list(csv.DictReader(csvfile))
            total = len(all_creds)
            
            # Split credentials across workers
            chunk_size = total // cls._worker_count
            remainder = total % cls._worker_count
            
            start = cls._worker_index * chunk_size
            end = start + chunk_size
            
            # Distribute remainder across first workers
            if cls._worker_index < remainder:
                start += cls._worker_index
                end += cls._worker_index + 1
            else:
                start += remainder
                end += remainder

            cls._local_credentials = all_creds[start:end]
            print(f"[Worker {cls._worker_index}] Loaded {len(cls._local_credentials)} credentials (index {start} to {end-1})")

    @classmethod
    def get_next_credentials(cls):
        """Return next available credentials for this worker."""
        with cls._index_lock:
            if not cls._local_credentials:
                print(f"[Worker {cls._worker_index}] No credentials available")
                return None, None

            cred = cls._local_credentials[cls._local_credential_index]
            print(f"[Worker {cls._worker_index}] Using credential index {cls._local_credential_index}: {cred['email']}")

            cls._local_credential_index = (cls._local_credential_index + 1) % len(cls._local_credentials)
            return cred['email'], cred['password']
        
class CredentialManagerUserUtils:
    @staticmethod
    def generate_random_name(length=8):
        name = ''.join(random.choice(string.ascii_letters) for _ in range(length)).capitalize()
        return name

    @staticmethod
    def generate_dynamic_email():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:8]
        email = f"loadtest_{random_part}_{timestamp}@yopmail.com"
        return email

    @staticmethod
    def generate_strong_password():
        components = [
            random.choice('!@#$%^&*'),
            random.choice(string.ascii_uppercase),
            *random.choices(string.digits, k=3),
            *random.choices(string.ascii_lowercase, k=3)
        ]
        random.shuffle(components)
        password = ''.join(components)
        return password


    @staticmethod
    def generate_random_phone_number():
        # Generate a random 10-digit number starting with 6, 7, 8, or 9
        first_digit = str(random.choice([6, 7, 8, 9]))
        remaining_digits = ''.join(str(random.randint(0, 9)) for _ in range(9))
        phone_number = first_digit + remaining_digits
        return f'+91{phone_number}'
