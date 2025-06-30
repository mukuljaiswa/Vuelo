from locust import HttpUser, task, between
import random
import string
from datetime import datetime, timezone
import uuid
import json
import csv

class SierraDimensionsUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://qa-api.sierradimensions.com"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email = None
        self.password = "Test@123"
        self.session_cookies = {}  # Initialize as empty dict
        self.auth_token = None
        # Initialize CSV file with header if it doesn't exist
        with open('users/users.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header only if file is empty
            if csvfile.tell() == 0:
                writer.writerow(['email'])
    
    def generate_random_name(self, length=8):
        """Generate a random name with specified length"""
        return ''.join(random.choice(string.ascii_letters) for _ in range(length)).capitalize()
    
    def generate_dynamic_email(self):
        """Generate a dynamic email with current UTC timestamp"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:8]
        return f"loadtest_{random_part}_{timestamp}@yopmail.com"
    
    def save_email_to_csv(self, email):
        """Save the email to users.csv file"""
        with open('users/users.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([email])
    
    @task
    def test_user_registration_flow(self):
        # Generate dynamic user data
        first_name = self.generate_random_name()
        last_name = self.generate_random_name()
        self.email = self.generate_dynamic_email()
        
        # Step 1: Signup
        signup_payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": self.email,
            "date_of_birth": "2001-08-15",
            "password": self.password,
            "confirm_password": self.password,
            "terms_accepted": True
        }
        
        with self.client.post(
            "/api/v1/public/signup",
            json=signup_payload,
            name="1. User Signup",
            catch_response=True
        ) as response:
            print(f"Signup Response: {response.text}")
            if response.status_code != 201:
                response.failure(f"Signup failed: {response.text}")
            elif response.cookies:
                self.session_cookies.update(response.cookies)
        
        # Step 2: OTP Verification
        otp_payload = {
            "contact": self.email,
            "otp": "000000",  # Test OTP
            "verify_type": "SIGNUP"
        }
        
        with self.client.post(
            "/api/v1/public/verify",
            json=otp_payload,
            name="2. Verify OTP (SIGNUP)",
            catch_response=True
        ) as response:
            print(f"OTP Verification Response: {response.text}")
            
            if response.status_code in (200, 201):
                if response.cookies:
                    self.session_cookies.update(response.cookies)
                try:
                    response_data = response.json()
                    if response_data.get('success'):
                        self.auth_token = response_data.get('data', {}).get('token')
                        # Save email to CSV only if OTP verification is successful
                        self.save_email_to_csv(self.email)
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"OTP verification failed: {response.text}")
        
        # Step 3: Get user profile using cookies from verify step
        if self.session_cookies:  # Check if we have cookies
            with self.client.get(
                "/api/v1/user/me",
                cookies=self.session_cookies,
                name="3. Get User Profile (After SIGNUP)",
                catch_response=True
            ) as response:
                print(f"Get User Profile Response: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile fetch failed: {response.text}")