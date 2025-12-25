import requests
from pydantic import BaseModel
from ragflow_sdk import RAGFlow


class RAGFlowServerConfig(BaseModel):
    base_url: str
    api_key: str


class RAGFlowClientNode:
    def __init__(self, server_config: RAGFlowServerConfig):
        self.server_config = server_config
        self.ragflow_client = RAGFlow(
            base_url=server_config.base_url,
            api_key=server_config.api_key
        )
        self.auth_header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {server_config.api_key}"
        }

    def client(self):
        return self.ragflow_client

    def list_datasets(self, page=1, page_size=1000, id=None):
        return self.ragflow_client.list_datasets(page=page, page_size=page_size, id=id)

    def get_document_chunks(self, dataset_id: str, document_id: str, page=1, page_size=1000):
        return requests.get(self.server_config.base_url +
                            f"/datasets/{dataset_id}/documents/{document_id}/chunks?page={page}&page_size={page_size}",
                            headers=self.auth_header).json()

    def get_documents(self, dataset_id: str, document_id: str = None, page=1, page_size=1000):
        return requests.get(self.server_config.base_url +
                            f"/datasets/{dataset_id}/documents?page={page}&page_size={page_size}" + (
                                "" if document_id is None else f"&id={document_id}"),
                            headers=self.auth_header).json()

    def get_document_content(self, dataset_id: str, document_id: str):
        return requests.get(self.server_config.base_url +
                            f"/datasets/{dataset_id}/documents/{document_id}",
                            headers=self.auth_header).content

    def retrieve(self, question: str, dataset_ids: list[str], top_k=1):
        return [c.to_json() for c in self.ragflow_client.retrieve(
            question=question,
            dataset_ids=dataset_ids,
            top_k=top_k)]
