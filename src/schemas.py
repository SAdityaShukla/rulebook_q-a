from dataclasses import dataclass, asdict, field

@dataclass
class Chunk:
    chunk_id: str
    source_file: str
    location: str
    text: str
    def to_dict(self): return asdict(self)

@dataclass
class RetrievedChunk:
    chunk: Chunk
    distance: float

@dataclass
class QAResult:
    question: str
    state: str
    answer: str
    citations: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
