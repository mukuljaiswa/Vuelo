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
            name="1. Signup API",
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
            name="2. Verify OTP (After Signup) API",
            catch_response=True
        ) as response:
            if response.status_code ==201:
                print(f"User {self.user.user_id} OTP Verification Response: {response.text}")
                otp_success = True
                if response.cookies:
                    self.user.session_cookies.update(response.cookies)
                try:
                    CredentialManager.save_credentials(user_data["email"], self.user.password, self.user.user_id)
                    print(f"User {self.user.user_id} successfully registered and logged in")

                    # response_data = response.json()
                    # print('Response Data:', response_data)
                    # if response_data.get('Authentication successful'):
                    #     print(f"User {self.user.user_id} successfully registered and logged in")
                    #     CredentialManager.save_credentials(user_data["email"], self.user.password, self.user.user_id)
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
                name="3. Get User Profile (After Signup) API",
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
            name="1. Login API",
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
            name="2. Verify OTP (After Login)  API",
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
            
        #Session Creation.........................

        if self.user.session_cookies:
            print(f"User {self.user.user_id} attempting to get user profile after login")

            # Get User Profile After Login..................
            with self.user.client.get(
                "/api/v1/user/me",
                cookies=self.user.session_cookies,
                name="3. Get User Profile (After Login) API",
                catch_response=True
            ) as response:
                print(f"User {self.user.user_id} Post-Login Profile Response: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile fetch failed: {response.text}")

            # User Add Nominee List After Login.......................

            nominee_data = {    
                "first_name": UserUtils.generate_random_name(self.user.user_id),
                "last_name": UserUtils.generate_random_name(self.user.user_id),
                "email": UserUtils.generate_dynamic_email(self.user.user_id),
                "phone":UserUtils.generate_random_phone_number(),
                "date_of_birth": "2000-01-01",
                "relationship": "other",
            }
            print(f"User {self.user.user_id} attempting to add nominee: {nominee_data}") 
        
            with self.user.client.post(
                "/api/v1/user/profile/nominee",
                json=nominee_data,
                name="2. Verify Add Nominee (After Login)  API",
                catch_response=True
            ) as response:


                if response.status_code == 201:
                    print(f"User {self.user.user_id} Nominee Add Response: {response.text}")
                    if response.cookies:
                        self.user.session_cookies.update(response.cookies)
                else:
                    response.failure(f"Add Nominee Failed {response.text}")

            
            # User Nominee List After Login..................
          # User Nominee List After Login..................
            with self.user.client.get(
                "/api/v1/user/profile/nominee/list",
                cookies=self.user.session_cookies,
                name="3. User NomineeList (After Login) API",
                catch_response=True
            ) as response:
                print(f"User {self.user.user_id} Post-Login NomineeList : {response.text}")
                if response.status_code != 200:
                    response.failure(f"NomineeList fetch failed: {response.text}")
                else:
                    try:
                        nominee_data = response.json().get("data", [])
                        self.user.nominee_id = nominee_data[0]["id"] if nominee_data else None
                        print(f"Stored Nominee ID for user {self.user.user_id}: {self.user.nominee_id}")
                    except Exception as e:
                        response.failure(f"Error parsing nominee list response: {str(e)}")
                        self.user.nominee_id = None

            #Update User Nominee List After Login..................

            update_nominee_data = {
                "id": self.user.nominee_id,  # Assuming you want to update the first nominee
                "first_name": "updated"+UserUtils.generate_random_name(self.user.user_id),
                "last_name": "updated"+UserUtils.generate_random_name(self.user.user_id),
                "email": "updated_"+UserUtils.generate_dynamic_email(self.user.user_id),
                "phone": UserUtils.generate_random_phone_number(),
                "date_of_birth": "2000-01-01",
                "relationship": "mother",
            }

            print(f"User {self.user.user_id} attempting to update nominee: {update_nominee_data}")

            with self.user.client.put(
                "/api/v1/user/profile/nominee",
                json=update_nominee_data,
                name="2. Update Nominee (After Login)  API",
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    print(f"User {self.user.user_id} Nominee Update Response: {response.text}")
                    if response.cookies:
                        self.user.session_cookies.update(response.cookies)
                else:
                    response.failure(f"Update Nominee Failed {response.text}")
            

            # Delete User Nominee List After Login..................
            if self.user.nominee_id:

                delete_data = {
                                    "id": self.user.nominee_id
                }
                                
                print(f"User {self.user.user_id} attempting to delete nominee with ID: {self.user.nominee_id}")
                with self.user.client.delete(
                    f"/api/v1/user/profile/nominee",
                    json=delete_data,
                    name="3. Delete Nominee (After Login) API",
                    catch_response=True
                ) as response:
                    if response.status_code == 200:
                        print(f"User {self.user.user_id} Nominee Delete Response: {response.text}")
                    else:
                        response.failure(f"Delete Nominee Failed: {response.text}")

            #Get Profile Details After Login..................
            with self.user.client.get(
                "/api/v1/user/profile/details",
               # cookies=self.user.session_cookies,
                name="4. Get User Profile Details(After Login) API",
                catch_response=True
            ) as response:
                print(f"User {self.user.user_id} Post-Login Profile Details: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile fetch failed: {response.text}")
            
            #User Profile Update Section After Login..................
            #Get profile avatars
            with self.user.client.get(
                "/api/v1/user/profile/avatars",
                #cookies=self.user.session_cookies,
                name="5. Get User Profile Avatars (After Login) API",
                catch_response=True
            ) as response:
                print(f"User {self.user.user_id} Post-Login Profile Avatars: {response.text}")
                if response.status_code != 200:
                    response.failure(f"Profile avatars fetch failed: {response.text}") 

            #Upload profile-picture 
            with open('/data/Vuelo/profile-image/varanasi.jpg', 'rb') as profile_picture:
                files = {'image': profile_picture}
                with self.user.client.post(
                    "/api/v1/user/profile/profile-picture/upload",
                    files=files,
                    #cookies=self.user.session_cookies,
                    name="6. Upload Profile Picture (After Login) API",
                    catch_response=True
                ) as response:
                    if response.status_code == 201:
                        print(f"User {self.user.user_id} Profile Picture Upload Response: {response.text}")
                    else:
                        response.failure(f"Profile picture upload failed: {response.text}")


