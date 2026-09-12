import json
import os
from dotenv import load_dotenv
from groq import Groq
from retrieve import Retriever
from schemas import QAResult

load_dotenv()
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.95"))

SYSTEM = """You are Policy Proof, an evidence-grounded university policy reasoner.
Use ONLY the supplied policy evidence. Never use general university knowledge.

Choose exactly one state:
- answers: the supplied evidence directly establishes an answer to the question.
- silent: the supplied evidence does not establish an answer. Adjacent or vaguely related rules are not enough.
- contradiction: two or more supplied policy clauses make incompatible claims that directly matter to the question.

Important:
- A contradiction is NOT merely two rules covering different situations. The provisions must conflict for the same situation.
- Do not resolve or invent a hierarchy unless the evidence explicitly gives one.
- Every substantive claim in an answers response must be supported by cited evidence.
- For silent, citations MUST be [] and the answer must clearly say the corpus does not establish the requested fact.
- For contradiction, cite all directly conflicting chunks.

Return JSON only with this exact shape:
{"state":"answers|silent|contradiction","answer":"...","citations":["exact-chunk-id"]}
"""

class Reasoner:
    def __init__(self):
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is missing. Put it in .env.")
        self.client = Groq(api_key=key)
        self.retriever = Retriever()

    def ask(self, question):
        hits = self.retriever.search(question, top_k=8)
        hits = [h for h in hits if h.distance <= MAX_DISTANCE]
        evidence = [
            {"chunk_id": h.chunk.chunk_id, "location": h.chunk.location,
             "text": h.chunk.text, "distance": round(h.distance, 4)}
            for h in hits
        ]
        if not evidence:
            return QAResult(question, "silent", "The supplied policy corpus does not contain enough evidence to answer this question.", [], [])

        user_prompt = json.dumps({"question": question, "evidence": evidence}, ensure_ascii=False)
        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=800,
        )
        try:
            data = json.loads(response.choices[0].message.content)
        except Exception:
            return QAResult(question, "silent", "The system could not produce a validated policy answer.", [], evidence)

        state = data.get("state", "silent")
        answer = str(data.get("answer", "")).strip()
        citations = data.get("citations", [])
        if not isinstance(citations, list): citations = []
        valid_ids = {e["chunk_id"] for e in evidence}
        citations = [c for c in citations if c in valid_ids]

        if state not in {"answers", "silent", "contradiction"}:
            state = "silent"
        if state == "silent":
            citations = []
            answer = answer or "The supplied policy corpus does not establish the requested fact."
        elif state == "contradiction" and len(citations) < 2:
            state = "silent"
            citations = []
            answer = "The supplied evidence was insufficient to verify a contradiction."
        elif state == "answers" and not citations:
            state = "silent"
            answer = "The supplied evidence was insufficient to validate a supported answer."

        return QAResult(question, state, answer, citations, evidence)
