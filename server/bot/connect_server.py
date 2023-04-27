import requests
import os


class UsersService:
    limit = 5
    base_url = f"http://{os.environ['WEB_APP_HOST']}:8000/api/"
    # base_url = f"http://127.0.0.1:8000/api/"

    def check_connect(self):
        response = requests.get(f"{self.base_url}ping/")
        print('status 200')
        response.raise_for_status()

    def get_users(self, query_params):
        response = requests.get(f"{self.base_url}users/", query_params)
        response.raise_for_status()
        return response.json()

    def patch_user(self, user_data, user_id):
        response = requests.patch(f"{self.base_url}user/{user_id}/", json=user_data)
        response.raise_for_status()
        return response.json()

    def post_user(self, user_data):
        response = requests.post(f"{self.base_url}users/", json=user_data)
        response.raise_for_status()
        return response.json()


users_service = UsersService()