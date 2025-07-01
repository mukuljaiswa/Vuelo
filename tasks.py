from utils import CredentialManager, UserUtils
import json

class SierraDimensionsTasks:
    def __init__(self, parent):
        self.user = parent

    def test_user_registration_flow(self):
        print(f"\nUser {self.user.user_id} starting registration flow")
        self.user.password = UserUtils.generate_strong_password(self.user.user_id)
        user_data = {
            "first_name": UserUtils.generate_random_name(self.user.user_id),
            "last_name": UserUtils.generate_random_name(self.user.user_id),
            "email": UserUtils.generate_dynamic_email(self.user.user_id),
            "date_of_birth": "2001-08-15",
            "password": self.user.password,
            "confirm_password": self.user.password,
            "terms_accepted": True
        }
        signup_success = False
        otp_success = False

        with self.user.client.post(
            "/api/v1/public/signup",
            json=user_data,
            name="1. User Signup",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                print(f"User {self.user.user_id} Signup Response: {response.text}")
                signup_success = True
            else:
                response.failure(f"Signup failed: {response.text}")

        if not signup_success:
            return

        otp_data = {
            "contact": user_data["email"],
            "otp": "000000",
            "verify_type": "SIGNUP"
        }

        with self.user.client.post(
            "/api/v1/public/verify",
            json=otp_data,
            name="2. Verify OTP (SIGNUP)",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201):
                print(f"User {self.user.user_id} OTP Verification Response: {response.text}")
                otp_success = True
                if response.cookies:
                    self.user.session_cookies.update(response.cookies)
                try:
                    response_data = response.json()
                    if response_data.get('success'):
                        CredentialManager.save_credentials(user_data["email"], self.user.password, self.user.user_id)
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"OTP verification failed: {response.text}")

        if not otp_success:
            return

        if self.user.session_cookies:
            print(f"User {self.user.user_id} attempting to get user profile")
            with self.user.client.get(
                "/api/v1/user/me",
                cookies=self.user.session_cookies,
                name="3. Get User Profile",
                catch_response=True
            ) as response:
                print(f"User {self.user.user_id} Profile Response: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile fetch failed: {response.text}")

    def test_user_login_flow(self):
        print(f"\nUser {self.user.user_id} starting login flow")
        email, password = CredentialManager.get_next_credentials()
        if not email or not password:
            print(f"User {self.user.user_id}: No valid credentials available for login")
            return

        print(f"User {self.user.user_id} attempting login with email: {email}")
        login_success = False
        otp_success = False

        with self.user.client.post(
            "/api/v1/public/login",
            json={"contact": email, "password": password},
            name="1. User Login",
            catch_response=True
        ) as response:
            print(f"User {self.user.user_id} Login Response: {response.text}")
            if response.status_code == 201:
                login_success = True
            else:
                response.failure(f"Login failed: {response.text}")

        if not login_success:
            return

        otp_data = {
            "contact": email,
            "otp": "000000",
            "verify_type": "LOGIN"
        }

        with self.user.client.post(
            "/api/v1/public/verify",
            json=otp_data,
            name="2. Verify OTP (LOGIN)",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201):
                print(f"User {self.user.user_id} Login OTP Verification Response: {response.text}")
                otp_success = True
                if response.cookies:
                    self.user.session_cookies.update(response.cookies)
            else:
                response.failure(f"Login OTP verification failed: {response.text}")

        if not otp_success:
            return

        if self.user.session_cookies:
            print(f"User {self.user.user_id} attempting to get user profile after login")
            with self.user.client.get(
                "/api/v1/user/me",
                cookies=self.user.session_cookies,
                name="3. Get User Profile After Login",
                catch_response=True
            ) as response:
                print(f"User {self.user.user_id} Post-Login Profile Response: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile fetch failed: {response.text}")
