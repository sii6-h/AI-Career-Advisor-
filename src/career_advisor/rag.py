from pathlib import Path
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

class CareerRAG:
    def __init__(self, pdf_path: str | Path, model_name: str = "all-MiniLM-L6-v2"):
        self.pdf_path = Path(pdf_path)
        self.embedding_model = SentenceTransformer(model_name)
        self.chunks = self._create_chunks(self._load_pages())
        self.embeddings = self.embedding_model.encode([c["text"] for c in self.chunks], normalize_embeddings=True, show_progress_bar=False)

    def _load_pages(self):
        reader = PdfReader(str(self.pdf_path))
        return [{"page": i, "text": (p.extract_text() or "").strip()} for i,p in enumerate(reader.pages,1) if (p.extract_text() or "").strip()]

    @staticmethod
    def _create_chunks(pages, chunk_size=800, overlap=150):
        chunks=[]
        for page in pages:
            start=0
            while start < len(page["text"]):
                text=page["text"][start:start+chunk_size].strip()
                if text: chunks.append({"page":page["page"],"text":text})
                start += chunk_size-overlap
        return chunks

    def retrieve(self, query: str, top_k: int = 3):
        q=self.embedding_model.encode([query], normalize_embeddings=True)[0]
        scores=np.dot(self.embeddings,q)
        indices=np.argsort(scores)[::-1][:top_k]
        return [{"source":"O*NET Career Listings","page":self.chunks[i]["page"],"content":self.chunks[i]["text"],"retrieval_score":float(scores[i])} for i in indices]
