# PRD: DocIntel AI — Multi-Agent Document Intelligence Platform

## 1. Document Control

| Field | Value |
|-------|-------|
| Document Title | DocIntel AI — Product Requirements Document |
| Version | 1.0 |
| Status | Draft |
| Document Type | Product Requirements Document (PRD) |
| Owner | Syahril Arfian Almazril |
| Target Deployment | Local Development (Free Tier) — untuk demo internal |
| Target End State | Enterprise deployment on-prem (Phase 2, di luar scope PRD ini) |
| Related Documents | E2E Health Renewal SME PRD v3.0 |
| Last Updated | 8 Agustus 2026 |

### 1.1 Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-08 | S.A. Almazril | Initial draft |

### 1.2 Approval Matrix

| Role | Name | Approval Required |
|------|------|-------------------|
| Author / Developer | S.A. Almazril | ✓ |
| Technical Reviewer | TBD | Pending |
| Product Owner | TBD | Pending |
| Security Reviewer | TBD | Pending (untuk fase deployment) |

---

## 2. Executive Summary

DocIntel AI adalah platform intelligence dokumen berbasis multi-agent yang dirancang untuk memproses dokumen enterprise berukuran besar (100+ halaman) dari format campuran (PDF, DOCX, XLSX, gambar/scan) dan menyediakan dua kapabilitas utama: **(1) extraction informasi penting terstruktur** dan **(2) tanya-jawab (Q&A) atas isi dokumen** — keduanya dengan jaminan **zero-hallucination** melalui citation mandatory, groundedness verification, dan confidence gating.

Sistem menggunakan arsitektur dua-fase: **ingestion pipeline deterministik** (Docling + PaddleOCR + hybrid chunking + embedding) yang berjalan asinkron saat upload, dan **agent orchestrator berbasis LangGraph** (Planner → Router → Retriever/Extractor/Table/Graph → Synthesizer → Verifier) yang berjalan saat query.

Untuk fase MVP (demo), seluruh sistem dijalankan **lokal di laptop developer** menggunakan Docker Compose, dengan LLM hybrid: model lokal via Ollama untuk embedding/verifier ringan, dan API free tier (Groq Llama 3.3 70B + Google Gemini 2.0 Flash) untuk reasoning dan extraction utama. Total biaya operasional MVP = **Rp 0**.

Target akhir Phase 1: sistem dapat menerima dokumen produk asuransi 20-100 halaman, mengekstrak semua field kritis (produk, benefit, premi, syarat, tanggal, signatory) dengan akurasi ≥95% pada extractive queries, dan menjawab pertanyaan user dengan citation yang bisa diklik menuju halaman + bounding-box sumber.

---

## 3. Latar Belakang & Problem Statement

### 3.1 Konteks Bisnis

Industri asuransi (termasuk PT Sompo Insurance Indonesia) menghadapi volume tinggi dokumen kompleks: proposal produk (PDS), polis, klaim, medical report, kontrak reinsurance, dokumen underwriting. Dokumen ini umumnya:

- Berukuran besar (20-500+ halaman)
- Multi-format dalam satu paket klaim (PDF native, PDF scan, Excel benefit table, Word draft, foto kwitansi)
- Bilingual (Indonesia + Inggris) dengan terminologi teknis
- Kritis untuk keputusan finansial dan legal — akurasi mutlak diperlukan
- Sensitive: mengandung PII, data medis, informasi komersial

### 3.2 Pain Points Saat Ini

| # | Pain Point | Dampak |
|---|-----------|--------|
| 1 | Manual review dokumen memakan waktu 2-8 jam per dokumen | Bottleneck di underwriting & claim assessment |
| 2 | Cari informasi spesifik (mis. "premi Worldwide Platinum untuk 7 hari") butuh scroll manual antar tabel | Produktivitas rendah, error rate tinggi |
| 3 | Data extraction untuk sistem downstream (mis. E2E Health Renewal) dilakukan re-typing manual | Risiko error, tidak scalable |
| 4 | Tools generic AI chat (ChatGPT/Gemini web) berhalusinasi & tidak bisa audit | Tidak layak untuk keputusan produksi |
| 5 | Data sensitif tidak boleh keluar organisasi | Solusi cloud SaaS terbatasi regulasi (POJK, UU PDP) |

### 3.3 Solusi yang Diusulkan

Platform DocIntel AI menyediakan:

1. **Upload multi-format** dengan parsing otomatis
2. **Structured extraction** — dokumen masuk, JSON tervalidasi keluar
3. **Q&A chatbot** dengan citation ke sumber persis
4. **Anti-hallucination guarantees** — sistem menolak menjawab jika tidak yakin
5. **Deployment fleksibel** — lokal untuk demo, on-prem untuk produksi
6. **Audit trail lengkap** — setiap jawaban traceable ke sumber dokumen

---

## 4. Tujuan & Success Metrics

### 4.1 Business Objectives

| # | Objective | Rasional |
|---|-----------|----------|
| BO-1 | Mengurangi waktu manual review dokumen 70%+ | Efisiensi operasional |
| BO-2 | Mencapai extraction accuracy ≥95% pada field kritis | Kelayakan produksi |
| BO-3 | Zero-hallucination pada extractive queries | Trust & audit compliance |
| BO-4 | Mendukung integrasi ke sistem E2E Health Renewal SME | Value chain internal |
| BO-5 | Deployment on-prem capable | Compliance regulasi |

### 4.2 Success Metrics (MVP Phase)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Extraction Accuracy (extractive) | ≥ 95% | Golden set of 50 Q&A pairs |
| Q&A Faithfulness (RAGAS) | ≥ 0.90 | RAGAS eval on test set |
| Q&A Answer Relevance | ≥ 0.85 | RAGAS eval on test set |
| Context Precision | ≥ 0.85 | RAGAS eval on test set |
| Citation Accuracy | 100% | Every citation must resolve to real source location |
| Refusal Rate (untuk out-of-scope query) | ≥ 95% | Adversarial test set |
| End-to-end Latency (Q&A) | ≤ 15 detik | P95 pada dokumen 50 halaman |
| Ingestion Latency (per halaman) | ≤ 5 detik | Rata-rata pada mixed corpus |

### 4.3 Non-Goals (untuk PRD ini)

- Multi-tenant / multi-user production access management
- SSO / Active Directory integration
- Fine-tuning custom LLM
- Deployment cluster / high-availability
- Real-time collaborative editing
- Full audit logging untuk kepatuhan SOX/PCI-DSS

---

## 5. Scope

### 5.1 In-Scope (MVP Phase 1 — 8 minggu)

**Ingestion:**
- Upload multi-file (PDF, DOCX, XLSX, JPG, PNG)
- Parsing native (Docling primary) + OCR fallback (PaddleOCR)
- Layout-aware chunking (section-based, tidak character-based)
- Contextual enrichment per chunk
- Embedding generation (bge-m3 via Ollama)
- Storage ke Qdrant + PostgreSQL

**Query & Extraction:**
- Chat Q&A dengan streaming response
- Structured extraction dengan schema definable
- Hybrid retrieval (dense + sparse BM25)
- Reranking (bge-reranker-v2-m3)
- Multi-agent orchestration (LangGraph)
- Groundedness verification (verifier LLM)
- Confidence scoring per jawaban
- Refusal ketika confidence rendah

**UI:**
- Chat interface dengan message streaming
- File upload dengan progress tracking
- PDF viewer dengan bbox highlight untuk citation
- Agent trace panel (real-time step visualization)
- Confidence badge per jawaban
- Structured extraction result viewer (JSON tree)

**Ops:**
- Docker Compose orkestrasi
- Langfuse observability (self-hosted)
- Environment configuration via `.env`

### 5.2 Out-of-Scope (untuk MVP)

- User authentication / multi-tenancy
- Cloud deployment
- Fine-tuning
- Full-text search index terpisah (BM25 di-handle oleh Qdrant sparse vectors)
- Knowledge graph advanced (LightRAG / GraphRAG) — dijadwal untuk Phase 2
- Batch processing dari folder (hanya upload manual)
- Export ke format lain selain JSON (CSV, XLSX, Word)
- Custom document classifier

### 5.3 Future Scope (Phase 2+)

- Deployment on-prem Sompo (Kubernetes / OpenShift)
- SSO integration (Azure AD / LDAP)
- Multi-tenant workspace (per department / per case)
- Knowledge graph untuk relational reasoning
- Fine-tuned model untuk domain asuransi Indonesia
- Integrasi API ke E2E Health Renewal SME
- Batch processing pipeline
- Human-in-the-loop annotation UI untuk correction
- Active learning: learn from user corrections

