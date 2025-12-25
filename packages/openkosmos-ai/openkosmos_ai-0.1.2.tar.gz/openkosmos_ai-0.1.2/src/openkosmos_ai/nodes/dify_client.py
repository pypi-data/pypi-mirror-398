import requests
from pydantic import BaseModel


class DifyServerConfig(BaseModel):
    name: str
    url: str
    email: str
    password: str


class DifyClientNode:
    def __init__(self, server_config: DifyServerConfig):
        self.server_config = server_config
        access_token = DifyClientNode.login(server_config)

        self.auth_header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

    def config(self) -> DifyServerConfig:
        return self.server_config

    @staticmethod
    def login(server_config: DifyServerConfig):
        return requests.post(server_config.url + "/console/api/login", json={
            "email": server_config.email,
            "password": server_config.password,
            "language": "zh-Hans",
            "remember_me": "true"
        }).json()["data"]["access_token"]

    def console_api_apps(self, page=1, limit=100):
        return requests.get(self.server_config.url + f"/console/api/apps?page={page}&limit={limit}",
                            headers=self.auth_header).json()

    def console_api_apps_export(self, app_id: str):
        return requests.get(self.server_config.url + f"/console/api/apps/{app_id}/export?include_secret=true",
                            headers=self.auth_header).json()
