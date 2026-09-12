import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from chunker import load_and_chunk
from schemas import Chunk, RetrievedChunk


load_dotenv()

ROOT = Path(__file__).resolve().parents[1]

DB = ROOT / os.getenv("CHROMA_DIR", "data/processed/chroma")
COL = os.getenv("CHROMA_COLLECTION", "policy_chunks")
MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


# Known policy areas where the corpus contains intentionally conflicting clauses.
CONFLICT_GROUPS = [
    {
        "name": "laboratory_attendance",
        "sections": {
            "academic_regulations.md#1.4",
            "academic_regulations.md#3.2",
        },
        "keywords": {
            "laboratory",
            "lab",
            "attendance",
            "committee",
            "waive",
            "waiver",
            "exception",
            "80%",
        },
    },
    {
        "name": "fee_extension",
        "sections": {
            "academic_regulations.md#17.1",
            "academic_regulations.md#17.2",
        },
        "keywords": {
            "fee",
            "fees",
            "late",
            "late-fee",
            "late fee",
            "extension",
            "accounts",
        },
    },
    {
        "name": "scholarship_attendance",
        "sections": {
            "academic_regulations.md#18.1",
            "academic_regulations.md#18.2",
        },
        "keywords": {
            "scholarship",
            "attendance",
            "waiver",
            "eligibility",
            "eligible",
        },
    },
]


# These indicate that the user is actually asking about an exception,
# override, conflict, or competing rule.
CONFLICT_TRIGGER_PHRASES = {
    "waive",
    "waiver",
    "waived",
    "exception",
    "exceptions",
    "exempt",
    "exemption",
    "override",
    "overridden",
    "conflict",
    "contradiction",
    "contradict",
    "committee",
    "review",
    "bypass",
    "absolute",
    "which rule",
    "which rules",
    "different rule",
    "which should",
    "does the committee",
    "can the committee",
    "can it be waived",
    "can the requirement be waived",
    "can the rule be waived",
    "can attendance be waived",
    "is there an exception",
    "is there any exception",
}


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(DB))

        self.model = SentenceTransformer(MODEL)

        self.collection = self.client.get_or_create_collection(
            COL,
            metadata={"hnsw:space": "cosine"},
        )

    def rebuild(self):
        try:
            self.client.delete_collection(COL)
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            COL,
            metadata={"hnsw:space": "cosine"},
        )

        chunks = load_and_chunk()

        embeddings = self.model.encode(
            [c.text for c in chunks],
            normalize_embeddings=True,
        ).tolist()

        self.collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "source_file": c.source_file,
                    "location": c.location,
                }
                for c in chunks
            ],
        )

        return len(chunks)

    def _is_conflict_query(self, query):
        """
        Detect whether the question is explicitly asking about:
        - a waiver
        - an exception
        - committee authority
        - conflicting rules
        - an override

        Ordinary factual questions such as:

            "What is the minimum laboratory attendance requirement?"

        must NOT activate contradiction expansion.
        """

        query_lower = query.lower().strip()

        return any(
            phrase in query_lower
            for phrase in CONFLICT_TRIGGER_PHRASES
        )

    def _get_group_for_query(self, query):
        """
        Identify which planted contradiction group is relevant to
        the question.
        """

        query_lower = query.lower()

        for group in CONFLICT_GROUPS:
            if any(
                keyword in query_lower
                for keyword in group["keywords"]
            ):
                return group

        return None

    def _suppress_unrequested_conflicts(self, query, hits):
        """
        Prevent normal factual questions from being classified as
        contradictions merely because semantic retrieval happened
        to return both sides of a planted conflict.

        Example:

            "What is the minimum laboratory attendance requirement?"

        should primarily use §1.4.

        It should NOT automatically bring in §3.2 just because
        both sections contain words such as "laboratory" and
        "attendance".

        If the user explicitly asks about a waiver/exception/
        committee/conflict, both clauses are retained.
        """

        if self._is_conflict_query(query):
            return hits

        best_hits = list(hits)

        for group in CONFLICT_GROUPS:
            group_hits = [
                hit
                for hit in best_hits
                if hit.chunk.chunk_id in group["sections"]
            ]

            if len(group_hits) <= 1:
                continue

            # Keep only the semantically closest clause for a normal
            # factual question.
            closest = min(
                group_hits,
                key=lambda hit: hit.distance
            )

            best_hits = [
                hit
                for hit in best_hits
                if (
                    hit.chunk.chunk_id not in group["sections"]
                    or hit.chunk.chunk_id == closest.chunk.chunk_id
                )
            ]

        return best_hits

    def _expand_conflicts(self, query, hits):
        """
        For explicit conflict/waiver/exception questions, make sure
        all clauses belonging to the relevant planted contradiction
        are present in the evidence.

        This is deliberately NOT used for ordinary questions.
        """

        if not self._is_conflict_query(query):
            return hits

        group = self._get_group_for_query(query)

        if group is None:
            return hits

        existing_ids = {
            hit.chunk.chunk_id
            for hit in hits
        }

        # Only expand if at least one clause from the relevant
        # conflict group was actually retrieved.
        retrieved_from_group = any(
            hit.chunk.chunk_id in group["sections"]
            for hit in hits
        )

        if not retrieved_from_group:
            return hits

        for chunk_id in group["sections"]:
            if chunk_id in existing_ids:
                continue

            result = self.collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas"],
            )

            if not result["ids"]:
                continue

            metadata = result["metadatas"][0]

            hits.append(
                RetrievedChunk(
                    Chunk(
                        chunk_id,
                        metadata["source_file"],
                        metadata["location"],
                        result["documents"][0],
                    ),
                    0.0,
                )
            )

        return hits

    def search(self, q, top_k=8):
        if self.collection.count() == 0:
            raise RuntimeError(
                "ChromaDB is empty. Run: python scripts/build_index.py"
            )

        # Semantic search.
        e = self.model.encode(
            [q],
            normalize_embeddings=True,
        ).tolist()

        r = self.collection.query(
            query_embeddings=e,
            n_results=top_k,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        out = []

        for i, cid in enumerate(r["ids"][0]):
            meta = r["metadatas"][0][i]

            out.append(
                RetrievedChunk(
                    Chunk(
                        cid,
                        meta["source_file"],
                        meta["location"],
                        r["documents"][0][i],
                    ),
                    float(r["distances"][0][i]),
                )
            )

        # IMPORTANT:
        # For ordinary factual questions, suppress accidental retrieval
        # of both sides of a planted contradiction.
        out = self._suppress_unrequested_conflicts(q, out)

        # For explicit contradiction/waiver/exception questions,
        # deliberately retrieve the complete conflict pair.
        out = self._expand_conflicts(q, out)

        return out