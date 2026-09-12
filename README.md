# Policy Proof — The Rulebook That Argues With Itself

**Policy Proof** is an evidence-grounded policy question-answering system built for **Problem 1: The Rulebook That Argues With Itself**.

It answers questions from a controlled university policy corpus and, importantly, distinguishes between:

* **Answers** — the supplied policy evidence directly establishes the answer.
* **Silent** — the corpus does not establish the requested fact.
* **Contradiction** — two supplied policy provisions make incompatible claims about the same situation.

The system is designed to avoid inventing policy rules and to expose the evidence behind every supported or contradictory answer.

---

## Problem

University policy documents often contain rules spread across different sections and documents. Sometimes the rules are incomplete, sometimes a requested fact simply does not exist in the available corpus, and sometimes two provisions genuinely conflict.

A conventional RAG system may retrieve relevant-looking text and confidently generate an answer even when:

* the corpus does not contain the requested information,
* the retrieved rules apply to different situations,
* or two retrieved provisions directly contradict each other.

**Policy Proof** treats these cases differently instead of forcing every question into a normal answer.

---

## What the System Does

Given a policy question, Policy Proof:

1. Retrieves relevant policy chunks using semantic search.
2. Filters the retrieved evidence using a configurable relevance threshold.
3. Detects whether the question is asking about an exception, waiver, override, committee authority, or explicit conflict.
4. Expands known conflict groups when the question genuinely requires conflict analysis.
5. Sends only the retrieved policy evidence to the LLM.
6. Forces the LLM to choose exactly one state:

   * `answers`
   * `silent`
   * `contradiction`
7. Validates the returned citations against the retrieved evidence.
8. Displays the answer and supporting policy evidence in the Streamlit interface.

The model is explicitly instructed **not to use general university knowledge**.

---

## Architecture

```text
                    User Question
                         │
                         ▼
                 ┌───────────────┐
                 │   Retriever   │
                 └───────┬───────┘
                         │
                  Semantic Search
                         │
                         ▼
                 ┌───────────────┐
                 │ ChromaDB      │
                 │ Vector Store  │
                 └───────┬───────┘
                         │
                   Relevant Chunks
                         │
                         ▼
              Conflict-aware retrieval
                         │
                         ▼
                 ┌───────────────┐
                 │   Reasoner    │
                 │   Groq LLM    │
                 └───────┬───────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          ANSWERS      SILENT   CONTRADICTION
             │           │           │
             └───────────┼───────────┘
                         ▼
                  Citation Validation
                         │
                         ▼
                  Streamlit UI
```

---

## Three Possible States

### 1. `answers`

The supplied evidence directly establishes the requested fact.

Example:

> What is the minimum laboratory attendance requirement?

The system can cite the laboratory attendance provision and answer from it.

---

### 2. `silent`

The supplied corpus does not establish the requested fact.

The system does **not** guess based on adjacent or vaguely related policies.

For example, if the corpus says nothing about cryptocurrency fee payments, the system returns:

```text
silent
```

with no citations.

---

### 3. `contradiction`

Two or more supplied policy provisions make incompatible claims that directly matter to the question.

For example, the corpus intentionally contains both:

* a provision stating that laboratory attendance below 80% cannot receive an exception or committee review, and
* another provision stating that the Academic Review Committee can waive the 80% laboratory attendance requirement in exceptional circumstances.

The system identifies both provisions rather than silently choosing one.

---

# Corpus

The project uses a **synthetic university policy corpus** created specifically for this problem.

It contains multiple policy sources, including:

* Academic Regulations
* Fee Schedule
* Hostel Handbook
* Society Constitution

The corpus contains ordinary policy rules as well as deliberately planted contradictory provisions.

### Important contradiction groups

#### Laboratory attendance

* `academic_regulations.md#1.4`
* `academic_regulations.md#3.2`

These provisions intentionally create a conflict between an apparently absolute 80% laboratory attendance requirement and an explicit committee waiver provision.

#### Fee extensions

