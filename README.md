# DocIntel AI — Enterprise Document Intelligence & Multi-Agent RAG Platform

DocIntel AI is a production-grade, multi-agent document intelligence platform engineered for automated document extractions, structured table parsing, and high-precision Q&A with strict zero-hallucination verification.

The platform combines a multi-agent orchestration architecture (LangGraph) with local AI execution (Ollama) to deliver fast, cost-free, and privacy-preserving document analysis across complex policy documents, financial disclosures, and legal contracts up to 500 pages.

---

## Key Features

- **Automated Key Highlights Extraction**: Automatically parses and categorizes critical document sections (Coverage Scope, Deductibles, Exclusions, Claim Deadlines, and Financial Terms) upon upload.
- **5-Layer Multi-Agent Verification Architecture**: Operates a sequential multi-agent execution pipeline (Planner, Router, Retriever, Synthesizer, Verifier) to eliminate hallucinated responses.
- **Page-Level & Bounding Box Source Citation**: Every generated response includes verifiable citations referencing source pages, section paths, and document chunks.
- **Deep Document & Table Parsing**: Integrates Docling layout parsing with PaddleOCR for robust structural extraction from scanned PDFs, DOCX files, and spreadsheets.
- **100% Local Inference Engine**: Fully compatible with local LLMs (Ollama `qwen2.5`, `llama3.2`) and local embedding models (`bge-m3`), ensuring complete data privacy and 0 API rate limit bottlenecks.
- **Industrial Deep Onyx UI**: High-contrast, dark-mode dashboard built with Next.js 15, TailwindCSS, and Lucide icons following enterprise design standards.

---

## System Architecture

```text
[ Upload Document (PDF / DOCX / XLSX) ]
                  │
                  ▼
[ Ingestion Pipeline: Docling + PaddleOCR ] ──► [ Layout Chunker ]
                                                      │
                                                      ▼
                                           [ Dense Embedding (bge-m3) ]
                                                      │
                                                      ▼
                                           [ Vector Storage: Qdrant ]

-----------------------------------------------------------------------

[ User Query ]
      │
      ▼
[ Planner Agent ] ────► Tentukan Intent & Strategy (QA / Extraction / Clarification)
      │
      ▼
[ Router Agent ] ─────► Route Pipeline Execution
      │
      ▼
[ Retriever Agent ] ──► Hybrid Dense + BM25 Retrieval & Reranking
      │
      ▼
[ Synthesizer Agent ] ► Generate Response + Source Citations
      │
      ▼
[ Verifier Agent ] ───► 5-Layer Fact Checking & Confidence Rating
      │
      ▼
[ Final Response ]
```

---

## Agent Pipeline Overview

1. **Planner Agent**: Analyzes user intent, checks query clarity, and decomposes complex queries into optimal retrieval sub-queries.
2. **Router Agent**: Dispatches execution paths dynamically based on query type (RAG QA, Structured Extract, or Document Overview).
3. **Retriever Agent**: Executes hybrid dense vector search and sparse BM25 keyword matching with Reciprocal Rank Fusion (RRF).
4. **Synthesizer Agent**: Generates concise, grounded responses strictly constrained to retrieved context chunks with source citations.
5. **Verifier Agent**: Validates claims against source passages, assigns confidence scores (High/Medium/Low), and suppresses ungrounded assertions.

---

## Technology Stack

### Backend
- **Framework**: Python 3.11, FastAPI
- **Agent Orchestration**: LangGraph, LangChain
- **Vector Database**: Qdrant Vector Search
- **Metadata Database**: SQLite (Async SQLAlchemy + AIOSQLite)
- **Document Parsing**: Docling, PaddleOCR, OpenPyXL, PyMuPDF
- **Local AI Engine**: Ollama (`bge-m3`, `qwen2.5:0.5b`, `llama3.2`)

### Frontend
- **Framework**: Next.js 15 (App Router), React 19, TypeScript
- **Styling**: TailwindCSS (Deep Onyx Theme)
- **Icons**: Lucide React
- **HTTP Client**: Native Fetch API

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (installed locally)
- Qdrant Vector Engine (or Docker)

### 1. Local AI Engine Setup (Ollama)
Ensure Ollama is running and pull the required models:
```bash
ollama pull bge-m3
ollama pull qwen2.5:0.5b
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -e .
```

Configure environment settings:
```bash
cp .env.example .env
```

Start the FastAPI application:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your web browser.

---

## API Endpoints Reference

### Document Management
- `POST /api/documents/upload` — Upload PDF/DOCX/XLSX files for background parsing.
- `GET /api/documents` — List all ingested documents and processing statuses.
- `GET /api/documents/{id}/highlights` — Retrieve extracted key highlights, categories, and tables.
- `DELETE /api/documents/{id}` — Delete document record and vector points.

### Q&A & Extractions
- `POST /api/query` — Execute multi-agent RAG Q&A pipeline with source citations.
- `POST /api/extract` — Perform schema-driven structured JSON extraction.

---

## License

Distributed under the MIT License. See `LICENSE` for details.
