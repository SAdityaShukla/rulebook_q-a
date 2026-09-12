import re
from ingest import load_all
from schemas import Chunk

def markdown_chunks(doc):
    out = []
    pattern = r"(?ms)^###\s+(.+?)\n(.*?)(?=^###\s+|\Z)"
    for m in re.finditer(pattern, doc.content):
        title = m.group(1).strip()
        body = re.sub(r"\s+", " ", m.group(2)).strip()
        num_match = re.match(r"([\d.]+)", title)
        num = num_match.group(1).rstrip(".") if num_match else title.lower().replace(" ", "-")
        out.append(Chunk(f"{doc.filename}#{num}", doc.filename, f"{doc.filename}, Section {title}", body))
    return out

def csv_chunks(doc):
    out = []
    for i, r in enumerate(doc.content, 1):
        if r["semester"] == "Policy Note":
            text = f"{r['fee_component']}: {r['note']}"
            loc = f"{doc.filename}, Policy Note"
        else:
            text = "; ".join(f"{k}: {v}" for k, v in r.items())
            loc = f"{doc.filename}, Row {i}"
        out.append(Chunk(f"{doc.filename}#row-{i}", doc.filename, loc, text))
    return out

def pdf_chunks(doc):
    out = []
    for n, text in doc.content:
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            out.append(Chunk(f"{doc.filename}#{n}", doc.filename, f"{doc.filename} (PDF), Page {n}", text))
    return out

def load_and_chunk():
    out = []
    for d in load_all():
        if d.kind == "markdown": out += markdown_chunks(d)
        elif d.kind == "csv": out += csv_chunks(d)
        else: out += pdf_chunks(d)
    return out