---

## 6. User Persona & Use Cases

### 6.1 Persona

**P1 — Underwriter (Primary User)**
- Perlu analyze proposal produk & polis untuk decision approve/reject
- Query typical: "Apa loss ratio estimate?", "Berapa max age?", "Apa exclusion utama?"
- Technical fluency: medium

**P2 — Product Owner / BA (Primary User)**
- Perlu extract full benefit matrix untuk masukkan ke sistem internal
- Query typical: "Extract semua benefit dan premi", "Compare produk A vs B"
- Technical fluency: medium-high

**P3 — Claim Analyst (Secondary User)**
- Review medical documents & claim documents
- Query typical: "Diagnosis pasien apa?", "Total tagihan berapa?", "Apakah tercover?"
- Technical fluency: medium

**P4 — Actuary (Secondary User)**
- Analisis premi & risk assessment
- Query typical: "Berapa premi Family Worldwide untuk semua durasi?", "Bagaimana loading premi usia 70+?"
- Technical fluency: high

### 6.2 Use Cases

**UC-1: Product Document Analysis**
- Actor: Product Owner
- Precondition: User punya proposal produk asuransi (10-50 halaman)
- Flow:
  1. User upload dokumen
  2. Sistem parse & index (async, dengan progress bar)
  3. User klik "Extract Structured Data"
  4. Sistem menampilkan JSON hasil extraction
  5. User verify + export JSON

**UC-2: Interactive Q&A**
- Actor: Underwriter
- Precondition: Dokumen sudah di-index
- Flow:
  1. User buka chat interface, pilih dokumen
  2. User tanya "Berapa loss ratio estimation?"
  3. Sistem streaming answer dengan citation
  4. User klik citation → PDF viewer highlight halaman + bbox
  5. User tanya follow-up "Apa consequence jika loss ratio > 25%?"

**UC-3: Cross-Document Comparison**
- Actor: Product Owner
- Precondition: 2+ dokumen sudah di-index
- Flow:
  1. User pilih multiple documents
  2. User tanya "Bandingkan premi Platinum Individual dari dokumen A dan B"
  3. Sistem retrieve dari kedua doc, generate comparison table
  4. Setiap value punya citation ke dokumen sumbernya

**UC-4: Refusal Case (Anti-Hallucination Demo)**
- Actor: Any user
- Precondition: Dokumen sudah di-index
- Flow:
  1. User tanya sesuatu yang tidak ada di dokumen ("Apakah cover kegiatan naik gunung?")
  2. Sistem retrieve, tidak menemukan match kuat
  3. Verifier reject synthesizer output
  4. Sistem respond: "Informasi mengenai kegiatan naik gunung tidak ditemukan di dokumen. Yang tersedia adalah [X, Y, Z]."

---

## 7. Functional Requirements

### 7.1 Document Ingestion

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ING-1 | Sistem harus menerima upload multi-file simultan (max 10 file, total 100MB) | P0 |
| FR-ING-2 | Support format: PDF (native & scan), DOCX, XLSX, JPG, PNG | P0 |
| FR-ING-3 | Auto-detect file type dan route ke parser yang tepat | P0 |
| FR-ING-4 | Progress tracking per file (parsing → chunking → embedding → indexing) | P0 |
| FR-ING-5 | Preserve struktur dokumen (heading hierarchy, table structure, section boundaries) | P0 |
| FR-ING-6 | Simpan original file di local filesystem dengan hash-based naming | P0 |
| FR-ING-7 | Extract metadata (title, author, page count, created date) | P1 |
| FR-ING-8 | Support DOCX dengan tracked changes (extract clean version) | P2 |
| FR-ING-9 | Handle PDF terenkripsi (prompt password ke user) | P2 |
| FR-ING-10 | Duplicate detection (hash-based) — reject re-upload dokumen sama | P1 |

### 7.2 Extraction Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-EXT-1 | Support user-defined schema (Pydantic model atau JSON Schema) | P0 |
| FR-EXT-2 | Provide pre-built schema untuk 3 tipe dokumen asuransi (product proposal, policy wording, claim form) | P0 |
| FR-EXT-3 | Setiap field yang di-extract HARUS punya citation `{doc_id, page, bbox, source_text}` | P0 |
| FR-EXT-4 | Return `null` (bukan hallucinate) jika field tidak ditemukan | P0 |
| FR-EXT-5 | Support field types: string, number, date, boolean, enum, array, nested object | P0 |
| FR-EXT-6 | Confidence score per field | P0 |
| FR-EXT-7 | Batch extraction (extract semua field yang define di schema dalam 1 pass) | P0 |
| FR-EXT-8 | Export hasil extraction ke JSON | P0 |
| FR-EXT-9 | Support numerical field validation (regex, range, format) | P1 |
| FR-EXT-10 | Support cross-field business rules (mis. `end_date > start_date`) | P1 |

### 7.3 Q&A Chat Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-QA-1 | Streaming response (kata per kata muncul, bukan tunggu selesai) | P0 |
| FR-QA-2 | Every answer statement harus punya citation inline | P0 |
| FR-QA-3 | Support Indonesian & English query (auto-detect language) | P0 |
| FR-QA-4 | Support multi-turn conversation (context-aware follow-up) | P0 |
| FR-QA-5 | Show agent execution trace (planner → retriever → verifier) | P1 |
| FR-QA-6 | Support clarification request ketika query ambigu | P0 |
| FR-QA-7 | Refusal mechanism ketika query tidak dapat dijawab dari dokumen | P0 |
| FR-QA-8 | Chat history persistence (per session) | P1 |
| FR-QA-9 | Export chat transcript | P2 |
| FR-QA-10 | Multi-document query (query cross beberapa dokumen sekaligus) | P1 |

### 7.4 Citation & Traceability

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CIT-1 | Setiap citation berisi minimal: `doc_id`, `page_number`, `chunk_id`, `text_snippet` | P0 |
| FR-CIT-2 | Untuk PDF, citation juga menyertakan `bbox` (bounding box coordinates) | P0 |
| FR-CIT-3 | Klik citation di UI harus buka PDF viewer di halaman terkait dengan highlight | P0 |
| FR-CIT-4 | Citation snippet di UI menampilkan preview text (100-200 char) | P0 |
| FR-CIT-5 | Multiple citations per statement supported (ranked by relevance) | P0 |
| FR-CIT-6 | Citation validation: text_snippet HARUS ditemukan verbatim di source doc | P0 |

### 7.5 Confidence Scoring

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CONF-1 | Setiap jawaban punya confidence score `[0.0, 1.0]` | P0 |
| FR-CONF-2 | Formula: `confidence = retrieval_score × groundedness_score × llm_confidence` | P0 |
| FR-CONF-3 | UI menampilkan badge: 🟢 high (>0.85), 🟡 medium (0.65-0.85), 🔴 low (<0.65) | P0 |
| FR-CONF-4 | Low confidence trigger refusal atau clarification | P0 |
| FR-CONF-5 | Threshold configurable via `.env` | P1 |

### 7.6 Observability

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-OBS-1 | Semua LLM call ter-log di Langfuse (input, output, latency, cost) | P0 |
| FR-OBS-2 | Agent execution trace ter-log per session | P0 |
| FR-OBS-3 | Retrieval performance metrics (recall@k, precision) | P1 |
| FR-OBS-4 | Error tracking (failed extractions, timeout, dll) | P0 |
| FR-OBS-5 | Dashboard untuk view aggregate metrics | P1 |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PERF-1 | Ingestion throughput | ≤ 5 detik per halaman (rata-rata) |
| NFR-PERF-2 | Q&A response latency (P95) | ≤ 15 detik untuk dokumen 50 halaman |
| NFR-PERF-3 | First token latency (streaming) | ≤ 3 detik |
| NFR-PERF-4 | Retrieval latency | ≤ 500 ms |
| NFR-PERF-5 | Reranking latency | ≤ 2 detik untuk 20 candidates |

### 8.2 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-REL-1 | Ingestion failure rate | ≤ 2% |
| NFR-REL-2 | Uptime (untuk local dev) | Manual restart acceptable |
| NFR-REL-3 | API rate limit handling | Auto-retry dengan exponential backoff |
| NFR-REL-4 | Graceful degradation | Kalau Groq down, fallback ke Gemini; kalau keduanya down, fallback ke local Ollama |

