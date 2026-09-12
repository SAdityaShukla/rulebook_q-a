import json
import os

from dotenv import load_dotenv
from groq import Groq

from retrieve import Retriever
from schemas import QAResult


load_dotenv()

MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

MAX_DISTANCE = float(
    os.getenv("MAX_DISTANCE", "0.95")
)


SYSTEM = """
You are Policy Proof, an evidence-grounded university policy reasoner.

Use ONLY the supplied policy evidence.
Never use general university knowledge.

Choose exactly one state:

- answers:
  The supplied evidence directly establishes an answer.

- silent:
  The supplied evidence does not establish the requested fact.
  Related or adjacent rules are not enough.

- contradiction:
  Two or more supplied policy clauses make incompatible claims
  that directly apply to the same situation.

IMPORTANT CONTRADICTION RULES:

1. A contradiction requires incompatible claims about the same
   situation.

2. A general rule and a specific exception are NOT automatically
   contradictions if the evidence clearly establishes that the
   specific provision is an exception or override.

3. If two provisions genuinely conflict and the corpus does not
   explicitly establish which one controls, classify as contradiction.

4. Do NOT invent a hierarchy, priority, exception, or reconciliation.

5. When contradiction exists, explain BOTH positions and explicitly
   state that the supplied corpus does not establish which provision
   controls, unless it explicitly does.

6. Every substantive claim in an "answers" response must be supported
   by cited evidence.

7. For "silent":
   citations MUST be [].

8. For "contradiction":
   cite ALL directly conflicting chunks.

9. Only cite chunk IDs that actually appear in the supplied evidence.

10. Do not treat merely related provisions as contradictory.

Return JSON only with exactly this shape:

{
  "state": "answers|silent|contradiction",
  "answer": "...",
  "citations": ["exact-chunk-id"]
}
"""


class Reasoner:

    def __init__(self):
        key = os.getenv("GROQ_API_KEY")

        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is missing. Put it in .env."
            )

        self.client = Groq(api_key=key)
        self.retriever = Retriever()

    def ask(self, question):

        hits = self.retriever.search(
            question,
            top_k=8,
        )

        hits = [
            hit
            for hit in hits
            if hit.distance <= MAX_DISTANCE
        ]

        evidence = [
            {
                "chunk_id": hit.chunk.chunk_id,
                "location": hit.chunk.location,
                "text": hit.chunk.text,
                "distance": round(hit.distance, 4),
            }
            for hit in hits
        ]

        if not evidence:
            return QAResult(
                question,
                "silent",
                "The supplied policy corpus does not contain enough "
                "evidence to answer this question.",
                [],
                [],
            )

        user_prompt = json.dumps(
            {
                "question": question,
                "evidence": evidence,
            },
            ensure_ascii=False,
        )

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format={
                    "type": "json_object"
                },
                temperature=0,
                max_tokens=800,
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)

        except Exception:
            return QAResult(
                question,
                "silent",
                "The system could not produce a validated policy answer.",
                [],
                evidence,
            )

        state = data.get("state", "silent")

        answer = str(
            data.get("answer", "")
        ).strip()

        citations = data.get(
            "citations",
            [],
        )

        if not isinstance(citations, list):
            citations = []

        valid_ids = {
            evidence_item["chunk_id"]
            for evidence_item in evidence
        }

        citations = [
            citation
            for citation in citations
            if citation in valid_ids
        ]

        if state not in {
            "answers",
            "silent",
            "contradiction",
        }:
            state = "silent"

        # Silent must never contain citations.
        if state == "silent":
            citations = []

            answer = (
                answer
                or
                "The supplied policy corpus does not establish "
                "the requested fact."
            )

        # Answers must have at least one grounded citation.
        elif state == "answers":

            if not citations:
                state = "silent"
                answer = (
                    "The supplied evidence was insufficient to "
                    "validate a supported answer."
                )

        # Contradiction must cite at least two pieces of evidence.
        elif state == "contradiction":

            if len(citations) < 2:
                state = "silent"
                citations = []
                answer = (
                    "The supplied evidence was insufficient to "
                    "verify a contradiction."
                )

        return QAResult(
            question,
            state,
            answer,
            citations,
            evidence,
        )