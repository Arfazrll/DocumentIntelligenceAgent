'use client';

import Link from 'next/link';
import {
  FileText,
  MessageSquare,
  Table,
  Upload,
  ShieldCheck,
  Zap,
  Brain,
  Activity,
  Layers,
  ArrowRight,
  Database,
  CheckCircle2,
  Lock,
  Search,
} from 'lucide-react';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Header */}
      <header className="border-b border-zinc-800/80 bg-[#09090b]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Brain className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-zinc-100 tracking-tight">DocIntel AI</h1>
                <span className="px-2 py-0.5 text-[10px] font-mono-code font-medium bg-zinc-800 text-zinc-400 border border-zinc-700 rounded">
                  v1.0.0-PROD
                </span>
              </div>
              <p className="text-[11px] font-mono-code text-zinc-400">Enterprise Document Intelligence Platform</p>
            </div>
          </div>
          <nav className="flex items-center gap-2">
            <Link
              href="/chat"
              className="px-3.5 py-1.5 rounded-md text-xs font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 border border-transparent hover:border-zinc-700 transition-all flex items-center gap-2"
            >
              <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
              Chat Q&A
            </Link>
            <Link
              href="/documents"
              className="px-3.5 py-1.5 rounded-md text-xs font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 border border-transparent hover:border-zinc-700 transition-all flex items-center gap-2"
            >
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              Documents & Key Extractions
            </Link>
            <Link
              href="/extract"
              className="px-3.5 py-1.5 rounded-md text-xs font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 border border-transparent hover:border-zinc-700 transition-all flex items-center gap-2"
            >
              <Table className="w-3.5 h-3.5 text-indigo-400" />
              Structured Extract
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-16 pb-14 w-full">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-zinc-900 border border-zinc-800 text-[11px] font-mono-code text-zinc-300 mb-6">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Industrial Multi-Agent Verification Architecture</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white mb-5 leading-tight">
            High-Precision Document Analysis & Automated Extractions
          </h1>
          <p className="text-sm sm:text-base text-zinc-400 leading-relaxed mb-8">
            Unggah dokumen (PDF, DOCX, XLSX). Sistem secara otomatis mengekstrak bagian-bagian penting (Cakupan, Batas Pertanggungan, Pengecualian, Batas Waktu Klaim, dan Tabel Data) dan menyediakan fitur Chat Q&A berbasis Local AI.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/documents"
              className="px-5 py-2.5 rounded-md bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs tracking-wide transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Upload & Extract Highlights
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link
              href="/chat"
              className="px-5 py-2.5 rounded-md bg-zinc-900 hover:bg-zinc-800 text-zinc-200 font-medium text-xs border border-zinc-700 transition-all flex items-center gap-2"
            >
              <MessageSquare className="w-4 h-4 text-zinc-400" />
              Buka Interactive Chat
            </Link>
          </div>
        </div>
      </section>

      {/* Feature Cards Grid */}
      <section className="max-w-7xl mx-auto px-6 py-8 w-full border-t border-zinc-800/60">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              icon: <FileText className="w-4 h-4 text-indigo-400" />,
              title: 'Automatic Key Extractions',
              desc: 'Ekstraksi otomatis bagian-bagian penting dokumen (Luas Pertanggungan, Pembatasan, Tabel & Prosedur Klaim).',
            },
            {
              icon: <Search className="w-4 h-4 text-indigo-400" />,
              title: 'Multi-Agent Q&A System',
              desc: 'Tanya jawab interaktif berbasis RAG dengan verifikasi otomatis 5-layer anti-halusinasi.',
            },
            {
              icon: <Table className="w-4 h-4 text-indigo-400" />,
              title: 'Structured Tables Parsing',
              desc: 'Parsing tabel dan data terstruktur menggunakan Docling layout parser + PaddleOCR.',
            },
            {
              icon: <Lock className="w-4 h-4 text-indigo-400" />,
              title: '100% Local Inference',
              desc: 'Pemrosesan data berjalan sepenuhnya secara lokal via Ollama (0 rate limit, 0 token cost).',
            },
          ].map((f, i) => (
            <div
              key={i}
              className="p-5 rounded-lg bg-[#121215] border border-zinc-800 hover:border-zinc-700 transition-all group"
            >
              <div className="w-8 h-8 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-4 group-hover:border-indigo-500/40 transition-colors">
                {f.icon}
              </div>
              <h2 className="text-sm font-semibold text-zinc-200 mb-1.5">{f.title}</h2>
              <p className="text-xs text-zinc-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Flow */}
      <section className="max-w-7xl mx-auto px-6 py-12 w-full border-t border-zinc-800/60">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xs font-mono-code tracking-wider uppercase text-zinc-400 font-medium">
              System Architecture & Workflow
            </h2>
            <p className="text-sm font-semibold text-zinc-200 mt-1">Multi-Agent Execution Trajectory</p>
          </div>
          <span className="px-2.5 py-1 rounded text-[10px] font-mono-code bg-zinc-900 border border-zinc-800 text-emerald-400">
            Active Status: Operational
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { step: '01', name: 'Planner Agent', desc: 'Query intent & strategy selection' },
            { step: '02', name: 'Router Agent', desc: 'Dynamic pipeline dispatching' },
            { step: '03', name: 'Retriever Agent', desc: 'Dense + Sparse BM25 RRF Search' },
            { step: '04', name: 'Synthesizer Agent', desc: 'Grounded response generation' },
            { step: '05', name: 'Verifier Agent', desc: 'Fact-checking & confidence evaluation' },
          ].map((agent, i) => (
            <div key={i} className="p-4 rounded bg-[#121215] border border-zinc-800">
              <span className="text-[10px] font-mono-code text-indigo-400 font-semibold">{agent.step}</span>
              <h3 className="text-xs font-semibold text-zinc-200 mt-1 mb-1">{agent.name}</h3>
              <p className="text-[11px] text-zinc-400 leading-normal">{agent.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-zinc-800/80 bg-[#09090b] py-6 text-center text-xs font-mono-code text-zinc-400">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>DocIntel AI v1.0.0 — Enterprise Document Intelligence</div>
          <div className="flex items-center gap-4 text-zinc-400">
            <span>Local Engine: Ollama</span>
            <span>Vector DB: Qdrant</span>
            <span>Broker: Redis</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
