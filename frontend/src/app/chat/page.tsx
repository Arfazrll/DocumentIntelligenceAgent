'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Send,
  Loader2,
  FileText,
  ChevronRight,
  Brain,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Activity,
  Layers,
  Search,
  BookOpen,
} from 'lucide-react';
import Link from 'next/link';

type Citation = {
  doc_id: string;
  doc_name: string;
  page_number: number;
  chunk_id: string;
  section_path?: string;
  text_snippet: string;
  bbox?: { x0: number; y0: number; x1: number; y1: number };
  relevance_score: number;
};

type AgentStep = {
  agent: string;
  action: string;
  result_summary: string;
  duration_ms: number;
};

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  confidence?: { score: number; level: 'high' | 'medium' | 'low' };
  trace?: AgentStep[];
  created_at: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function ChatContent() {
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get('doc_id');
  const initialQuery = searchParams.get('q');

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showTrace, setShowTrace] = useState(false);
  const [activeTrace, setActiveTrace] = useState<AgentStep[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_URL}/api/documents`);
      const data = await res.json();
      const readyDocs = data.filter((d: any) => d.status === 'INDEXED' || d.status === 'COMPLETED');
      setDocuments(readyDocs);

      if (initialDocId) {
        setSelectedDocIds([initialDocId]);
      } else if (readyDocs.length > 0 && selectedDocIds.length === 0) {
        setSelectedDocIds([readyDocs[0].id]);
      }

      if (initialQuery && !input) {
        setInput(decodeURIComponent(initialQuery));
      }
    } catch (e) {
      console.error('Failed to fetch documents:', e);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const queryText = input;
    const docIdsToSend = selectedDocIds.length > 0 ? selectedDocIds : documents.map(d => d.id);

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: queryText,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setActiveTrace([]);

    try {
      const res = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          document_ids: docIdsToSend,
          query: queryText,
        }),
      });

      const data = await res.json();
      if (!sessionId && data.session_id) setSessionId(data.session_id);

      const assistantMsg: Message = {
        id: data.message_id || Date.now().toString(),
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
        confidence: data.confidence,
        trace: data.trace?.steps,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMsg]);
      if (data.trace?.steps) setActiveTrace(data.trace.steps);
    } catch (e) {
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Terjadi kesalahan saat menghubungi server backend. Pastikan server FastAPI berjalan.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceBadge = (level: string, score: number) => {
    const scorePct = (score * 100).toFixed(0);
    switch (level) {
      case 'high':
        return (
          <span className="badge-status badge-completed">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            Verified High Confidence ({scorePct}%)
          </span>
        );
      case 'medium':
        return (
          <span className="badge-status badge-pending">
            <AlertCircle className="w-3 h-3 text-amber-400" />
            Medium Confidence ({scorePct}%)
          </span>
        );
      case 'low':
        return (
          <span className="badge-status badge-error">
            <XCircle className="w-3 h-3 text-rose-400" />
            Low Confidence ({scorePct}%)
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-[#09090b] text-zinc-100 font-sans overflow-hidden">
      {/* Sidebar: Document Selection */}
      <aside className="w-80 bg-[#121215] border-r border-zinc-800 flex flex-col shrink-0">
        <div className="p-4 border-b border-zinc-800">
          <Link href="/" className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Brain className="w-4 h-4" />
            </div>
            <span className="font-semibold text-zinc-100 tracking-tight">DocIntel AI</span>
          </Link>
          <div className="flex items-center justify-between">
            <h2 className="text-[11px] font-mono-code uppercase tracking-wider text-zinc-400 font-semibold">
              Select Active Documents ({documents.length})
            </h2>
            <Link href="/documents" className="text-[11px] font-mono-code text-indigo-400 hover:text-indigo-300">
              + Manage
            </Link>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {documents.length === 0 ? (
            <div className="text-center text-zinc-500 text-xs py-10 px-4">
              <FileText className="w-8 h-8 mx-auto mb-2 text-zinc-600 opacity-60" />
              <p>Belum ada dokumen terindeks.</p>
              <Link href="/documents" className="text-indigo-400 hover:underline text-xs mt-2 inline-block font-mono-code">
                Upload Dokumen →
              </Link>
            </div>
          ) : (
            documents.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.id);
              return (
                <button
                  key={doc.id}
                  onClick={() => {
                    setSelectedDocIds(prev =>
                      prev.includes(doc.id)
                        ? prev.filter(id => id !== doc.id)
                        : [...prev, doc.id]
                    );
                  }}
                  className={`w-full text-left p-3 rounded-md border transition-all text-xs flex items-center justify-between ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/60 text-white'
                      : 'bg-zinc-900/40 border-zinc-800/80 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <FileText className={`w-4 h-4 shrink-0 ${isSelected ? 'text-indigo-400' : 'text-zinc-500'}`} />
                    <span className="truncate font-medium">{doc.filename}</span>
                  </div>
                  <span className="text-[10px] font-mono-code text-zinc-500 shrink-0">
                    {doc.file_type.toUpperCase()}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </aside>

      {/* Main Chat Panel */}
      <main className="flex-1 flex flex-col bg-[#09090b] overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-zinc-800 px-6 flex items-center justify-between bg-[#121215]/80 backdrop-blur-md shrink-0">
          <div>
            <h1 className="text-sm font-semibold text-zinc-100">Multi-Agent RAG Chat Studio</h1>
            <p className="text-xs font-mono-code text-zinc-400 mt-0.5">
              {selectedDocIds.length > 0
                ? `Active Context: ${selectedDocIds.length} Dokumen Dicentang`
                : 'Pilih dokumen di sidebar untuk mempersempit konteks'}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTrace(!showTrace)}
              className={`px-3 py-1.5 rounded text-xs font-mono-code transition-all border flex items-center gap-1.5 ${
                showTrace
                  ? 'bg-indigo-950/60 text-indigo-300 border-indigo-700'
                  : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Agent Trace {activeTrace.length > 0 ? `(${activeTrace.length})` : ''}
            </button>
          </div>
        </header>

        {/* Content Area (Messages + Agent Trace Drawer) */}
        <div className="flex-1 flex overflow-hidden">
          {/* Message Thread */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-zinc-500 max-w-md mx-auto text-center">
                  <div className="w-12 h-12 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 mb-4">
                    <BookOpen className="w-6 h-6" />
                  </div>
                  <h2 className="text-sm font-semibold text-zinc-200 mb-1">Tanya Jawab Dokumen Terstruktur</h2>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Ketik pertanyaan mengenai isi dokumen. Setiap jawaban dilengkapi verifikasi anti-halusinasi 5-layer dan kutipan halaman resmi.
                  </p>
                </div>
              )}

              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`animate-fade-in flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg p-4 text-xs sm:text-sm leading-relaxed border ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white border-indigo-500 font-sans'
                        : 'bg-[#121215] text-zinc-200 border-zinc-800'
                    }`}
                  >
                    <p className="whitespace-pre-wrap font-sans">{msg.content}</p>

                    {/* Confidence Rating */}
                    {msg.confidence && (
                      <div className="mt-3 pt-2.5 border-t border-zinc-800 flex items-center justify-between">
                        {getConfidenceBadge(msg.confidence.level, msg.confidence.score)}
                      </div>
                    )}

                    {/* Citations Snippets */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-zinc-800/80 space-y-2">
                        <div className="text-[11px] font-mono-code text-zinc-400 uppercase tracking-wider font-semibold">
                          Sumber Kutipan ({msg.citations.length} Sources):
                        </div>
                        <div className="grid gap-2">
                          {msg.citations.map((cit, i) => (
                            <div key={i} className="p-2.5 rounded bg-zinc-950/80 border border-zinc-800 text-xs">
                              <div className="flex items-center justify-between text-[11px] font-mono-code text-indigo-400 mb-1">
                                <span>[{i + 1}] Halaman {cit.page_number}</span>
                                <span>Relevansi: {(cit.relevance_score * 100).toFixed(0)}%</span>
                              </div>
                              <p className="text-zinc-400 text-xs font-sans line-clamp-2 leading-relaxed">
                                {cit.text_snippet}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex items-center gap-3 p-4 rounded-lg bg-[#121215] border border-zinc-800 max-w-sm">
                  <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                  <span className="text-xs font-mono-code text-zinc-400">Multi-Agent Planner & Retrieval running...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input Box */}
            <div className="p-4 border-t border-zinc-800 bg-[#121215]">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
                className="flex items-center gap-3 max-w-4xl mx-auto"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ketik pertanyaan Anda tentang dokumen..."
                  className="flex-1 px-4 py-2.5 rounded bg-zinc-950 border border-zinc-800 text-xs sm:text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="px-5 py-2.5 rounded bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition-all shadow-sm flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  Kirim
                </button>
              </form>
            </div>
          </div>

          {/* Agent Trace Drawer */}
          {showTrace && (
            <div className="w-80 border-l border-zinc-800 bg-[#121215] p-4 overflow-y-auto flex flex-col gap-4 shrink-0">
              <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-xs font-mono-code font-semibold uppercase tracking-wider text-zinc-200">
                    Agent Trajectory
                  </h3>
                </div>
                <button
                  onClick={() => setShowTrace(false)}
                  className="text-zinc-500 hover:text-zinc-300 text-xs font-mono-code"
                >
                  Close
                </button>
              </div>

              {activeTrace.length === 0 ? (
                <div className="text-xs text-zinc-500 text-center py-8">
                  Jejak eksekusi agen akan muncul setelah pertanyaan diajukan.
                </div>
              ) : (
                <div className="space-y-3">
                  {activeTrace.map((step, i) => (
                    <div key={i} className="p-3 rounded bg-zinc-950 border border-zinc-800 text-xs">
                      <div className="flex items-center justify-between text-[10px] font-mono-code mb-1">
                        <span className="font-semibold text-indigo-400 uppercase">{step.agent}</span>
                        <span className="text-zinc-500">{step.duration_ms}ms</span>
                      </div>
                      <p className="text-zinc-300 font-medium mb-1">{step.action}</p>
                      <p className="text-[11px] text-zinc-400 font-sans leading-normal">{step.result_summary}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="h-screen bg-[#09090b] flex items-center justify-center text-xs text-zinc-500">Loading Chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}
