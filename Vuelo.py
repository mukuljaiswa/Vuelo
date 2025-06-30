from locust import HttpUser, task, between
import random
import string
from datetime import datetime, timezone
import uuid
import json
import csv
import os
import threading

class SierraDimensionsUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://qa-api.sierradimensions.com"
    
    # Class-level variables for thread-safe credential management
    _lock = threading.Lock()
    _user_credentials = []
    _credential_index = 0
    _index_lock = threading.Lock()
    _user_counter = 0
    _counter_lock = threading.Lock()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with self._counter_lock:
            self.user_id = self._user_counter
            self.__class__._user_counter += 1
        
        self.email = None
        self.password = None
        self.session_cookies = {}
        self.auth_token = None
        
        # Initialize users directory and CSV files
        os.makedirs('users', exist_ok=True)
        self._init_csv_files()
        
        # Load credentials once for the class
        with self._lock:
            if not self.__class__._user_credentials:
                self.__class__._load_user_credentials()
        print(f"User {self.user_id} initialized - {len(self.__class__._user_credentials)} credentials available")

    def _init_csv_files(self):
        """Initialize CSV files if they don't exist"""
        csv_path = 'users/users.csv'
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            print("Initializing new users.csv file")
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow(['email', 'password'])

    @classmethod
    def _load_user_credentials(cls):
        """Load user credentials from CSV file"""
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
        """Get next credentials in a thread-safe round-robin fashion"""
        with cls._index_lock:
            if not cls._user_credentials:
                print("No credentials available")
                return None, None
            
            # Get the next credential in sequence
            credentials = cls._user_credentials[cls._credential_index]
            print(f"Assigned credentials index {cls._credential_index}: {credentials['email']}")
            
            # Move to next credential (with wrap-around)
            cls._credential_index = (cls._credential_index + 1) % len(cls._user_credentials)
            
            return credentials['email'], credentials['password']

    def generate_random_name(self, length=8):
        """Generate a random name with specified length"""
        name = ''.join(random.choice(string.ascii_letters) for _ in range(length)).capitalize()
        print(f"User {self.user_id} generated name: {name}")
        return name
    
    def generate_dynamic_email(self):
        """Generate a dynamic email with current UTC timestamp"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:8]
        email = f"loadtest_{random_part}_{timestamp}@yopmail.com"
        print(f"User {self.user_id} generated email: {email}")
        return email
    
    def generate_strong_password(self):
        """Generate a strong password"""
        components = [
            random.choice('!@#$%^&*'),  # 1 special char
            random.choice(string.ascii_uppercase),  # 1 uppercase
            *random.choices(string.digits, k=3),  # 3 digits
            *random.choices(string.ascii_lowercase, k=3)  # 3 lowercase
        ]
        random.shuffle(components)
        password = ''.join(components)
        print(f"User {self.user_id} generated password: {password}")
        return password
    
    def save_credentials(self, email, password):
        """Save credentials to CSV file"""
        with self._lock:
            print(f"User {self.user_id} saving credentials for {email}")
            with open('users/users.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow([email, password])
            self.__class__._load_user_credentials()  # Refresh credentials
    
    @task(1)
    def test_user_registration_flow(self):
        """Test the complete user registration flow"""
        print(f"\nUser {self.user_id} starting registration flow")
        self.password = self.generate_strong_password()
        user_data = {
            "first_name": self.generate_random_name(),
            "last_name": self.generate_random_name(),
            "email": self.generate_dynamic_email(),
            "date_of_birth": "2001-08-15",
            "password": self.password,
            "confirm_password": self.password,
            "terms_accepted": True
        }
        print(f"User {self.user_id} registration data: {user_data}")
        
        with self.client.post(
            "/api/v1/public/signup",
            json=user_data,
            name="1. User Signup",
            catch_response=True
        ) as response:
            print(f"User {self.user_id} Signup Response: {response.text}")
            if response.status_code != 201:
                response.failure(f"Signup failed: {response.text}")
            elif response.cookies:
                self.session_cookies.update(response.cookies)
                print(f"User {self.user_id} updated session cookies from signup")
        
        otp_data = {
            "contact": user_data["email"],
            "otp": "000000",
            "verify_type": "SIGNUP"
        }
        print(f"User {self.user_id} OTP verification data: {otp_data}")
        
        with self.client.post(
            "/api/v1/public/verify",
            json=otp_data,
            name="2. Verify OTP (SIGNUP)",
            catch_response=True
        ) as response:
            print(f"User {self.user_id} OTP Verification Response: {response.text}")
            if response.status_code in (200, 201):
                if response.cookies:
                    self.session_cookies.update(response.cookies)
                    print(f"User {self.user_id} updated session cookies from OTP verification")
                try:
                    response_data = response.json()
                    if response_data.get('success'):
                        self.auth_token = response_data.get('data', {}).get('token')
                        print(f"User {self.user_id} auth token received: {self.auth_token}")
                        self.save_credentials(user_data["email"], self.password)
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"OTP verification failed: {response.text}")
        
        if self.session_cookies:
            print(f"User {self.user_id} attempting to get user profile")
            with self.client.get(
                "/api/v1/user/me",
                cookies=self.session_cookies,
                name="3. Get User Profile",
                catch_response=True
            ) as response:
                print(f"User {self.user_id} Profile Response: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile fetch failed: {response.text}")
    
    @task(7)
    def test_user_login_flow(self):
        """Test the complete user login flow"""
        print(f"\nUser {self.user_id} starting login flow")
        email, password = self.__class__.get_next_credentials()
        if not email or not password:
            print(f"User {self.user_id}: No valid credentials available for login")
            return

        print(f"User {self.user_id} attempting login with email: {email}")
        
        with self.client.post(
            "/api/v1/public/login",
            json={"contact": email, "password": password},
            name="1. User Login",
            catch_response=True
        ) as response:
            print(f"User {self.user_id} Login Response: {response.text}")
            if response.status_code != 201:
                response.failure(f"Login failed: {response.text}")
            elif response.cookies:
                self.session_cookies.update(response.cookies)
                print(f"User {self.user_id} updated session cookies from login")
        
        otp_data = {
            "contact": email,
            "otp": "000000",
            "verify_type": "LOGIN"
        }
        print(f"User {self.user_id} Login OTP data: {otp_data}")
        
        with self.client.post(
            "/api/v1/public/verify",
            json=otp_data,
            name="2. Verify OTP (LOGIN)",
            catch_response=True
        ) as response:
            print(f"User {self.user_id} Login OTP Verification Response: {response.text}")
            if response.status_code in (200, 201):
                if response.cookies:
                    self.session_cookies.update(response.cookies)
                    print(f"User {self.user_id} updated session cookies from login OTP")
                try:
                    response_data = response.json()
                    if response_data.get('success'):
                        self.auth_token = response_data.get('data', {}).get('token')
                        print(f"User {self.user_id} login auth token received: {self.auth_token}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Login OTP verification failed: {response.text}")
        
        if self.session_cookies:
            print(f"User {self.user_id} attempting to get user profile after login")
            with self.client.get(
                "/api/v1/user/me",
                cookies=self.session_cookies,
                name="3. Get User Profile After Login",
                catch_response=True
            ) as response:
                print(f"User {self.user_id} Post-Login Profile Response: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile fetch failed: {response.text}")

    def on_start(self):
        """Initialize user when starting"""
        print(f"\n=== User {self.user_id} started ===")
