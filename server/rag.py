"""
rag.py — Lightweight TF-IDF RAG retriever for KodBank chatbot.

Knowledge sources:
  1. User guide (user_guide.md) — chunked by section at startup
  2. Live news — injected via add_news_chunks() called from app.py
"""

import os
import re
import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
_GUIDE_PATH = os.path.join(os.path.dirname(__file__), '..', '.gemini',
                           'antigravity', 'brain',
                           '59fe8601-032a-4370-8e84-e6a9fb780bd3',
                           'user_guide.md')

# Fallback inline guide if the file path doesn't resolve (e.g. on Vercel)
_INLINE_GUIDE = """
# KodBank User Guide

## Chat — AI Financial Assistant
Use the chat box to ask anything finance-related. Examples: What is the difference between a mutual fund and an ETF? Explain the RSI indicator. How should I start investing? What are Bollinger Bands?

## Dashboard — Balance & Transactions
Shows your current account balance and a summary of recent activity including deposits, withdrawals, and transaction history.

## News — Financial News Feed
Displays live news articles fetched from NewsAPI across four categories: Latest News (business headlines), Bitcoin (crypto news), Gold (commodities), Stocks (stock market).

## Stock Analytics — Technical Analysis
Analyze any NSE or US-listed stock. Search by ticker symbol (e.g. TCS, INFY, AAPL, NVDA). Displays RSI, Bollinger Bands, Moving Averages (SMA50, SMA200, EMA50, EMA200), and MACD indicators with analysis text. Toggle between Candlestick and Line charts. Hover over chart for exact values.

## RSI — Relative Strength Index
Range 0-100. Above 70 means overbought (potential sell signal). Below 30 means oversold (potential buy signal). Between 30-70 is neutral.

## Bollinger Bands
Upper Band and Lower Band. Price near upper band indicates overbought territory. Price near lower band indicates oversold territory.

## Moving Averages
SMA 50 and SMA 200 are Simple Moving Averages. EMA 50 and EMA 200 are Exponential Moving Averages. Golden Cross occurs when SMA50 crosses above SMA200 (bullish signal). Death Cross occurs when SMA50 crosses below SMA200 (bearish signal).

## MACD — Moving Average Convergence Divergence
Shows MACD Line, Signal Line, and Histogram. Bullish crossover when MACD crosses above signal line. Bearish crossover when MACD crosses below signal line.

## Supported Markets
NSE India: RELIANCE, TCS, INFY, HDFCBANK, TATAMOTORS, and all major NSE-listed stocks.
US Markets: AAPL, NVDA, TSLA, MSFT, GOOGL, META, AMZN, and major NASDAQ/NYSE stocks.
"""


class RAGRetriever:
    """TF-IDF based retriever over text chunks."""

    def __init__(self):
        self._lock = threading.Lock()
        self._chunks: list[str] = []
        self._vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self._matrix = None

    def fit(self, chunks: list[str]):
        """Fit the vectorizer on a list of text chunks."""
        with self._lock:
            self._chunks = [c.strip() for c in chunks if c.strip()]
            if not self._chunks:
                return
            self._matrix = self._vectorizer.fit_transform(self._chunks)

    def add_chunks(self, new_chunks: list[str]):
        """Append new chunks and refit (used for news refresh)."""
        with self._lock:
            combined = self._chunks + [c.strip() for c in new_chunks if c.strip()]
            self._chunks = combined
            if self._chunks:
                self._matrix = self._vectorizer.fit_transform(self._chunks)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """Return top_k most relevant chunks for the query."""
        with self._lock:
            if self._matrix is None or not self._chunks:
                return []
            try:
                q_vec = self._vectorizer.transform([query])
                scores = cosine_similarity(q_vec, self._matrix).flatten()
                top_indices = np.argsort(scores)[::-1][:top_k]
                # Only return chunks with non-zero similarity
                return [self._chunks[i] for i in top_indices if scores[i] > 0.01]
            except Exception:
                return []


# ── Guide chunking ────────────────────────────────────────────────────────────

def _load_guide_text() -> str:
    """Load user guide from file, fall back to inline guide."""
    try:
        path = os.path.abspath(_GUIDE_PATH)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception:
        pass
    return _INLINE_GUIDE


def _chunk_guide(text: str) -> list[str]:
    """Split markdown guide into section chunks (split on ## headings)."""
    parts = re.split(r'\n(?=#{1,3} )', text)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # If a chunk is very long, break it into ~500 char sub-chunks
        if len(part) > 600:
            words = part.split()
            sub, buf = [], []
            for w in words:
                buf.append(w)
                if len(' '.join(buf)) > 500:
                    sub.append(' '.join(buf))
                    buf = []
            if buf:
                sub.append(' '.join(buf))
            chunks.extend(sub)
        else:
            chunks.append(part)
    return chunks


# ── News chunking ──────────────────────────────────────────────────────────────

def news_articles_to_chunks(articles: list[dict]) -> list[str]:
    """Convert news article dicts to searchable text chunks."""
    chunks = []
    for a in articles:
        title = a.get('title', '')
        desc = a.get('description', '')
        source = a.get('source', '')
        if title and title != '[Removed]':
            chunks.append(f"News from {source}: {title}. {desc}")
    return chunks


# ── Public interface ───────────────────────────────────────────────────────────

# Singleton retriever
retriever = RAGRetriever()


def build_knowledge_base() -> RAGRetriever:
    """
    Load the user guide, chunk it, and fit the retriever.
    Called once at Flask startup.
    Returns the retriever so tests can call retrieve() on it directly.
    """
    guide_text = _load_guide_text()
    chunks = _chunk_guide(guide_text)
    retriever.fit(chunks)
    print(f"[RAG] Knowledge base built: {len(chunks)} guide chunks loaded.")
    return retriever


def refresh_news(articles: list[dict]):
    """
    Called from app.py after a news fetch to add fresh articles into the retriever.
    Re-fits only the news portion by rebuilding from scratch.
    """
    # Re-load guide chunks first so we don't lose them
    guide_text = _load_guide_text()
    guide_chunks = _chunk_guide(guide_text)
    news_chunks = news_articles_to_chunks(articles)
    all_chunks = guide_chunks + news_chunks
    retriever.fit(all_chunks)
    print(f"[RAG] Refreshed with {len(news_chunks)} news chunks. Total: {len(all_chunks)}.")


def get_context(query: str, top_k: int = 3) -> str:
    """
    Retrieve relevant context for a user query.
    Returns a formatted string to inject into the system prompt.
    """
    chunks = retriever.retrieve(query, top_k=top_k)
    if not chunks:
        return ""
    return "\n\n---\nRelevant context from KodBank knowledge base:\n" + \
           "\n\n".join(f"• {c}" for c in chunks)
