from locust import HttpUser, between, task
from tasks import SierraDimensionsTasks
from utils import CredentialManager, CredentialManager
from dotenv import load_dotenv
import os


# Load variables from .env
load_dotenv()

class SierraDimensionsUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("HOST")  # Get from .env

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = CredentialManager.assign_user_id()
        self.email = None
        self.password = None
        self.session_cookies = {}
        self.auth_token = None
        self.tasks_impl = SierraDimensionsTasks(self)
        CredentialManager.init_csv_files()
        CredentialManager.load_user_credentials()
        print(f"User {self.user_id} initialized - {len(CredentialManager._user_credentials)} credentials available")

    def on_start(self):
        print(f"\n=== User {self.user_id} started ===")

    # @task(1)
    # # def test_user_registration_flow(self):
    # #     self.tasks_impl.test_user_registration_flow()

    @task(1)
    def test_user_login_flow(self):
        self.tasks_impl.test_user_login_flow()