### 8.3 Security & Privacy

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SEC-1 | Data at rest | Semua dokumen tersimpan di local filesystem (untuk MVP) |
| NFR-SEC-2 | API key management | `.env` file, tidak di-commit ke Git |
| NFR-SEC-3 | Log sanitization | Langfuse boleh capture prompt/response, tapi tidak boleh log raw file content |
| NFR-SEC-4 | Session isolation | Chat session tidak leak ke session lain |

### 8.4 Scalability (untuk transisi ke Phase 2)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SCALE-1 | Codebase modular | Ganti Qdrant Cloud dengan Qdrant self-hosted tanpa refactor |
| NFR-SCALE-2 | Stateless backend | Ready untuk horizontal scaling |
| NFR-SCALE-3 | Async task queue | Ingestion bisa scale ke multiple workers |

### 8.5 Maintainability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-MAINT-1 | Test coverage | ≥ 70% untuk core modules |
| NFR-MAINT-2 | Documentation | Docstring untuk semua public function |
| NFR-MAINT-3 | Code style | PEP8, black formatter |
| NFR-MAINT-4 | Dependency management | `pyproject.toml` + lock file |

---

## 9. System Architecture

### 9.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                            │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼───────────────────────────────────┐
│                  FRONTEND (Next.js @ :3000)                      │
│  • Chat UI (Vercel AI SDK)                                       │
│  • File Upload (react-dropzone)                                  │
│  • PDF Viewer (react-pdf + bbox overlay)                         │
│  • Agent Trace Panel                                             │
└────────────────────────────┬───────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼───────────────────────────────────┐
│               BACKEND API (FastAPI @ :8000)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Router: /upload, /query, /extract, /documents           │  │
│  └────────┬─────────────────────────────┬──────────────────┘  │
│           │                             │                      │
│  ┌────────▼────────────┐   ┌───────────▼──────────────────┐  │
│  │  INGESTION PIPELINE │   │  QUERY ORCHESTRATOR (LangGraph)│ │
│  │  (Celery Worker)    │   │                                │ │
│  │                     │   │  ┌──────────┐  ┌──────────┐   │ │
│  │  1. Router (type)   │   │  │ Planner  │→ │ Router   │   │ │
│  │  2. Docling parse   │   │  └──────────┘  └────┬─────┘   │ │
│  │  3. OCR fallback    │   │                     │         │ │
│  │  4. Chunking        │   │       ┌─────────────┼──────┐  │ │
│  │  5. Enrichment      │   │       ▼             ▼      ▼  │ │
│  │  6. Embedding       │   │  ┌────────┐ ┌────────┐┌────┐  │ │
│  │  7. Index to Qdrant │   │  │Retrieval│ │ Table  ││Extr│  │ │
│  │                     │   │  └────┬───┘ └───┬────┘└──┬─┘  │ │
│  └─────────────────────┘   │       └──────┬──┴────────┘   │ │
│                            │              ▼                │ │
│                            │        ┌──────────┐           │ │
│                            │        │Synthesizer│          │ │
│                            │        └────┬─────┘           │ │
│                            │             ▼                 │ │
│                            │        ┌──────────┐           │ │
│                            │        │ Verifier │           │ │
│                            │        └────┬─────┘           │ │
│                            │             ▼                 │ │
│                            │      Final Answer + Citation  │ │
│                            └─────────────────────────────┬─┘ │
└──────┬───────────────┬───────────────────┬───────────────┼───┘
       │               │                   │               │
┌──────▼──────┐ ┌──────▼──────┐  ┌────────▼──────┐ ┌─────▼──────┐
│  Qdrant     │ │ PostgreSQL  │  │  Redis        │ │  Langfuse  │
│  (:6333)    │ │ (:5432)     │  │  (:6379)      │ │  (:3001)   │
│             │ │             │  │               │ │            │
│  Vector +   │ │  Metadata   │  │  Task Queue   │ │  Trace &   │
│  Sparse     │ │  Session    │  │  Cache        │ │  Metrics   │
└─────────────┘ └─────────────┘  └───────────────┘ └────────────┘

              ┌─────────────────────────────────────┐
              │        LLM LAYER                     │
              │                                      │
              │  ┌────────────┐  ┌────────────────┐ │
              │  │  Ollama    │  │  API (Free)    │ │
              │  │  (local)   │  │                │ │
              │  │            │  │  • Groq        │ │
              │  │  bge-m3    │  │    Llama 3.3   │ │
              │  │  qwen2.5:7b│  │  • Gemini 2.0  │ │
              │  │            │  │    Flash       │ │
              │  └────────────┘  └────────────────┘ │
              └─────────────────────────────────────┘

Files stored: ./data/documents/{doc_hash}/original.{ext}
```

### 9.2 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Frontend | User interaction, streaming display, PDF rendering |
| Backend API | Request routing, session management, orchestration entry |
| Ingestion Pipeline | Async document processing (parse, chunk, embed, index) |
| Query Orchestrator | Multi-agent flow for Q&A and extraction |
| Qdrant | Vector similarity search + sparse BM25 |
| PostgreSQL | Document metadata, session state, chat history |
| Redis | Celery task queue, cache |
| Langfuse | Observability (traces, metrics, cost tracking) |
| Ollama | Local LLM runtime (embedding + light inference) |
| Groq / Gemini | Primary LLM inference (via API) |

### 9.3 Data Flow (Upload → Query)

**Ingestion Flow:**
```
1. User uploads file → Frontend POST /upload
2. Backend saves file to ./data/documents/{hash}/
3. Backend creates Document record in PostgreSQL (status=PENDING)
4. Backend enqueues Celery task
5. Celery worker picks up:
   a. Detect file type
   b. Route to parser:
      - PDF native → PyMuPDF via Docling
      - PDF scan → PaddleOCR PP-StructureV3
      - DOCX → Docling
      - XLSX → openpyxl + Docling
      - Image → PaddleOCR
   c. Extract structured content (title, sections, tables, figures)
   d. Layout-aware chunking (per section, max 1000 tokens/chunk)
   e. Contextual enrichment (Gemini Flash: "Chunk ini dari section X tentang Y")
   f. Generate embeddings (bge-m3 via Ollama)
   g. Generate sparse vector (BM25 via Qdrant native)
   h. Upsert to Qdrant with metadata
   i. Update Document status=INDEXED
6. Frontend polls /documents/{id}/status until INDEXED
```

**Query Flow:**
```
1. User submits query → Frontend POST /query (WebSocket)
2. Backend spawns LangGraph orchestrator
3. Planner Agent:
   - Analyze query intent (extract vs. QA vs. compare)
   - Decompose into sub-queries if needed
   - Select strategy
4. Router Agent:
   - For QA → Retrieval Agent
   - For structured data → Extraction Agent
   - For tabular query → Table Agent
5. Retrieval Agent:
   - Generate query embedding
   - Hybrid search (dense + sparse) in Qdrant
   - Fetch top-20 candidates
   - Rerank via bge-reranker-v2-m3
   - Return top-5 chunks
6. Synthesizer Agent:
   - Prompt: "Answer from context ONLY. Cite every claim. Return null if not found."
   - Generate answer (Groq Llama 3.3 70B, streaming)
   - Structured output via Instructor (Pydantic schema with citation)
7. Verifier Agent:
   - NLI-style check: does answer entail from cited sources?
   - Confidence scoring
   - If confidence < threshold → reject, request retry or refuse
