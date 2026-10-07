from pathlib import Path
from .rag import CareerRAG
from .orchestrator import CareerAdvisorOrchestrator

def build_advisor(pdf_path: str | Path = "data/IP_Career_Listings.pdf"):
    return CareerAdvisorOrchestrator(CareerRAG(pdf_path))
