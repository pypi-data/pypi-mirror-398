from typing import Optional, List

import requests
from pydantic import BaseModel


class XinferenceServerConfig(BaseModel):
    base_url: str
    api_key: str
    mode: Optional[str] = "http"
    rerank_model: Optional[str] = "bge-reranker-v2-m3"
    embed_model: Optional[str] = "bge-m3"


class XinferenceClientNode:
    def __init__(self, server_config: XinferenceServerConfig):
        self.server_config = server_config
        # if server_config.mode == "client":
        #     self.client = RESTfulClient(server_config.base_url)
        #     self.rerank_model: RESTfulRerankModelHandle = self.client.get_model("bge-reranker-v2-m3")
        #     self.embed_model: RESTfulEmbeddingModelHandle = self.client.get_model("bge-m3")

    def client(self):
        if self.server_config.mode == "http":
            return None
        # else:
        #     return self.client

    def rerank(self, documents: List[str], query: str, top_n=3):
        if self.server_config.mode == "http":
            return requests.post(self.server_config.base_url + "/v1/rerank",
                                 json={
                                     "model": self.server_config.rerank_model,
                                     "query": query,
                                     "documents": documents,
                                     "top_n": top_n
                                 }).json()["results"]
        # else:
        #     return self.rerank_model.rerank(documents=documents, query=query, top_n=top_n)["results"]

    def embed(self, input: str):
        if self.server_config.mode == "client":
            return requests.post(self.server_config.base_url + "/v1/embeddings",
                                 json={
                                     "model": self.server_config.embed_model,
                                     "input": input,
                                     "encoding_format": "float"
                                 }).json()
        # else:
        #     return self.embed_model.create_embedding(input)