8. Return final answer + citations + confidence to frontend (streaming)
9. Log to Langfuse
```

---

## 10. Technology Stack

### 10.1 Frontend

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Framework | Next.js | 15.x | App Router, server actions, streaming built-in |
| UI Library | shadcn/ui + Tailwind CSS | Latest | Production-grade, customizable, gratis |
| Chat SDK | Vercel AI SDK (`ai`) | 4.x | Streaming, message state, tool calls |
| PDF Rendering | react-pdf | 9.x | Client-side PDF viewer |
| File Upload | react-dropzone | 14.x | Drag-drop, multi-file |
| State Management | Zustand | 5.x | Ringan, minimal boilerplate |
| Data Fetching | TanStack Query | 5.x | Cache, retry, optimistic updates |
| Icons | lucide-react | Latest | Consistent icon set |
| Language | TypeScript | 5.x | Type safety |

### 10.2 Backend

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Framework | FastAPI | 0.115+ | Async native, auto OpenAPI docs, Pydantic integration |
| Language | Python | 3.11+ | Ecosystem AI/ML |
| Task Queue | Celery | 5.4+ | Battle-tested untuk async job |
| Message Broker | Redis | 7-alpine | Celery broker + cache |
| WebSocket | FastAPI WebSocket | native | Streaming ke frontend |
| Validation | Pydantic | 2.x | Type-safe schema |
| Structured LLM Output | Instructor | Latest | Enforce Pydantic schema pada LLM output |
| Async DB | asyncpg + SQLAlchemy 2.0 (async) | Latest | Non-blocking DB access |
| Migration | Alembic | Latest | Schema versioning |

### 10.3 AI/ML Layer

| Purpose | Technology | Runtime | Free Tier / Cost |
|---------|-----------|---------|------------------|
| Agent Orchestration | LangGraph | Python | Free (open-source) |
| Document Parsing | Docling (IBM) | Python | Free (open-source) |
| OCR | PaddleOCR PP-StructureV3 | Python | Free (open-source) |
| Embedding | bge-m3 (multilingual) | Ollama local | Free (local) |
| Reranker | bge-reranker-v2-m3 | Python (FlagEmbedding) | Free (local) |
| Reasoner/Synthesizer | Llama 3.3 70B | Groq API | 30 req/min free |
| Extractor | Gemini 2.0 Flash | Google AI Studio API | 1500 req/day free |
| Verifier | Qwen 2.5 7B Instruct | Ollama local | Free (local) |
| Local Fallback | Llama 3.2 3B | Ollama local | Free (local) |

### 10.4 Data Layer

| Store | Technology | Purpose | Free Tier |
|-------|-----------|---------|-----------|
| Vector DB | Qdrant (Docker) | Dense + sparse vectors, metadata filter | Free (self-hosted) |
| Metadata DB | PostgreSQL 16 (Docker) | Doc metadata, session, chat history | Free (self-hosted) |
| Queue/Cache | Redis 7 (Docker) | Celery broker, cache | Free (self-hosted) |
| File Storage | Local filesystem | Original documents, hash-named | N/A |
| Observability | Langfuse (Docker) | LLM traces, metrics | Free (self-hosted) |

### 10.5 Infrastructure (Local Development)

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | v2+ | Multi-container orchestration |
| Ollama | Latest | Native install (bukan Docker) untuk optimal GPU access |
| Git | 2.x | Version control |
| Node.js | 20 LTS | Frontend dev |
| Python | 3.11+ | Backend dev |
| Poetry / uv | Latest | Python dependency management |

### 10.6 Development Tools

| Tool | Purpose |
|------|---------|
| Ruff | Python linter & formatter |
| MyPy | Python type checker |
| Pytest | Python testing |
| ESLint + Prettier | JS/TS lint & format |
| Vitest | Frontend testing |
| Pre-commit | Git hooks |

---

## 11. Data Model

### 11.1 PostgreSQL Schema

```sql
-- Document metadata
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(20) NOT NULL,  -- pdf, docx, xlsx, image
    file_size_bytes BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    page_count INTEGER,
    status VARCHAR(20) NOT NULL,     -- PENDING, PARSING, INDEXING, INDEXED, FAILED
    error_message TEXT,
    metadata JSONB,                   -- title, author, created_date, etc.
    doc_type VARCHAR(50),             -- product_proposal, policy_wording, claim_form, etc.
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    indexed_at TIMESTAMPTZ
);

CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_hash ON documents(file_hash);

-- Chunk registry (for citation resolution)
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    section_path TEXT,                -- e.g. "Section 5.2 > Table 3"
    chunk_type VARCHAR(20),           -- text, table, figure, heading
    content TEXT NOT NULL,
    contextual_prefix TEXT,           -- enrichment prefix
    bbox JSONB,                       -- {x0, y0, x1, y1} for PDFs
    qdrant_point_id VARCHAR(100),     -- reference to Qdrant point
    metadata JSONB
);

CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_qdrant ON chunks(qdrant_point_id);

-- Chat sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100),             -- placeholder for MVP
    document_ids UUID[],              -- scoped documents
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Chat messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,        -- user, assistant, system
    content TEXT NOT NULL,
    citations JSONB,                  -- array of citation objects
    confidence FLOAT,
    agent_trace JSONB,                -- planner/router/retriever steps
    llm_metadata JSONB,               -- model, tokens, cost
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON messages(session_id);

-- Extraction jobs (async structured extraction)
CREATE TABLE extraction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    schema_definition JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,      -- PENDING, RUNNING, COMPLETED, FAILED
    result JSONB,
    confidence_scores JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

### 11.2 Qdrant Collection Schema

```python
# Collection: "documents"
{
    "vectors": {
        "dense": {
            "size": 1024,  # bge-m3 dimension
            "distance": "Cosine"
        }
    },
    "sparse_vectors": {
        "bm25": {
            "modifier": "idf"
        }
    }
}

# Point payload structure
{
    "chunk_id": "uuid",
    "document_id": "uuid",
    "page_number": 12,
    "section_path": "Section 5.2 > Benefit Table",
    "chunk_type": "table",  # text | table | figure | heading
    "content": "...",
    "contextual_prefix": "Chunk ini dari...",
    "bbox": {"x0": 100, "y0": 200, "x1": 500, "y1": 400},
    "doc_type": "product_proposal",
    "metadata": {
        "language": "id_en",
        "table_id": "benefit_asean_platinum",
        "created_at": "2026-08-08T..."
    }
}
```

### 11.3 Citation Object Schema

```typescript
type Citation = {
    doc_id: string;
    doc_name: string;
    page_number: number;
    chunk_id: string;
    section_path: string;
    text_snippet: string;      // 200 char preview
    bbox?: {x0, y0, x1, y1};   // PDF only
    relevance_score: number;    // 0.0 - 1.0
};
```

---

## 12. API Design

### 12.1 REST Endpoints

**POST `/api/documents/upload`**
```json
Request: multipart/form-data
  - files: File[]
  - doc_type?: string

Response 202 Accepted:
{
    "documents": [
        {
            "id": "uuid",
            "filename": "Product_Test_AI.docx",
            "status": "PENDING",
            "task_id": "celery_task_uuid"
        }
    ]
}
```

**GET `/api/documents/{id}/status`**
```json
Response 200:
{
    "id": "uuid",
    "status": "INDEXING",
    "progress": {
        "current_step": "chunking",
        "steps_completed": 3,
        "total_steps": 7,
        "percentage": 42
    }
}
```

**GET `/api/documents/{id}`**
```json
Response 200:
{
    "id": "uuid",
    "filename": "...",
    "file_type": "docx",
    "page_count": 24,
    "doc_type": "product_proposal",
    "status": "INDEXED",
    "chunk_count": 156,
    "metadata": {...}
}
```

**POST `/api/query`** (WebSocket recommended)
```json
Request:
{
    "session_id": "uuid",
    "document_ids": ["uuid1", "uuid2"],
    "query": "Berapa premi Worldwide Platinum untuk 7-9 hari?",
    "options": {
        "stream": true,
        "include_trace": true
    }
}

Response (streaming):
event: token
data: {"content": "Premi Worldwide Platinum Individual untuk"}

event: token
data: {"content": " 7-9 hari adalah Rp 576.840"}

event: citation
data: {
    "citations": [{
        "doc_id": "uuid",
        "page_number": 3,
        "text_snippet": "...",
        "bbox": {...}
    }]
}

event: confidence
data: {"score": 0.94, "level": "high"}

event: done
data: {"message_id": "uuid"}
```

**POST `/api/extract`**
```json
Request:
{
    "document_id": "uuid",
    "schema": {
        "product_name": {"type": "string"},
        "insurer": {"type": "string"},
        "loss_ratio_estimate": {"type": "number"},
        "signatories": {
            "type": "array",
            "items": {
                "name": {"type": "string"},
                "title": {"type": "string"}
            }
        }
    }
}

Response 200:
{
    "extraction_id": "uuid",
    "result": {
        "product_name": {
            "value": "Asuransi Travelapp",
            "citation": {...},
            "confidence": 0.98
        },
        "loss_ratio_estimate": {
            "value": 0.25,
            "citation": {...},
            "confidence": 0.95
        }
    }
}
```

**GET `/api/sessions/{id}/messages`**
```json
Response 200:
{
    "messages": [
        {
            "id": "uuid",
            "role": "user",
            "content": "...",
            "created_at": "..."
        },
        {
            "id": "uuid",
            "role": "assistant",
            "content": "...",
            "citations": [...],
            "confidence": 0.94,
            "created_at": "..."
        }
    ]
}
```

