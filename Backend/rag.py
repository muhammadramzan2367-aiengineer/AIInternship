# rag.py
import os
import json
from datetime import datetime
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
UPLOAD_FOLDER = "documents"
CHROMA_PERSIST_DIR = "chroma_db"
CHUNKS_JSONL_PATH = "processed_chunks.jsonl"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)


class RAGPipeline:
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None

    def _lazy_load_embeddings(self):
        if self.embeddings is None:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={
                    "device": "cpu",                    # change to "cuda" if you have GPU
                    "trust_remote_code": False,
                },
                encode_kwargs={
                    "normalize_embeddings": True,
                    "batch_size": 32,
                },
                # Helps prevent some serialization issues
                cache_folder=os.path.expanduser("~/.cache/huggingface/hub"),
            )
        return self.embeddings

    def _lazy_load_vectorstore(self):
        if self.vectorstore is not None:
            return self.vectorstore

        db_path = os.path.join(CHROMA_PERSIST_DIR, "chroma.sqlite3")
        if os.path.exists(db_path):
            self.vectorstore = Chroma(
                persist_directory=CHROMA_PERSIST_DIR,
                embedding_function=self._lazy_load_embeddings()
            )
        return self.vectorstore

    def _save_chunks_to_jsonl(self, chunks: List[str], sources: List[str]):
        """Append chunks with metadata to JSONL file"""
        with open(CHUNKS_JSONL_PATH, "a", encoding="utf-8") as f:
            for i, text in enumerate(chunks):
                entry = {
                    "text": text.strip(),
                    "chunk_index": i,
                    "source_file": sources[i] if i < len(sources) else None,
                    "timestamp": datetime.now().isoformat(),
                    "length": len(text)
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def build_or_update_index(self) -> int:
        """Chunk PDFs → save to JSONL → embed → update Chroma"""
        self._lazy_load_embeddings()

        all_chunks_text = []
        all_sources = []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=120,
            length_function=len,
            add_start_index=True,
        )

        for filename in os.listdir(UPLOAD_FOLDER):
            if not filename.lower().endswith(".pdf"):
                continue

            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                chunks = splitter.split_documents(docs)

                chunk_texts = [c.page_content for c in chunks]
                all_chunks_text.extend(chunk_texts)
                all_sources.extend([filename] * len(chunk_texts))

            except Exception as e:
                print(f"Error processing {filename}: {e}")

        if not all_chunks_text:
            return 0

        # Save chunks to JSONL
        self._save_chunks_to_jsonl(all_chunks_text, all_sources)

        # Create / update Chroma collection
        self.vectorstore = Chroma.from_texts(
            texts=all_chunks_text,
            embedding=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
            collection_name="pdf_rag_collection"
        )

        # In newer Chroma versions this is often not necessary after from_texts/from_documents
        # self.vectorstore.persist()

        return len(all_chunks_text)

    def retrieve(self, query: str, k: int = 4) -> List[str]:
        self._lazy_load_vectorstore()
        if self.vectorstore is None:
            raise RuntimeError("No vector index available. Run build_or_update_index() first.")

        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def is_ready(self) -> bool:
        self._lazy_load_vectorstore()
        return self.vectorstore is not None

    def get_chunk_file_path(self) -> str:
        return CHUNKS_JSONL_PATH