import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from chunker import load_and_chunk

ROOT = Path(__file__).resolve().parents[1]

def test_corpus_is_6000_plus_words():
    text = (ROOT / "data/raw/academic_regulations.md").read_text(encoding="utf-8")
    assert len(re.findall(r"\b[\w’'-]+\b", text)) >= 6000

def test_mixed_formats_exist():
    raw = ROOT / "data/raw"
    assert (raw / "academic_regulations.md").exists()
    assert (raw / "fee_schedule.csv").exists()
    assert (raw / "hostel_handbook.pdf").exists()
    assert (raw / "society_constitution.md").exists()

def test_stable_citations_and_chunks():
    chunks = load_and_chunk()
    ids = {c.chunk_id for c in chunks}
    assert len(chunks) > 20
    assert "academic_regulations.md#1.1" in ids
    assert "academic_regulations.md#1.4" in ids
    assert "academic_regulations.md#3.2" in ids
    assert "academic_regulations.md#17.1" in ids
    assert "academic_regulations.md#17.2" in ids
    assert "academic_regulations.md#18.1" in ids
    assert "academic_regulations.md#18.2" in ids
    assert "academic_regulations.md#19.1" in ids
    assert "academic_regulations.md#19.2" in ids
