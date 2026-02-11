import os
import faiss
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
UPLOAD_FOLDER = "documents"

class RAGPipeline:
    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.index = None
        self.documents = []

 
    def load_documents(self):
        all_chunks = []

        for file in os.listdir(UPLOAD_FOLDER):
            if file.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(UPLOAD_FOLDER, file))
                docs = loader.load()

                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=100
                )

                chunks = splitter.split_documents(docs)

                for chunk in chunks:
                    all_chunks.append(chunk.page_content)

        self.documents = all_chunks
        return all_chunks


    def build_index(self):
        if not self.documents:
            self.load_documents()

        embeddings = self.embedding_model.encode(self.documents)
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings))


    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding), top_k
        )

        results = [self.documents[i] for i in indices[0]]
        return results