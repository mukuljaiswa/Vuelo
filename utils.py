import threading
import os
import csv
import random
import string
from datetime import datetime, timezone
import uuid

class CredentialManager:
    _lock = threading.Lock()
    _index_lock = threading.Lock()
    _counter_lock = threading.Lock()
    _user_credentials = []
    _credential_index = 0
    _user_counter = 0

    @classmethod
    def assign_user_id(cls):
        with cls._counter_lock:
            uid = cls._user_counter
            cls._user_counter += 1
            return uid

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
    def load_user_credentials(cls):
        csv_path = 'users/users_login_credentials.csv'
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                cls._user_credentials = list(reader)
                print(f"Loaded {len(cls._user_credentials)} user credentials")
        else:
            print("Warning: No credentials file found at users/users_login_credentials.csv")

    @classmethod
    def get_next_credentials(cls):
        with cls._index_lock:
            if not cls._user_credentials:
                print("No credentials available")
                return None, None
            credentials = cls._user_credentials[cls._credential_index]
            print(f"Assigned credentials index {cls._credential_index}: {credentials['email']}")
            cls._credential_index = (cls._credential_index + 1) % len(cls._user_credentials)
            return credentials['email'], credentials['password']

    @classmethod
    def save_credentials(cls, email, password, user_id):
        with cls._lock:
            print(f"User {user_id} saving credentials for {email}")
            with open('users/users.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow([email, password])
            cls.load_user_credentials()

class UserUtils:
    @staticmethod
    def generate_random_name(user_id, length=8):
        name = ''.join(random.choice(string.ascii_letters) for _ in range(length)).capitalize()
        return name

    @staticmethod
    def generate_dynamic_email(user_id):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:8]
        email = f"loadtest_{random_part}_{timestamp}@yopmail.com"
        return email

    @staticmethod
    def generate_strong_password(user_id):
        components = [
            random.choice('!@#$%^&*'),
            random.choice(string.ascii_uppercase),
            *random.choices(string.digits, k=3),
            *random.choices(string.ascii_lowercase, k=3)
        ]
        random.shuffle(components)
        password = ''.join(components)
        return password
