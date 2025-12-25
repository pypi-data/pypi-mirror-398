from typing import Optional
from uuid import uuid4

import faiss
from langchain_community.docstore import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel


class VectorStoreConfig(BaseModel):
    model: str
    index_dir: Optional[str] = None
    index_name: Optional[str] = None
    top_k: Optional[int] = 3


class SearchResult(BaseModel):
    similarity_score: float
    relevance_score: Optional[float] = 0
    doc: dict


class VectorStoreNode:
    def __init__(self, store_config: VectorStoreConfig):
        self.store_config = store_config
        self.vector_store = None
        self.embedding_model = HuggingFaceEmbeddings(model_name=self.store_config.model,
                                                     model_kwargs={'device': 'cpu'})

    def store(self):
        return self.vector_store

    def load_index(self):
        self.vector_store = FAISS.load_local(folder_path=self.store_config.index_dir,
                                             index_name=self.store_config.index_name,
                                             embeddings=self.embedding_model,
                                             allow_dangerous_deserialization=True,
                                             normalize_L2=True)

    def build_index(self, documents: list[Document]):
        self.vector_store = FAISS(
            embedding_function=self.embedding_model,
            index=faiss.IndexFlatIP(len(self.embedding_model.embed_query("AI"))),
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
            normalize_L2=True
        )

        self.vector_store.add_documents(documents=documents,
                                        ids=[str(uuid4()) for _ in range(len(documents))])
        if self.store_config.index_name is not None and self.store_config.index_dir is not None:
            self.vector_store.save_local(folder_path=self.store_config.index_dir,
                                         index_name=self.store_config.index_name)

    def search(self, query: str, threshold=0.8, filter_meta={}) -> list[SearchResult]:
        results = self.vector_store.similarity_search_with_score(query=query, k=self.store_config.top_k,
                                                                 filter=filter_meta)
        return [SearchResult(similarity_score=score, doc=doc.model_dump())
                for doc, score in results if score > threshold]
