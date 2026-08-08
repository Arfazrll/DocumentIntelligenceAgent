import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DocIntel AI — Document Intelligence Platform',
  description: 'Multi-agent document intelligence platform with zero-hallucination guarantee for insurance document analysis, extraction, and Q&A.',
  keywords: 'document intelligence, AI, insurance, extraction, Q&A, RAG',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" className="dark">
      <body className="min-h-screen bg-dark-950 text-dark-50 antialiased">
        {children}
      </body>
    </html>
  );
}