### 12.2 WebSocket Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `query` | Client → Server | Submit query |
| `token` | Server → Client | Streaming token |
| `agent_step` | Server → Client | Agent execution step update |
| `citation` | Server → Client | Citation attached to statement |
| `confidence` | Server → Client | Final confidence score |
| `error` | Server → Client | Error event |
| `done` | Server → Client | Completion signal |
| `ping/pong` | Both | Keepalive |

---

## 13. Agent Design (Detail)

### 13.1 Planner Agent

**Purpose:** Analyze user query, decompose if complex, select execution strategy.

**Input:**
- User query (raw string)
- Conversation history (last 5 turns)
- Available document IDs

**Output:**
```python
class Plan(BaseModel):
    intent: Literal["qa", "extraction", "comparison", "clarification_needed"]
    sub_queries: list[str]
    strategy: Literal["single_retrieval", "multi_retrieval", "table_lookup", "structured_extract"]
    reasoning: str
    requires_clarification: bool
    clarification_question: Optional[str]
```

**LLM Model:** Groq Llama 3.3 70B (temp=0.1)

**Prompt Template:**
```
Anda adalah planner untuk sistem Q&A dokumen asuransi.
Analisis query user, tentukan strategi optimal.

Available documents:
{document_summaries}

Conversation history:
{history}

User query: "{query}"

Tugas:
1. Identify intent (qa/extraction/comparison/clarification_needed)
2. Decompose ke sub-queries jika perlu
3. Pilih strategy
4. Jika query ambigu, MINTA klarifikasi (jangan tebak)

Output JSON sesuai schema Plan.
```

### 13.2 Retrieval Agent

**Purpose:** Hybrid retrieval + reranking dari Qdrant.

**Steps:**
1. Generate dense embedding via bge-m3 (Ollama)
2. Generate sparse vector via Qdrant native BM25
3. Qdrant hybrid search dengan RRF (Reciprocal Rank Fusion), top-20
4. Rerank via bge-reranker-v2-m3, ambil top-5
5. Return chunks dengan metadata + scores

**Configuration:**
```python
RETRIEVAL_CONFIG = {
    "top_k_initial": 20,
    "top_k_final": 5,
    "min_relevance_score": 0.3,
    "fusion_alpha": 0.6,  # weight dense vs sparse
}
```

### 13.3 Table Agent

**Purpose:** Handle query yang membutuhkan tabular reasoning (e.g. "premi Family Worldwide 14-17 hari").

**Steps:**
1. Detect chunk_type == "table" dalam retrieved chunks
2. Parse table structure (rows, columns, cell values)
3. Locate specific cell based on query dimensions (area × plan × duration)
4. Return cell value + surrounding context untuk citation

**Note:** Untuk MVP, treat table sebagai text with structure preserved. Full text-to-SQL untuk XLSX di Phase 2.

### 13.4 Extraction Agent

**Purpose:** Execute schema-driven extraction.

**Input:**
- Document ID
- Pydantic schema (or JSON schema)

**Steps:**
1. Retrieve relevant chunks per field (schema-guided retrieval)
2. Construct prompt dengan schema + few-shot examples
3. Call Gemini 2.0 Flash dengan Instructor (structured output)
4. Validate output vs. schema (format, regex, range)
5. Verify each field's citation exists in source
6. Return structured result dengan confidence per field

**Sample Schema (Insurance Product):**
```python
class InsuranceProductExtraction(BaseModel):
    product_name: FieldWithCitation[str]
    insurer: FieldWithCitation[str]
    insured_type: FieldWithCitation[list[str]]
    coverage_areas: FieldWithCitation[list[str]]
    max_age_adult: FieldWithCitation[int]
    max_age_child: FieldWithCitation[int]
    premium_loading_senior: FieldWithCitation[float]  # 0.35 for +35%
    loss_ratio_estimate: FieldWithCitation[float]
    commission_percent: FieldWithCitation[float]
    marketing_fee_percent: FieldWithCitation[float]
    free_look_period_days: FieldWithCitation[Optional[int]]
    signatories: FieldWithCitation[list[Signatory]]
    effective_date: FieldWithCitation[date]
    benefit_matrix: FieldWithCitation[list[BenefitRow]]
    premium_matrix: FieldWithCitation[list[PremiumRow]]

class FieldWithCitation(Generic[T]):
    value: Optional[T]
    citation: Optional[Citation]
    confidence: float
    reasoning: Optional[str]  # if value is None, why?
```

### 13.5 Synthesizer Agent

**Purpose:** Generate final answer dari retrieved context.

**LLM Model:** Groq Llama 3.3 70B (temp=0.0)

**Prompt Template:**
```
Anda adalah asisten Q&A untuk dokumen asuransi.
Jawab HANYA berdasarkan CONTEXT di bawah.

ATURAN KETAT:
1. Jangan gunakan pengetahuan umum. Hanya dari CONTEXT.
2. Setiap fakta HARUS punya citation ke chunk_id.
3. Jika informasi TIDAK ADA di context, katakan tegas: "Informasi tersebut tidak ditemukan di dokumen."
4. Jangan menebak, jangan menyimpulkan di luar teks.
5. Untuk nilai numerik, kutip persis seperti di dokumen.

CONTEXT:
{retrieved_chunks_with_ids}

CONVERSATION HISTORY:
{history}

USER QUERY: {query}

Output structured (via Instructor):
{
    "answer": "...",
    "statements": [
        {"claim": "...", "citation_chunk_ids": ["...", "..."]}
    ],
    "not_found_reason": null or "..."
}
```

### 13.6 Verifier Agent

**Purpose:** Verify groundedness dari synthesizer output.

**LLM Model:** Ollama Qwen 2.5 7B (diversity dari synthesizer)

**Steps:**
1. Untuk setiap statement dalam answer, verify dengan cited chunks
2. NLI-style check: apakah statement entailed by chunks?
3. Return per-statement verdict: `ENTAILED / PARTIAL / CONTRADICTED / NOT_SUPPORTED`
4. Compute overall groundedness score
5. Jika groundedness < 0.7 → reject, trigger refusal atau retry

**Prompt Template:**
```
Anda adalah verifier untuk fact-check jawaban.

STATEMENT: "{statement}"

CITED SOURCE:
{chunk_content}

Tugas: Tentukan apakah STATEMENT bisa disimpulkan dari CITED SOURCE.

Output:
{
    "verdict": "ENTAILED" | "PARTIAL" | "CONTRADICTED" | "NOT_SUPPORTED",
    "confidence": 0.0-1.0,
    "reasoning": "..."
}
```

### 13.7 Agent Coordination (LangGraph)

```python
from langgraph.graph import StateGraph, END

class OrchestratorState(TypedDict):
    query: str
    session_id: str
    document_ids: list[str]
    history: list[Message]
    plan: Optional[Plan]
    retrieved_chunks: list[Chunk]
    draft_answer: Optional[str]
    verification: Optional[Verification]
    final_answer: Optional[str]
    citations: list[Citation]
    confidence: float
    trace: list[TraceEvent]

graph = StateGraph(OrchestratorState)
graph.add_node("planner", planner_agent)
graph.add_node("router", router_agent)
graph.add_node("retriever", retrieval_agent)
graph.add_node("table_agent", table_agent)
graph.add_node("extractor", extraction_agent)
graph.add_node("synthesizer", synthesizer_agent)
graph.add_node("verifier", verifier_agent)
graph.add_node("refusal", refusal_handler)

graph.set_entry_point("planner")
graph.add_conditional_edges("planner", route_from_planner, {
    "retrieve": "retriever",
    "extract": "extractor",
    "refuse": "refusal",
    "clarify": END,
})
graph.add_edge("retriever", "synthesizer")
graph.add_edge("extractor", "verifier")
graph.add_edge("synthesizer", "verifier")
graph.add_conditional_edges("verifier", route_from_verifier, {
    "accept": END,
    "reject": "refusal",
    "retry": "retriever",
})
graph.add_edge("refusal", END)
```

---

## 14. Anti-Hallucination Strategy

### 14.1 Layered Defense

Sistem menerapkan **5 layer defense** terhadap halusinasi:

**Layer 1 — Retrieval Grounding**
- LLM tidak pernah melihat query tanpa retrieved context
- Prompt eksplisit: "Jawab HANYA dari context"
- Zero fallback ke world knowledge

**Layer 2 — Citation Mandatory**
- Structured output dengan Instructor: setiap statement WAJIB punya `citation_chunk_ids`
- Empty citation → statement rejected
- Citation text_snippet HARUS ditemukan verbatim di source (fuzzy match tolerance ≤5%)

