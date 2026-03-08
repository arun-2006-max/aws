"""ChromaDB vector store service for RAG document retrieval."""
import os
import uuid

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class ChromaService:
    def __init__(self):
        self.collection = None
        if CHROMA_AVAILABLE:
            try:
                client = chromadb.PersistentClient(path="data/chroma")
                self.collection = client.get_or_create_collection(
                    name="knowledge_base",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                print(f"ChromaDB init failed (non-fatal): {e}")

    def add_document(self, content: str, source: str = "", metadata: dict = None):
        """Index a document chunk into ChromaDB."""
        if not self.collection:
            return
        doc_id = str(uuid.uuid4())
        self.collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[{**(metadata or {}), "source": source}],
        )

    def search(self, query: str, n_results: int = 3) -> list[dict]:
        """Semantic search over indexed documents."""
        if not self.collection or self.collection.count() == 0:
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count()),
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            return [
                {
                    "content": doc,
                    "source": meta.get("source", ""),
                    "score": round(1 - dist, 4),
                }
                for doc, meta, dist in zip(docs, metas, dists)
            ]
        except Exception as e:
            print(f"ChromaDB search error (non-fatal): {e}")
            return []

    def add_text_file(self, filepath: str, chunk_size: int = 500):
        """Index a plain text file into ChromaDB in chunks."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        words = text.split()
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        for chunk in chunks:
            if chunk.strip():
                self.add_document(chunk, source=os.path.basename(filepath))
        print(f"Indexed {len(chunks)} chunks from {filepath}")
