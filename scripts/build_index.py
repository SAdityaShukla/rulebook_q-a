import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from retrieve import Retriever
n=Retriever().rebuild()
print(f"Indexed {n} chunks into ChromaDB.")
