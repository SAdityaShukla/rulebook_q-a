import csv, re
from pathlib import Path
from dataclasses import dataclass
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/"data/raw"
@dataclass
class RawDocument:
    filename: str
    kind: str
    content: object

def load_all():
    docs=[]
    for p in sorted(RAW.iterdir()):
        if p.suffix==".md": docs.append(RawDocument(p.name,"markdown",p.read_text(encoding="utf-8")))
        elif p.suffix==".csv":
            with open(p,encoding="utf-8",newline="") as f: docs.append(RawDocument(p.name,"csv",list(csv.DictReader(f))))
        elif p.suffix==".pdf":
            pages=[]
            with pdfplumber.open(p) as pdf:
                for n,page in enumerate(pdf.pages,1): pages.append((n,page.extract_text() or ""))
            docs.append(RawDocument(p.name,"pdf",pages))
    return docs