**Layer 3 — Constrained Decoding**
- Instructor + Pydantic force LLM output ke schema
- Impossible untuk output free-form text yang bypass validation

**Layer 4 — Verifier Agent (Second Opinion)**
- Model berbeda dari synthesizer (Qwen 2.5 7B vs Llama 3.3 70B)
- NLI-style entailment check per statement
- Model diversity mengurangi kesamaan bias

**Layer 5 — Confidence Gating**
- Composite score: `retrieval × groundedness × llm_confidence`
- Threshold 0.7: below → refuse to answer
- User sees confidence badge, tahu kapan mempercayai

### 14.2 Refusal Mechanism

Sistem menolak menjawab dalam 4 kondisi:

| Kondisi | Response |
|---------|----------|
| Retrieval score rendah (top chunk < 0.3) | "Tidak ada informasi relevan di dokumen untuk pertanyaan ini." |
| Verifier verdict = NOT_SUPPORTED | "Tidak dapat memverifikasi jawaban dari dokumen." |
| Confidence < 0.7 setelah retry | "Tingkat kepercayaan rendah. Silakan spesifikkan pertanyaan." |
| Query ambigu (planner detect) | "Bisa dispesifikkan? Apakah maksud Anda [option A] atau [option B]?" |

### 14.3 Confidence Score Formula

```python
def compute_confidence(
    retrieval_score: float,       # top-1 rerank score, 0-1
    groundedness_score: float,    # avg verifier confidence, 0-1
    llm_self_confidence: float,   # LLM logprob-derived, 0-1
    citation_coverage: float,     # % statements with valid citation, 0-1
) -> float:
    # Weighted geometric mean (penalizes low value in any dimension)
    weights = [0.25, 0.35, 0.15, 0.25]
    scores = [retrieval_score, groundedness_score, llm_self_confidence, citation_coverage]
    
    log_sum = sum(w * math.log(max(s, 0.01)) for w, s in zip(weights, scores))
    return math.exp(log_sum)
```

### 14.4 Anti-Hallucination Test Cases

Test cases khusus yang wajib pass:

| Test | Query | Expected Behavior |
|------|-------|-------------------|
| T1 | "Apakah cover kegiatan hiking?" (tidak ada di dokumen) | Refusal, bukan menebak |
| T2 | "Berapa premi Platinum 7-9 hari?" (ambigu antar area) | Clarification request |
| T3 | "Compute premi usia 72 tahun Worldwide Platinum 7-9 hari" | Explicit formula displayed, bukan langsung angka |
| T4 | "Siapa CEO dari Sompo?" (world knowledge, bukan dari doc) | Refusal, bukan jawab dari training data |
| T5 | Query dengan typo → planner recover atau clarify | No silent misinterpretation |

---

## 15. Extraction Schema (Sample: Insurance Product Document)

Skema spesifik untuk dokumen tipe **product proposal / PDS** (Product Disclosure Statement) — sesuai contoh dokumen Asuransi Travelapp yang di-review.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
from decimal import Decimal

class Citation(BaseModel):
    doc_id: str
    page_number: int
    chunk_id: str
    section_path: str
    text_snippet: str
    bbox: Optional[dict] = None

class FieldWithCitation[T](BaseModel):
    value: Optional[T]
    citation: Optional[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None

class Signatory(BaseModel):
    name: FieldWithCitation[str]
    title: FieldWithCitation[str]
    organization: FieldWithCitation[str]

class BenefitItem(BaseModel):
    benefit_number: int
    benefit_name: FieldWithCitation[str]
    coverage_area: FieldWithCitation[str]  # ASEAN+, APAC, Worldwide, Schengen, Non-Schengen, Domestic
    plan_tier: FieldWithCitation[str]      # Platinum, Gold, Basic
    limit_amount: FieldWithCitation[Optional[Decimal]]  # None jika "Tidak Tersedia"
    limit_currency: FieldWithCitation[Literal["IDR", "USD"]]
    limit_unit: FieldWithCitation[Literal["per_person", "per_family", "per_incident", "aggregate", "per_day"]]
    conditions: FieldWithCitation[Optional[str]]  # e.g. "Tidak Tersedia", "Sesuai tagihan"

class PremiumRow(BaseModel):
    coverage_area: FieldWithCitation[str]
    plan_tier: FieldWithCitation[str]
    insured_type: FieldWithCitation[Literal["Individual", "Dual", "Family"]]
    duration_range: FieldWithCitation[str]  # "1-3 hari", "Tahunan", etc.
    base_premium_idr: FieldWithCitation[Decimal]
    age_range: FieldWithCitation[str]  # "0-69 tahun"

class AddOnBenefit(BaseModel):
    add_on_name: FieldWithCitation[str]
    coverage_area: FieldWithCitation[str]
    plan_tier: FieldWithCitation[str]
    limit_amount: FieldWithCitation[Optional[Decimal]]
    additional_premium_idr: FieldWithCitation[Optional[Decimal]]

class SpecialCondition(BaseModel):
    condition_name: FieldWithCitation[str]  # e.g. "Age 70-75 Loading"
    condition_type: FieldWithCitation[str]
    parameters: FieldWithCitation[dict]  # e.g. {"age_min": 70, "age_max": 75, "loading_percent": 35}

class InsuranceProductExtraction(BaseModel):
    # Identity
    product_name: FieldWithCitation[str]
    product_name_english: FieldWithCitation[Optional[str]]
    insurer: FieldWithCitation[str]
    insured_target: FieldWithCitation[str]  # e.g. "Nasabah PT Bank X"
    
    # Coverage
    coverage_areas: FieldWithCitation[list[str]]
    insured_types: FieldWithCitation[list[str]]  # Individual, Dual, Family
    coverage_period_short_trip_max_days: FieldWithCitation[int]  # e.g. 183
    coverage_period_annual_max_days_per_trip: FieldWithCitation[int]  # e.g. 90
    
    # Age
    max_age_adult: FieldWithCitation[int]  # e.g. 75
    max_age_child: FieldWithCitation[int]  # e.g. 21 or 25
    child_age_extended_condition: FieldWithCitation[Optional[str]]
    
    # Special conditions
    senior_loading_percent: FieldWithCitation[float]  # e.g. 0.35 for 35%
    senior_age_range: FieldWithCitation[str]  # "70-75 years"
    special_conditions: FieldWithCitation[list[SpecialCondition]]
    
    # Commercial
    commission_percent: FieldWithCitation[float]  # 0.20
    marketing_fee_percent: FieldWithCitation[float]  # 0.10
    loss_ratio_estimate: FieldWithCitation[float]  # 0.25
    loss_ratio_review_months: FieldWithCitation[int]  # 6
    
    # Policy conditions
    free_look_period_days: FieldWithCitation[Optional[int]]  # None if not available
    max_policies_per_cif: FieldWithCitation[int]  # 1
    
    # Sales
    sales_channel: FieldWithCitation[str]
    payment_source: FieldWithCitation[list[str]]  # ["Conventional", "Syariah"]
    
    # Content
    benefits: FieldWithCitation[list[BenefitItem]]
    add_on_benefits: FieldWithCitation[list[AddOnBenefit]]
    premium_matrix: FieldWithCitation[list[PremiumRow]]
    exclusions: FieldWithCitation[list[str]]
    
    # Signatures
    effective_date: FieldWithCitation[date]
    signing_location: FieldWithCitation[str]
    signatories: FieldWithCitation[list[Signatory]]
    
    # Meta
    document_language: FieldWithCitation[Literal["id", "en", "id_en"]]
    document_version: FieldWithCitation[Optional[str]]
```

**Validation Rules:**
```python
VALIDATION_RULES = [
    # Business rule: Platinum > Gold untuk premi
    lambda p: all(
        p.premium_matrix.value[i].base_premium_idr.value >= 
        p.premium_matrix.value[j].base_premium_idr.value
        for i, j in same_area_duration_where(i.plan == "Platinum", j.plan == "Gold")
    ),
    # Family >= Dual >= Individual
    lambda p: all(...),
    # Commission + marketing fee = valid range
    lambda p: 0 <= p.commission_percent.value + p.marketing_fee_percent.value <= 0.5,
    # Loss ratio in reasonable range
    lambda p: 0.1 <= p.loss_ratio_estimate.value <= 0.9,
]
```

---

## 16. Testing & Evaluation

### 16.1 Test Data (Golden Set)

Build corpus dari 5-10 dokumen representatif:

| Doc Type | Count | Source |
|----------|-------|--------|
| Product Proposal (PDS) | 3 | Sample dokumen internal (di-anonymize) |
| Policy Wording | 2 | Sample dokumen internal |
| Claim Form + Medical | 2 | Synthetic (untuk demo) |
| Benefit Comparison (XLSX) | 1 | Sample dokumen internal |
| Contract Draft (DOCX) | 1 | Sample dokumen internal |

Per dokumen, siapkan **10-20 Q&A pairs** dengan expected answer + citation.

### 16.2 Evaluation Metrics

**RAGAS Metrics:**
- Faithfulness (target ≥ 0.90)
- Answer Relevance (target ≥ 0.85)
- Context Precision (target ≥ 0.85)
- Context Recall (target ≥ 0.80)

**Custom Metrics:**
- Citation Accuracy (100% target — citation must resolve)
- Refusal Precision (untuk out-of-scope queries)
- Extraction Field Accuracy (per-field precision/recall)

**Latency Metrics:**
- P50, P95, P99 for Q&A response
- Ingestion throughput (pages/second)

### 16.3 Evaluation Automation

```python
# tests/eval/test_qa_quality.py
import pytest
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

@pytest.mark.eval
def test_qa_golden_set():
    dataset = load_golden_set("golden_qa.jsonl")
    results = []
    for item in dataset:
        answer = system.query(
            document_id=item.doc_id,
            query=item.query
        )
        results.append({
            "question": item.query,
            "answer": answer.text,
            "contexts": [c.text for c in answer.citations],
            "ground_truth": item.expected_answer
        })
    
    scores = evaluate(
        results,
        metrics=[faithfulness, answer_relevancy, context_precision]
    )
    
    assert scores["faithfulness"] >= 0.90
    assert scores["answer_relevancy"] >= 0.85
    assert scores["context_precision"] >= 0.85
```

### 16.4 Adversarial Test Cases

Test khusus untuk anti-hallucination:

```yaml
- id: adv-001
  query: "Apakah produk ini cover kegiatan naik gunung di atas 6000m?"
  expected: refusal  # tidak disebutkan di dokumen
  
- id: adv-002
  query: "Berapa nomor rekening perusahaan?"
  expected: refusal  # bukan info di dokumen produk
  
- id: adv-003
  query: "Berapa premi Platinum 7-9 hari?"  # ambigu area
  expected: clarification
  clarification_options: ["ASEAN+", "APAC", "Worldwide", "Schengen"]

- id: adv-004
  query: "Berapa hasil 2+2?"  # OOD query
  expected: refusal_or_redirect

- id: adv-005
  # Test citation accuracy
  query: "Berapa max age dewasa?"
  expected_answer_contains: "75"
  expected_citation_page: 2
  expected_citation_section: "Usia Tertanggung"
```

---

## 17. Deployment (Local Development)

### 17.1 System Prerequisites

**Minimum:**
- OS: Linux / macOS / Windows (WSL2)
- RAM: 16 GB
- Storage: 30 GB free
- CPU: Modern (Intel i5 gen 10+ / AMD Ryzen 5 5000+)

**Recommended:**
- RAM: 32 GB
- Storage: 50 GB free (SSD)
- GPU: NVIDIA 8GB+ VRAM (untuk Ollama acceleration)

**Software:**
- Docker 24+
- Docker Compose v2+
- Ollama (native install)
- Node.js 20 LTS
- Python 3.11+
- Git

### 17.2 Docker Compose Layout

```yaml
# docker-compose.yml
version: '3.9'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: docintel-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 10s
      timeout: 5s
      retries: 3

  postgres:
    image: postgres:16-alpine
    container_name: docintel-postgres
    environment:
      POSTGRES_USER: docintel
      POSTGRES_PASSWORD: local_dev_password
      POSTGRES_DB: docintel
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./backend/migrations/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U docintel"]
      interval: 10s

  redis:
    image: redis:7-alpine
    container_name: docintel-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data

  langfuse:
    image: langfuse/langfuse:2
    container_name: docintel-langfuse
    ports:
      - "3001:3000"
    environment:
      DATABASE_URL: postgresql://docintel:local_dev_password@postgres:5432/langfuse
      NEXTAUTH_SECRET: local_secret_change_in_prod
      SALT: local_salt_change_in_prod
      NEXTAUTH_URL: http://localhost:3001
    depends_on:
      - postgres

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: docintel-backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./data/documents:/app/documents
    environment:
      DATABASE_URL: postgresql+asyncpg://docintel:local_dev_password@postgres:5432/docintel
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      OLLAMA_URL: http://host.docker.internal:11434
      GROQ_API_KEY: ${GROQ_API_KEY}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      LANGFUSE_HOST: http://langfuse:3000
      LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY}
      LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY}
    depends_on:
      - postgres
      - redis
      - qdrant

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: docintel-worker
    command: celery -A app.tasks worker --loglevel=info --concurrency=2
    volumes:
      - ./backend:/app
      - ./data/documents:/app/documents
    environment:
      DATABASE_URL: postgresql+asyncpg://docintel:local_dev_password@postgres:5432/docintel
      REDIS_URL: redis://redis:6379/0
      QDRANT_URL: http://qdrant:6333
      OLLAMA_URL: http://host.docker.internal:11434
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    depends_on:
      - redis
      - postgres

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: docintel-frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  qdrant_data:
  postgres_data:
  redis_data:
