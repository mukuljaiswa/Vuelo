from utils import CredentialManager
from sierra_tasks import Tasks
from locust import between


class SierraDimensionsTasks:
    def __init__(self, parent):
        self.user = parent
        self.wait_time = between(1, 3)  # Random wait between 1-3 seconds

    # ------------------------------
    # Registration Flow
    # ------------------------------
    def test_user_registration_flow(self):
        print(f"\n[Worker {self.user.environment.runner.worker_index}] User {self.user.user_id} starting signup flow")

        # Signup user 
        signupsuccess, user_data =Tasks.signup(self.user)
        self.user.wait()  # Add random delay


        if not signupsuccess:
            print(f"User {self.user.user_id} signup failed, skipping further steps")
            return
        
        # Verify OTP after signup
        otp_success=Tasks.verify_otp(self.user,user_data["email"],"SIGNUP")
        self.user.wait()  # Add random delay
    
        #save_credential 
        if otp_success:
            CredentialManager.save_credentials(user_data["email"], self.user.password, self.user.user_id)
        else:
            print(f"User {self.user.user_id} OTP Verifiaction Failed, skipping further steps")
            return  
        
        # Get user profile after signup
        Tasks.get_user_profile(self.user)
    

    # ------------------------------
    # Login Flow
    # ------------------------------
    def test_user_login_flow(self):
        print(f"\n[Worker {self.user.environment.runner.worker_index}] User {self.user.user_id} starting login flow")

        # Login user
        loginsuccess, email = Tasks.login(self.user)
        self.user.wait()  # Add random delay

        if not loginsuccess:
            print(f"[Worker {self.user.environment.runner.worker_index}] User {self.user.user_id}: Login failed")
            return

        # Verify OTP after login
        otp_success = Tasks.verify_otp(self.user, email, "LOGIN")
        self.user.wait()  # Add random delay
        if not otp_success:
            print(f"[Worker {self.user.environment.runner.worker_index}] User {self.user.user_id}: OTP verification failed")
            return

        # Get User Profile
        Tasks.get_user_profile(self.user)
        self.user.wait()  # Add random delay


        # User Add Nominee List After Login.......................
        Tasks.add_nominee(self.user)
        self.user.wait()  # Add random delay

        # User Nominee List After Login..................
        nominee_id=Tasks.get_nominee_list(self.user)
        print(f"User {self.user.user_id} Nominee ID: {nominee_id}") 
        self.user.wait()  # Add random delay

        #Update User Nominee List After Login..................
        Tasks.update_nominee(self.user,nominee_id)
        self.user.wait()  # Add random delay

        # Delete User Nominee List After Login..................
        Tasks.delete_nominee(self.user,nominee_id)
        self.user.wait()  # Add random delay

        # #Get Profile Details After Login..................
        Tasks.get_profile_details(self.user)
        self.user.wait()  # Add random delay

        #Get profile avatars
        Tasks.get_avatars(self.user)
        self.user.wait()  # Add random delay

        #Upload profile-picture  (Avatar)
        Tasks.upload_avatar(self.user)
        self.user.wait()  # Add random delay

        #Upload profile-picture
        Tasks.upload_profile_picture(self.user)
        self.user.wait()  # Add random delay

        #Delete profile-picture
        Tasks.delete_profile_picture(self.user)



