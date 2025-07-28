# tasks.py
from utils import CredentialManager
from sierra_tasks import Tasks
import json

class SierraDimensionsTasks:
    def __init__(self, parent):
        self.user = parent

    # ------------------------------
    # Registration Flow
    # ------------------------------
    def test_user_registration_flow(self):
        print(f"\nUser {self.user.user_id} starting registration flow")

        # Signup user 
        signupsuccess, user_data =Tasks.signup(self)

        if not signupsuccess:
            print(f"User {self.user.user_id} signup failed, skipping further steps")
            return
        

        # Verify OTP after signup
        otp_success=Tasks.verify_otp(self,user_data["email"],"SIGNUP")
    
        #save_credential 
        if otp_success:
            CredentialManager.save_credentials(user_data["email"], self.user.password, self.user.user_id)
        else:
            print(f"User {self.user.user_id} OTP Verifiaction Failed, skipping further steps")
            return  
        
        # Get user profile after signup
        Tasks.get_user_profile(self)
        
    # ------------------------------
    # Login Flow
    # ------------------------------
    def test_user_login_flow(self):
        print(f"\nUser {self.user.user_id} starting login flow")

        #Login user
        loginsuccess,email=Tasks.login(self)

        if not loginsuccess: 
            print("Login failed")
            return
        
        #Verify OTP after login
        otp_success=Tasks.verify_otp(self, email ,"LOGIN")

        if not otp_success:
            print("OTP verification failed:")
            return

        #Get User Profile
        Tasks.get_user_profile(self)    

         # User Add Nominee List After Login.......................
        Tasks.add_nominee(self)

        # User Nominee List After Login..................
        nominee_id=Tasks.get_nominee_list(self)
        print(f"User {self.user.user_id} Nominee ID: {nominee_id}") 

        #Update User Nominee List After Login..................
        Tasks.update_nominee(self,nominee_id)


        # Delete User Nominee List After Login..................
        Tasks.delete_nominee(self,nominee_id)

        # #Get Profile Details After Login..................
        Tasks.get_profile_details(self)

        #Get profile avatars
        Tasks.get_avatars(self)

        #Upload profile-picture  (Avatar)
        Tasks.upload_avatar(self)

        #Upload profile-picture
        Tasks.upload_profile_picture(self)

        #Delete profile-picture
        Tasks.delete_profile_picture(self)















        


        




   