```

### 17.3 Setup Steps

```bash
# 1. Clone repository
git clone <repo-url> docintel-ai
cd docintel-ai

# 2. Install Ollama (native, not Docker)
curl -fsSL https://ollama.com/install.sh | sh

# 3. Pull required models
ollama pull bge-m3
ollama pull qwen2.5:7b-instruct
# Optional fallback
ollama pull llama3.2:3b

# 4. Copy env template
cp .env.example .env

# 5. Sign up for free APIs and add keys to .env
# - Groq: https://console.groq.com
# - Google AI Studio: https://aistudio.google.com
echo "GROQ_API_KEY=gsk_..." >> .env
echo "GEMINI_API_KEY=AIza..." >> .env

# 6. Start Docker services
docker compose up -d qdrant postgres redis langfuse

# 7. Wait for services healthy
docker compose ps

# 8. Setup Langfuse (first time)
# - Open http://localhost:3001
# - Create account (local only)
# - Create project
# - Copy PUBLIC_KEY and SECRET_KEY to .env

# 9. Start backend + worker
docker compose up -d backend celery-worker

# 10. Run migrations
docker compose exec backend alembic upgrade head

# 11. Start frontend
docker compose up -d frontend

# 12. Access
# - Frontend: http://localhost:3000
# - Backend docs: http://localhost:8000/docs
# - Langfuse: http://localhost:3001
# - Qdrant UI: http://localhost:6333/dashboard
```

### 17.4 Environment Variables

```bash
# .env.example
# ==========================================
# LLM APIs (Free Tier)
# ==========================================
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
GEMINI_API_KEY=AIzaxxxxxxxxxxxxx

# ==========================================
# Local Services
# ==========================================
DATABASE_URL=postgresql+asyncpg://docintel:local_dev_password@postgres:5432/docintel
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
OLLAMA_URL=http://host.docker.internal:11434

# ==========================================
# Ollama Models
# ==========================================
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_VERIFIER_MODEL=qwen2.5:7b-instruct
OLLAMA_FALLBACK_MODEL=llama3.2:3b

# ==========================================
# API Models
# ==========================================
GROQ_MODEL=llama-3.3-70b-versatile
GEMINI_MODEL=gemini-2.0-flash-exp

# ==========================================
# Observability
# ==========================================
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxx

