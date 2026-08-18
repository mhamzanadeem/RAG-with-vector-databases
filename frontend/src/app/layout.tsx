import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Semantic Search",
  description:
    "RAG pipeline over a custom document set — FAISS & ChromaDB, Hugging Face embeddings.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}