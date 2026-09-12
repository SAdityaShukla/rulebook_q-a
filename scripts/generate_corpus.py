"""Corpus generator already run for this submission package."""
from pathlib import Path
import re
p=Path(__file__).resolve().parents[1]/"data/raw/academic_regulations.md"
text=p.read_text(encoding="utf-8")
print("Academic regulations words:",len(re.findall(r"\\b[\\w’'-]+\\b",text)))
print("Corpus files:",len(list(p.parent.iterdir())))
