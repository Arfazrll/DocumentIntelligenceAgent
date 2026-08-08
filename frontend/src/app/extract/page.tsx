'use client';

import { useState, useEffect } from 'react';
import {
  FileText,
  Brain,
  Loader2,
  Download,
  ChevronRight,
  ChevronDown,
  MessageSquare,
  Table as TableIcon,
  CheckCircle2,
  AlertCircle,
  Play,
  Copy,
} from 'lucide-react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const PREBUILT_SCHEMAS: Record<string, string> = {
  insurance_product: 'Insurance Policy & Product Schema (PDS)',
};

export default function ExtractPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [schemaType, setSchemaType] = useState('insurance_product');
  const [isExtracting, setIsExtracting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_URL}/api/documents`);
      const data = await res.json();
      setDocuments(data.filter((d: any) => d.status === 'INDEXED' || d.status === 'COMPLETED'));
    } catch (e) {
      console.error('Failed to fetch documents:', e);
    }
  };

  const runExtraction = async () => {
    if (!selectedDocId) return;
    setIsExtracting(true);
    setResult(null);

    try {
      const res = await fetch(`${API_URL}/api/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: selectedDocId,
          schema_type: schemaType,
        }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error('Extraction failed:', e);
      setResult({ status: 'FAILED', error_message: 'Connection failed to backend' });
    } finally {
      setIsExtracting(false);
    }
  };

  const exportJSON = () => {
    if (!result?.result) return;
    const blob = new Blob([JSON.stringify(result.result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extraction_${selectedDocId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const toggleExpand = (key: string) => {
    setExpandedKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const renderValue = (key: string, value: any, depth: number = 0): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-zinc-600 italic">null</span>;
    }

    if (typeof value === 'object' && value.value !== undefined && value.confidence !== undefined) {
      return (
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <span className="text-zinc-200 font-medium">{JSON.stringify(value.value)}</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono-code bg-indigo-950/60 text-indigo-300 border border-indigo-800/50">
            {(value.confidence * 100).toFixed(0)}% Conf
          </span>
          {value.citation && (
            <span className="text-[10px] font-mono-code text-zinc-500">
              Hal {value.citation.page_number}
            </span>
          )}
        </div>
      );
    }

    if (Array.isArray(value)) {
      const isExpanded = expandedKeys.has(key);
      return (
        <div>
          <button onClick={() => toggleExpand(key)} className="flex items-center gap-1 text-zinc-400 hover:text-zinc-200 text-xs">
            {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-mono-code">Array [{value.length}]</span>
          </button>
          {isExpanded && (
            <div className="ml-4 mt-1 space-y-1.5 border-l border-zinc-800 pl-3">
              {value.map((item, i) => (
                <div key={i}>{renderValue(`${key}.${i}`, item, depth + 1)}</div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (typeof value === 'object') {
      const isExpanded = expandedKeys.has(key);
      return (
        <div>
          <button onClick={() => toggleExpand(key)} className="flex items-center gap-1 text-zinc-400 hover:text-zinc-200 text-xs">
            {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span className="font-mono-code">Object {`{${Object.keys(value).length}}`}</span>
          </button>
          {isExpanded && (
            <div className="ml-4 mt-1 space-y-1.5 border-l border-zinc-800 pl-3">
              {Object.entries(value).map(([k, v]) => (
                <div key={k} className="flex gap-2 items-start">
                  <span className="text-indigo-400 text-xs font-mono-code">{k}:</span>
                  {renderValue(`${key}.${k}`, v, depth + 1)}
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    return <span className="text-zinc-300 text-xs">{JSON.stringify(value)}</span>;
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-zinc-800/80 bg-[#09090b]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                <Brain className="w-4 h-4" />
              </div>
              <span className="font-semibold text-zinc-100 tracking-tight">DocIntel AI</span>
            </Link>
            <span className="text-zinc-700">/</span>
            <h1 className="text-xs font-mono-code uppercase tracking-wider text-zinc-400 font-medium">
              Structured Extraction Studio
            </h1>
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
          </nav>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8 w-full">
        {/* Extraction Config Box */}
        <div className="p-6 rounded-lg bg-[#121215] border border-zinc-800 mb-8">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-zinc-800">
            <TableIcon className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-zinc-100">Konfigurasi Structured Extraction</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="text-[11px] font-mono-code uppercase tracking-wider text-zinc-400 font-medium">Pilih Dokumen</label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="w-full mt-1.5 px-3 py-2 rounded bg-zinc-950 border border-zinc-800 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">Pilih dokumen...</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>{doc.filename}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] font-mono-code uppercase tracking-wider text-zinc-400 font-medium">Target Schema</label>
              <select
                value={schemaType}
                onChange={(e) => setSchemaType(e.target.value)}
                className="w-full mt-1.5 px-3 py-2 rounded bg-zinc-950 border border-zinc-800 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500"
              >
                {Object.entries(PREBUILT_SCHEMAS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={runExtraction}
                disabled={!selectedDocId || isExtracting}
                className="w-full px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition-all shadow-sm flex items-center justify-center gap-2"
              >
                {isExtracting ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Running Extraction...</>
                ) : (
                  <><Play className="w-4 h-4" /> Run Extraction</>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Results Studio */}
        {result && (
          <div className="p-6 rounded-lg bg-[#121215] border border-zinc-800">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-semibold text-zinc-100">Hasil Ekstraksi Terstruktur</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge-status ${result.status === 'COMPLETED' ? 'badge-completed' : 'badge-error'}`}>
                  {result.status}
                </span>
                {result.result && (
                  <button
                    onClick={exportJSON}
                    className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-mono-code border border-zinc-700 transition-all flex items-center gap-1.5"
                  >
                    <Download className="w-3.5 h-3.5" /> Export JSON
                  </button>
                )}
              </div>
            </div>

            {result.error_message && (
              <div className="text-xs text-rose-400 mb-4 p-3 rounded bg-rose-950/40 border border-rose-800/50 font-mono-code">
                {result.error_message}
              </div>
            )}

            {result.result && (
              <div className="p-4 rounded bg-zinc-950 border border-zinc-800/80 font-mono-code text-xs space-y-2 max-h-[550px] overflow-y-auto">
                {Object.entries(result.result).map(([key, value]) => (
                  <div key={key} className="flex gap-3 items-start border-b border-zinc-900/80 pb-2 last:border-0">
                    <span className="text-indigo-400 font-semibold min-w-[220px]">{key}:</span>
                    <div className="flex-1">{renderValue(key, value)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
