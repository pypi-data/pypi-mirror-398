from pydantic import BaseModel
from sqlalchemy import create_engine


class DatabaseServerConfig(BaseModel):
    url: str


class DatabaseClientNode:
    def __init__(self, server_config: DatabaseServerConfig):
        self.database_engine = create_engine(server_config.url, pool_size=10)

    def engine(self):
        return self.database_engine
