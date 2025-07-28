# sierra_tasks.py

from utils import CredentialManager,CredentialManagerUserUtils
import json

class Tasks:
    def __init__(self, parent):
        self.user = parent

    def signup(self):
        print(f"\nUser {self.user.user_id} starting registration flow")
        self.user.password = CredentialManagerUserUtils.generate_strong_password()
        print(f"Generated password for user {self.user.user_id}: {self.user.password}")
        user_data = {
            "first_name": CredentialManagerUserUtils.generate_random_name(),
            "last_name": CredentialManagerUserUtils.generate_random_name(),
            "email": CredentialManagerUserUtils.generate_dynamic_email(),
            "date_of_birth": "2001-08-15",
            "password": self.user.password,
            "confirm_password": self.user.password,
            "terms_accepted": True
        }

        with self.user.client.post(
            "/api/v1/public/signup",
            json=user_data,
            name="1. Signup API",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                print(f"User {self.user.user_id} Signup Response: {response.text}")
                return True, user_data
            else:
                response.failure(f"Signup failed: {response.text}")
                return False, None

    def verify_otp(self, contact, verify_type):
        otp_data = {
            "contact": contact,
            "otp": "000000",
            "verify_type": verify_type
        }

        with self.user.client.post(
            "/api/v1/public/verify",
            json=otp_data,
            name=f"2. Verify OTP ({verify_type}) API",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201):
                print(f"User {self.user.user_id} OTP Verification Response: {response.text}")
                return True
            else:
                response.failure(f"OTP verification failed: {response.text}")
                return False

    def get_user_profile(self):
        with self.user.client.get(
            "/api/v1/user/me",
            name="3. Get User Profile API",
            catch_response=True
        ) as response:
            print(f"User {self.user.user_id} Profile Response: {response.text}")
            if response.status_code != 200:
                response.failure(f"Profile fetch failed: {response.text}")

    def login(self):
        email, password = CredentialManager.get_next_credentials()
        if not email or not password:
            print(f"User {self.user.user_id}: No valid credentials available")
            return None, None

        with self.user.client.post(
            "/api/v1/public/login",
            json={"contact": email, "password": password},
            name="4. Login API",
            catch_response=True
        ) as response:
            print(f"User {self.user.user_id} Login Response: {response.text}")
            if response.status_code == 201:
                return True, email
            else:
                response.failure(f"Login failed: {response.text}")
                return None, None

    def add_nominee(self):
        nominee_data = {
            "first_name": CredentialManagerUserUtils.generate_random_name(),
            "last_name": CredentialManagerUserUtils.generate_random_name(),
            "email": CredentialManagerUserUtils.generate_dynamic_email(),
            "phone": CredentialManagerUserUtils.generate_random_phone_number(),
            "date_of_birth": "2000-01-01",
            "relationship": "other",
        }
        with self.user.client.post(
            "/api/v1/user/profile/nominee",
            json=nominee_data,
            name="5. Add Nominee API",
            catch_response=True
        ) as response:
            if response.status_code == 201:
                print(f"User {self.user.user_id} Nominee Add Response: {response.text}")
            else:
                response.failure(f"Add Nominee Failed: {response.text}")

    def get_nominee_list(self):
        with self.user.client.get(
            "/api/v1/user/profile/nominee/list",
            name="6. Get Nominee List API",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Nominee list fetch failed: {response.text}")
                return None

            try:
                data = response.json().get("data", [])
                print(f"User {self.user.user_id} Nominee List Response: {data}")
                return data[0]["id"] if data else None
            except Exception as e:
                response.failure(f"Error parsing nominee list: {str(e)}")
                return None

    def update_nominee(self, nominee_id):
        data = {
            "id": nominee_id,
            "first_name": "updated" +CredentialManagerUserUtils.generate_random_name(),
            "last_name": "updated" + CredentialManagerUserUtils.generate_random_name(),
            "email": "updated_" + CredentialManagerUserUtils.generate_dynamic_email(),
            "phone":CredentialManagerUserUtils.generate_random_phone_number(),
            "date_of_birth": "2000-01-01",
            "relationship": "mother",
        }

        with self.user.client.put(
            "/api/v1/user/profile/nominee",
            json=data,
            name="7. Update Nominee API",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"User {self.user.user_id} Nominee Update Response: {response.text}")
            else:
                response.failure(f"Nominee update failed: {response.text}")

    def delete_nominee(self, nominee_id):
        with self.user.client.delete(
            "/api/v1/user/profile/nominee",
            json={"id": nominee_id},
            name="8. Delete Nominee API",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"User {self.user.user_id} Nominee Delete Response: {response.text}")
            else:
                response.failure(f"Nominee delete failed: {response.text}")

    def get_profile_details(self):
        with self.user.client.get(
            "/api/v1/user/profile/details",
            name="9. Get Profile Details API",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Profile details fetch failed: {response.text}")

    def get_avatars(self):
        with self.user.client.get(
            "/api/v1/user/profile/avatars",
            name="10. Get Avatars API",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Avatar list fetch failed: {response.text}")

    def upload_avatar(self):
        with self.user.client.put(
            "/api/v1/user/profile/profile-picture/avatar",
            json={"avatarId": "f82e86ea-e0d7-462e-9704-8d54a847b19c"},
            name="11. Upload Avatar API",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"User {self.user.user_id} Avatar Upload Response: {response.text}")
            else:
                response.failure(f"Avatar upload failed: {response.text}")

    def upload_profile_picture(self):
        with open('/data/Vuelo/profile-image/varanasi.jpg', 'rb') as file:
            files = {'image': ('varanasi.jpg', file, 'image/jpeg')}
            with self.user.client.post(
                "/api/v1/user/profile/profile-picture/upload",
                files=files,
                name="12. Upload Profile Picture API",
                catch_response=True
            ) as response:
                if response.status_code == 201:
                    print(f"User {self.user.user_id} Profile Picture Upload Response: {response.text}")
                else:
                    response.failure(f"Profile picture upload failed: {response.text}")

    def delete_profile_picture(self):
        with self.user.client.delete(
            "/api/v1/user/profile/profile-picture",
            name="13. Delete Profile Picture API",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"User {self.user.user_id} Profile Picture Delete Response: {response.text}")
            else:
                response.failure(f"Profile picture delete failed: {response.text}")