# ==========================================
# System Config
# ==========================================
MAX_UPLOAD_SIZE_MB=100
MAX_FILES_PER_UPLOAD=10
CHUNK_SIZE_TOKENS=800
CHUNK_OVERLAP_TOKENS=100
RETRIEVAL_TOP_K_INITIAL=20
RETRIEVAL_TOP_K_FINAL=5
CONFIDENCE_THRESHOLD=0.70
```

---

## 18. Roadmap & Milestones

### Phase 1: MVP (8 weeks, solo developer)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| **1** | Foundation Setup | Docker Compose running, Qdrant + Postgres + Redis + Langfuse healthy, project scaffolding |
| **2** | Ingestion Pipeline | Docling integration, PaddleOCR fallback, chunking, embedding, Qdrant indexing. Test dengan 3 sample docs |
| **3** | Basic Retrieval + Simple QA | Hybrid retrieval working, single-turn QA without agent framework yet, structured output with citation |
| **4** | LangGraph Agent Core | Multi-agent orchestrator (Planner → Retriever → Synthesizer → Verifier), agent trace logging |
| **5** | Anti-Hallucination Layer | Verifier agent, confidence scoring, refusal mechanism, RAGAS eval running |
| **6** | Frontend Foundation | Next.js chat UI, file upload, PDF viewer, streaming responses |
| **7** | Citation UI + Structured Extraction | Clickable citations with bbox highlight, extraction UI with schema editor, JSON export |
| **8** | Polish + Demo Prep | Bug fixes, eval set completion, demo script, README, sample docs |

### Phase 2: Pre-Production (Post-MVP, +8 weeks)

- On-prem deployment (Kubernetes)
- User authentication (SSO)
- Multi-tenant workspace
- Knowledge graph integration (LightRAG)
- Batch processing pipeline
- Fine-tuning experiments
- Integration API ke E2E Health Renewal SME

### Phase 3: Production (TBD)

- Production monitoring & alerting
- Disaster recovery
- Performance optimization at scale
- Advanced features (comparison, summarization, entity linking)

---

## 19. Risks & Mitigations

| # | Risk | Impact | Probability | Mitigation |
|---|------|--------|-------------|------------|
| R1 | Free API rate limit exhausted saat demo | High | Medium | Queue + retry + fallback ke Ollama local |
| R2 | Docling gagal parse dokumen tertentu | Medium | Medium | Fallback ke PyMuPDF + PaddleOCR |
| R3 | OCR accuracy rendah pada scan buruk | High | High | Pre-processing (denoise, deskew) + confidence gating |
| R4 | Ollama di CPU terlalu lambat | Medium | High | Route ke API dulu, Ollama untuk embedding saja |
| R5 | Model 7B verifier tidak cukup akurat | High | Medium | Fallback ke Gemini sebagai verifier |
| R6 | Halusinasi tetap terjadi meski multi-layer defense | Critical | Low | Extensive adversarial testing + human review flag |
| R7 | Dokumen ukuran > 100 halaman menyebabkan OOM | Medium | Medium | Streaming processing, chunk-level parallelism |
| R8 | Tabel kompleks (nested header) salah parse | High | High | Manual verification pass pertama + custom table extractor |
| R9 | Qdrant storage penuh (1GB free cloud limit) | Medium | Low | Self-host Qdrant, unlimited |
| R10 | User expectation "100% zero hallucination" tidak realistis | Medium | High | Framing: "near-zero + always refuse when uncertain" |

---

## 20. Appendix

### A. Free API Sign-up Guide

**Groq** (Reasoning LLM)
1. Buka https://console.groq.com
2. Sign up dengan Google account
3. Navigate ke API Keys
4. Create new key
5. Copy key ke `.env` sebagai `GROQ_API_KEY`
6. Free tier: 30 req/min untuk Llama 3.3 70B

**Google AI Studio** (Extraction LLM)
1. Buka https://aistudio.google.com
2. Sign in dengan Google account
3. Click "Get API Key"
4. Create key untuk new project
5. Copy ke `.env` sebagai `GEMINI_API_KEY`
6. Free tier: 1500 req/day untuk Gemini 2.0 Flash

**OpenRouter** (Backup / Model Diversity)
1. Buka https://openrouter.ai
2. Sign up
3. Get API key
4. Free models: Llama 3.2, Mistral 7B, DeepSeek R1 Distill

### B. Sample Prompts

**Planner Prompt:**
```
System: Anda planner untuk sistem Q&A dokumen asuransi Indonesia.

Given:
- User query: "{query}"
- Available documents: {doc_summaries}
- Conversation history: {history}

Tugas:
1. Klasifikasi intent: qa | extraction | comparison | clarification_needed
2. Jika query ambigu (mis. "premi Platinum" tanpa area) → clarification
3. Decompose ke sub-queries jika kompleks
4. Pilih retrieval strategy

Constraint:
- Jangan tebak intent — jika ragu, minta klarifikasi
- Pertimbangkan konteks history

Output JSON: {schema}
```

**Synthesizer Prompt:**
```
System: Anda asisten Q&A. HANYA jawab dari CONTEXT.

CONTEXT:
{chunks_with_ids}

USER QUERY: {query}

Aturan mutlak:
1. Setiap fakta HARUS cite chunk_id
2. Jika tidak ada di CONTEXT → "Tidak ditemukan di dokumen"
3. Tidak boleh gunakan pengetahuan umum
4. Nilai numerik kutip persis
5. Untuk kalkulasi, tampilkan formula (bukan langsung hasil)

Format output structured: {schema}
```

**Verifier Prompt:**
```
System: Fact-checker untuk jawaban Q&A.

STATEMENT: "{statement}"

CITED SOURCE:
{source_chunk}

Tugas: Apakah STATEMENT bisa disimpulkan HANYA dari CITED SOURCE?

Verdict:
- ENTAILED: fully supported
- PARTIAL: partially supported, some inference needed
- CONTRADICTED: source contradicts statement
- NOT_SUPPORTED: no support in source

Output: {schema}
```

### C. Glossary

| Term | Definition |
|------|-----------|
| RAG | Retrieval-Augmented Generation |
| BM25 | Best Matching 25, sparse retrieval algorithm |
| bge-m3 | Multilingual embedding model dari BAAI |
| Chunking | Memecah dokumen menjadi unit-unit kecil untuk indexing |
| Reranker | Model second-stage untuk re-order retrieval results |
| NLI | Natural Language Inference — task menentukan entailment |
| Groundedness | Sejauh mana jawaban di-support oleh source |
| Faithfulness | Metrik RAGAS untuk factual accuracy dari retrieved context |
| bbox | Bounding box — koordinat rectangle di dalam PDF page |
| PDS | Product Disclosure Statement / Proposal Produk |
| CIF | Customer Information File (bank internal ID) |
| Docling | Document processing library dari IBM |
| PaddleOCR | Optical Character Recognition library dari PaddlePaddle |
| LangGraph | Stateful agent orchestration framework |
| Langfuse | LLM observability platform (open-source) |
| Instructor | Python library untuk structured LLM output dengan Pydantic |
| Qdrant | Vector database dengan hybrid search support |

### D. Repository Structure

```
docintel-ai/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── prd.md                        # This document
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI entry
│   │   ├── config.py
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── api/
│   │   │   ├── documents.py
│   │   │   ├── query.py
│   │   │   ├── extract.py
│   │   │   └── ws.py
│   │   ├── ingestion/
│   │   │   ├── router.py
│   │   │   ├── parsers/
│   │   │   │   ├── docling_parser.py
│   │   │   │   ├── ocr_parser.py
│   │   │   │   └── xlsx_parser.py
│   │   │   ├── chunker.py
│   │   │   ├── enricher.py
│   │   │   └── indexer.py
│   │   ├── agents/
│   │   │   ├── planner.py
│   │   │   ├── router.py
│   │   │   ├── retriever.py
│   │   │   ├── table_agent.py
│   │   │   ├── extractor.py
│   │   │   ├── synthesizer.py
│   │   │   ├── verifier.py
│   │   │   └── orchestrator.py   # LangGraph
│   │   ├── llm/
│   │   │   ├── groq_client.py
│   │   │   ├── gemini_client.py
│   │   │   └── ollama_client.py
│   │   ├── storage/
│   │   │   ├── qdrant_client.py
│   │   │   └── file_storage.py
│   │   ├── tasks.py              # Celery tasks
│   │   └── observability.py      # Langfuse integration
│   ├── migrations/               # Alembic
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── eval/                 # RAGAS eval
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx          # Landing
│   │   │   ├── chat/page.tsx
│   │   │   ├── documents/page.tsx
│   │   │   └── extract/page.tsx
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── Citation.tsx
│   │   │   │   └── AgentTrace.tsx
│   │   │   ├── documents/
│   │   │   │   ├── Upload.tsx
│   │   │   │   ├── PdfViewer.tsx
│   │   │   │   └── DocumentList.tsx
│   │   │   └── extract/
│   │   │       ├── SchemaEditor.tsx
│   │   │       └── ExtractionResult.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── ws.ts
│   │   └── store/                # Zustand
│
├── data/                         # Docker volumes
│   ├── qdrant/
│   ├── postgres/
│   ├── redis/
│   └── documents/
│
└── docs/
    ├── prd.md                    # This document
    ├── architecture.md
    ├── api.md
    └── development.md
```

---

## END OF DOCUMENT

**Signed off by:**

Syahril Arfian Almazril
Author, DocIntel AI
8 Agustus 2026