* `academic_regulations.md#17.1`
* `academic_regulations.md#17.2`

These provisions conflict over whether late fees continue during an approved fee extension.

#### Scholarship attendance

* `academic_regulations.md#18.1`
* `academic_regulations.md#18.2`

These provisions contain incompatible treatment of attendance waivers and Merit Scholarship eligibility.

---

# Retrieval

The vector database is implemented using **ChromaDB**.

Documents are:

1. Loaded from `data/raw/`
2. Split into policy chunks
3. Embedded using `all-MiniLM-L6-v2`
4. Stored in a persistent ChromaDB collection

The retriever uses cosine similarity.

A conflict-aware retrieval layer prevents ordinary questions from accidentally becoming contradictions merely because both sides of an intentionally conflicting policy happen to be semantically similar.

For example:

```text
"What is the minimum laboratory attendance requirement?"
```

should retrieve the normal laboratory attendance rule rather than automatically treating the question as a contradiction.

However:

```text
"Can the committee waive the laboratory attendance requirement?"
```

requires the conflicting provisions to be considered together.

---

# Reasoning

The reasoning layer uses the Groq API and an LLM configured through:

```text
GROQ_MODEL
```

The default model is:

```text
openai/gpt-oss-120b
```

The system prompt enforces evidence-grounded reasoning.

The model is instructed to:

* use only supplied policy evidence,
* never invent university rules,
* distinguish unsupported facts from contradictions,
* cite evidence for substantive answers,
* return no citations for silent questions,
* cite all directly conflicting clauses for contradictions.

The returned JSON is also validated by the application before being accepted.

---

# Citation Validation

The reasoner does not blindly trust citations returned by the LLM.

Returned citation IDs are checked against the IDs of the retrieved evidence.

Invalid citation IDs are discarded.

Additional validation rules include:

* `silent` → citations must be empty
* `answers` → requires supporting citations
* `contradiction` → requires at least two valid citations

This keeps the final result grounded in evidence that was actually retrieved.

---

# Evaluation Benchmark

The evaluation set contains **25 questions**.

The benchmark is intentionally divided into:

| Category      | Questions |
| ------------- | --------: |
| Answers       |        10 |
| Silent        |        10 |
| Contradiction |         5 |
| **Total**     |    **25** |

### Answers

Questions whose answers are directly established by the corpus.

### Silent

Questions asking for information that is not established by the corpus.

These test whether the system knows when **not to answer**.

### Contradiction

Questions designed around the deliberately conflicting policy provisions.

These test whether the system can identify conflicting evidence rather than selecting one rule arbitrarily.

---

# Evaluation

Run:

```bash
python scripts/evaluate.py
```

The evaluator reports:

* state accuracy,
* full score including citation requirements,
* per-state accuracy,
* individual question results.

Example output format:

```text
A01 | expected=answers       got=answers       state=PASS full=PASS
S01 | expected=silent        got=silent        state=PASS full=PASS
C01 | expected=contradiction got=contradiction state=PASS full=PASS

=== POLICY PROOF EVALUATION ===
Questions:      25
State accuracy: ...
Full score:     ...
answers        : ...
silent         : ...
contradiction  : ...
```

---

# Project Structure

```text
rulebook_q-a/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
│
├── data/
│   ├── raw/
│   │   ├── academic_regulations.md
│   │   ├── fee_schedule.csv
│   │   ├── hostel_handbook.pdf
│   │   └── society_constitution.md
│   │
│   ├── processed/
│   │   └── chroma/
│   │
│   └── eval_questions.jsonl
│
├── scripts/
│   ├── build_index.py
│   ├── evaluate.py
│   └── generate_corpus.py
│
└── src/
    ├── chunker.py
    ├── ingest.py
    ├── reasoner.py
    ├── retrieve.py
    └── schemas.py
```

---

# Installation

## 1. Clone the repository

```bash
git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_URL>
cd rulebook_q-a
```

## 2. Create a virtual environment

Windows:

```cmd
python -m venv .venv
```

