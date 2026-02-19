# rag.py
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

import torch
import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ────────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
UPLOAD_FOLDER        = "documents"
CHROMA_PERSIST_DIR   = "chroma_db"
COLLECTION_NAME      = "pdf_rag_collection"
CHUNKS_JSONL_PATH    = "processed_chunks.jsonl"

os.makedirs(UPLOAD_FOLDER,      exist_ok=True)
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)


class RAGPipeline:
    def __init__(self):
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.vectorstore: Optional[Chroma] = None

    def _lazy_load_embeddings(self) -> HuggingFaceEmbeddings:
        if self.embeddings is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading embedding model: {EMBEDDING_MODEL_NAME} on device: {device}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={
                    "device": device,
                    "trust_remote_code": False,
                },
                encode_kwargs={
                    "normalize_embeddings": True,
                    "batch_size": 32,
                },
                cache_folder=os.path.expanduser("~/.cache/huggingface/hub"),
            )
        return self.embeddings

    def _lazy_load_vectorstore(self) -> Chroma:
        if self.vectorstore is not None:
            return self.vectorstore

        self._lazy_load_embeddings()

        # Recommended stable way in recent langchain-chroma versions
        self.vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )

        count = self.vectorstore._collection.count()
        print(f"Vector store loaded – collection: {COLLECTION_NAME}")
        print(f"→ Current document count in collection: {count}")

        return self.vectorstore

    def _append_chunks_to_jsonl(
        self,
        texts: List[str],
        sources: List[str],
        chunk_indices: List[int]
    ):
        if len(texts) != len(sources) or len(texts) != len(chunk_indices):
            raise ValueError("Length mismatch between texts/sources/indices")

        with open(CHUNKS_JSONL_PATH, "a", encoding="utf-8") as f:
            for text, source, idx in zip(texts, sources, chunk_indices):
                entry = {
                    "text": text.strip(),
                    "source": source,
                    "chunk_index_in_file": idx,
                    "timestamp": datetime.utcnow().isoformat(),
                    "length": len(text),
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"→ Appended {len(texts)} chunks to {CHUNKS_JSONL_PATH}")

    def build_or_update_index(self) -> int:
        """
        Process all PDFs in UPLOAD_FOLDER → chunk → embed → store
        Returns number of new chunks added this run
        """
        self._lazy_load_vectorstore()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=140,
            length_function=len,
        )

        total_new_chunks = 0
        new_chunk_texts   = []
        new_chunk_sources = []
        new_chunk_indices = []

        pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".pdf")]
        print(f"Found {len(pdf_files)} PDF files to process")

        for filename in pdf_files:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            print(f"  Processing: {filename}")

            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                chunks = splitter.split_documents(docs)

                chunk_texts = [c.page_content.strip() for c in chunks if c.page_content.strip()]
                if not chunk_texts:
                    print(f"    → no valid content")
                    continue

                chunk_indices_in_file = list(range(len(chunk_texts)))

                new_chunk_texts.extend(chunk_texts)
                new_chunk_sources.extend([filename] * len(chunk_texts))
                new_chunk_indices.extend(chunk_indices_in_file)

                print(f"    → {len(chunk_texts)} chunks extracted")

            except Exception as e:
                print(f"    Error processing {filename}: {e}")
                continue

        if not new_chunk_texts:
            print("No new chunks to add.")
            return 0

        # Log chunks
        self._append_chunks_to_jsonl(new_chunk_texts, new_chunk_sources, new_chunk_indices)

        # Add to Chroma
        ids = [f"{src}_{i}" for i, src in enumerate(new_chunk_sources)]
        metadatas = [{"source": src} for src in new_chunk_sources]

        print(f"Adding {len(new_chunk_texts)} chunks to Chroma collection '{COLLECTION_NAME}' ...")
        self.vectorstore.add_texts(
            texts=new_chunk_texts,
            metadatas=metadatas,
            ids=ids,
        )
        print("→ add_texts completed")

        # Very important verification
        count_after = self.vectorstore._collection.count()
        print(f"→ Items in collection AFTER add: {count_after}")

        total_new_chunks = len(new_chunk_texts)
        print(f"Index update complete. Added {total_new_chunks} chunks this run.")
        return total_new_chunks

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, any]]:
        self._lazy_load_vectorstore()

        if not query.strip():
            return []

        print(f"Retrieving for query: {query!r}  (k={k})")

        results = self.vectorstore.similarity_search_with_score(query, k=k)

        print(f"→ Found {len(results)} results")

        formatted = []
        for doc, score in results:
            formatted.append({
                "content": doc.page_content,
                "score": round(float(score), 4),   # lower = better (cosine distance)
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "unknown")
            })
            print(f"   score={score:.4f} | {doc.metadata.get('source','?')} | {doc.page_content[:70]}...")

        return formatted

    def is_ready(self) -> bool:
        try:
            vs = self._lazy_load_vectorstore()
            return vs is not None
        except Exception as e:
            print(f"is_ready failed: {e}")
            return False

    def get_chunks_log_path(self) -> str:
        return CHUNKS_JSONL_PATH


# Quick test when running file directly
if __name__ == "__main__":
    rag = RAGPipeline()
    added = rag.build_or_update_index()
    print(f"\nTotal chunks added this run: {added}")

    if added > 0:
        test_query = input("\nEnter test query (or press Enter to skip): ").strip()
        if test_query:
            results = rag.retrieve(test_query, k=5)
            print("\nTest retrieval results:")
            for r in results:
                print(f"  {r['score']:.4f}  {r['source']}  →  {r['content'][:80]}...")