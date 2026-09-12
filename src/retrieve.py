import os
from pathlib import Path
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from chunker import load_and_chunk
from schemas import Chunk, RetrievedChunk
load_dotenv()
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/os.getenv("CHROMA_DIR","data/processed/chroma")
COL=os.getenv("CHROMA_COLLECTION","policy_chunks")
MODEL=os.getenv("EMBEDDING_MODEL","all-MiniLM-L6-v2")
class Retriever:
    def __init__(self):
        self.client=chromadb.PersistentClient(path=str(DB)); self.model=SentenceTransformer(MODEL)
        self.collection=self.client.get_or_create_collection(COL,metadata={"hnsw:space":"cosine"})
    def rebuild(self):
        try: self.client.delete_collection(COL)
        except Exception: pass
        self.collection=self.client.get_or_create_collection(COL,metadata={"hnsw:space":"cosine"})
        chunks=load_and_chunk(); emb=self.model.encode([c.text for c in chunks],normalize_embeddings=True).tolist()
        self.collection.add(ids=[c.chunk_id for c in chunks],embeddings=emb,documents=[c.text for c in chunks],metadatas=[{"source_file":c.source_file,"location":c.location} for c in chunks])
        return len(chunks)
    def search(self,q,top_k=8):
        if self.collection.count()==0: raise RuntimeError("ChromaDB is empty. Run: python scripts/build_index.py")
        e=self.model.encode([q],normalize_embeddings=True).tolist()
        r=self.collection.query(query_embeddings=e,n_results=top_k,include=["documents","metadatas","distances"])
        out=[]
        for i,cid in enumerate(r["ids"][0]):
            meta=r["metadatas"][0][i]; out.append(RetrievedChunk(Chunk(cid,meta["source_file"],meta["location"],r["documents"][0][i]),float(r["distances"][0][i])))
        return out