Activate it:

```cmd
.venv\Scripts\activate
```

## 3. Install dependencies

```cmd
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Optional configuration variables include:

```env
MAX_DISTANCE=0.95
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_DIR=data/processed/chroma
CHROMA_COLLECTION=policy_chunks
```

**Do not commit your actual API key.**

---

# Build the Vector Index

After installing the dependencies and placing the policy corpus in `data/raw/`:

```cmd
python scripts/build_index.py
```

This creates the persistent ChromaDB index.

---

# Run the Evaluation

```cmd
python scripts/evaluate.py
```

The evaluator reads:

```text
data/eval_questions.jsonl
```

and runs all 25 benchmark questions through the complete retrieval + reasoning pipeline.

---

# Run the Application

Start the Streamlit interface:

```cmd
streamlit run app.py
```

The UI allows a user to ask policy questions and inspect:

* the predicted state,
* the generated answer,
* citations,
* retrieved evidence,
* and the underlying policy locations.

---

# What Is Mocked / Synthetic

This submission uses a **synthetic policy corpus**.

The university regulations, fee schedule, hostel handbook, and society constitution are controlled data created for the benchmark. They are **not official university policies** and should not be treated as real institutional regulations.

The contradiction cases are intentionally planted into the synthetic corpus to evaluate contradiction detection.

The 25-question evaluation set is also a controlled benchmark created for this submission.

The system's LLM reasoning is **not mocked**; it uses the configured Groq API.

The vector retrieval layer is also real and uses a persistent ChromaDB index.

---

# Design Decisions

### Evidence over confidence

The system should prefer:

```text
"I don't have enough evidence."
```

over inventing an answer.

### Contradiction over arbitrary resolution

When two provisions directly conflict, the system does not decide which one "sounds more correct."

It reports the contradiction and cites both provisions.

### Scope matters

Two rules mentioning the same topic do not automatically constitute a contradiction.

For example, a general theory attendance rule and a laboratory attendance rule may apply to different categories.

The system therefore distinguishes between:

```text
same topic
```

and:

```text
same situation + incompatible claims
```

### Explicit exceptions matter

The corpus contains cases where an apparently general rule is followed by a more specific exception or delegated authority.

The retrieval layer therefore only expands known contradiction groups when the question indicates that the exception or conflict is actually relevant.

---

# Limitations

* The benchmark corpus is synthetic rather than production university policy.
* Retrieval quality depends on the embedding model and indexed chunks.
* The final reasoning step depends on the configured LLM.
* Contradiction detection is limited to evidence available to the system.
* The system does not attempt to establish an external legal or institutional hierarchy between conflicting provisions.
* A policy that is absent from the corpus is treated as unsupported rather than inferred from general knowledge.

---

# Tech Stack

* **Python**
* **Streamlit**
* **ChromaDB**
* **Sentence Transformers**
* **all-MiniLM-L6-v2**
* **Groq API**
* **LLM-based evidence reasoning**
* **pdfplumber**
* **python-dotenv**

---

# Core Files

| File                     | Purpose                                                |
| ------------------------ | ------------------------------------------------------ |
| `src/ingest.py`          | Loads Markdown, CSV and PDF policy sources             |
| `src/chunker.py`         | Converts source documents into policy chunks           |
| `src/retrieve.py`        | Embedding-based retrieval and conflict-aware retrieval |
| `src/reasoner.py`        | Evidence-grounded LLM reasoning and validation         |
| `src/schemas.py`         | Data structures for chunks and QA results              |
| `scripts/build_index.py` | Builds the ChromaDB index                              |
| `scripts/evaluate.py`    | Runs the 25-question benchmark                         |
| `app.py`                 | Streamlit user interface                               |

---

# Submission

**Problem:**
`1 · The Rulebook That Argues With Itself`

**Repository:**
Public GitHub repository containing the complete implementation, synthetic corpus, evaluation benchmark, README, and source code.

The repository is intended to be reproducible using the setup instructions above.
