# Policy Proof — Groq + ChromaDB

Policy Proof is an evidence-grounded university policy QA system built for a vibe-coding evaluation. It deliberately distinguishes three outcomes: **answers**, **silent**, and **contradiction**.

## Stack
- **LLM:** Groq — `openai/gpt-oss-120b` (configurable via `.env`)
- **Embeddings:** `all-MiniLM-L6-v2` locally
- **Vector database:** ChromaDB with persistent local storage
- **UI:** Streamlit
- **Formats:** Markdown, CSV, PDF

## Corpus and benchmark
- Academic regulations: **11,300 words**
- Mixed-format sources: `academic_regulations.md`, `society_constitution.md`, `fee_schedule.csv`, `hostel_handbook.pdf`
- Three intentional contradictions documented in `data/contradictions.md`
- 42 evaluation questions: 9 answerable, 25 silent/near-miss, 8 contradiction

## Architecture
1. Ingest Markdown/CSV/PDF.
2. Convert policy material into stable, citable chunks.
3. Generate local embeddings with Sentence Transformers.
4. Persist embeddings and metadata in ChromaDB.
5. Retrieve the top policy evidence for a student question.
6. Apply a retrieval-distance gate to support abstention.
7. Ask Groq for a strict JSON classification and evidence-grounded answer.
8. Validate the returned state and citations against retrieved evidence before displaying it.

The LLM is **not** allowed to invent citations. Silent answers contain no citations; contradiction answers require at least two validated citations.

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your Groq key:

```env
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
```

## Build index

```bash
python scripts/build_index.py
```

## Evaluate

```bash
python scripts/evaluate.py
```

The evaluator reports state accuracy and full citation-aware score separately. Do not claim a score until you run it with your own Groq key.

## Tests

```bash
pytest tests/
```

## Run demo

```bash
streamlit run src/app.py
```

See `demo/demo-script.md` for the recommended three-state demonstration.

## Important
The corpus is synthetic, created specifically for this evaluation. It should not be presented as an actual university's regulations.
