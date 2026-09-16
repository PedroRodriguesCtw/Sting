from __future__ import annotations

import json
import mimetypes
import re
import ssl
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from pypdf import PdfReader


ROOT_DIR = Path(__file__).resolve().parent
DOCS_DIR = ROOT_DIR / "docs"
KB_PATH = ROOT_DIR / "docs" / "knowledge-base.json"


@dataclass(frozen=True)
class KnowledgeDocument:
    id: str
    title: str
    url: str
    summary: str
    facts: list[str]
    keywords: list[str]
    extracted_text: str = ""


def load_knowledge_base() -> dict[str, Any]:
    with KB_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    documents = [
        KnowledgeDocument(
            id=document["id"],
            title=document["title"],
            url=document["url"],
            summary=document["summary"],
            facts=document["facts"],
            keywords=document["keywords"],
            extracted_text=document.get("extractedText", ""),
        )
        for document in payload["documents"]
    ]
    payload["documents"] = documents
    return payload


KNOWLEDGE_BASE = load_knowledge_base()
TLS_CONTEXT = ssl.create_default_context()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def score_document(question: str, document: KnowledgeDocument) -> int:
    haystack = normalize(question)
    score = 0

    for keyword in document.keywords:
        normalized_keyword = normalize(keyword)
        if normalized_keyword and normalized_keyword in haystack:
            score += max(3, len(normalized_keyword.split()))

    for fact in document.facts:
        tokens = re.findall(r"[a-z0-9\-\+]+", fact.lower())
        shared = {token for token in tokens if len(token) > 3 and token in haystack}
        score += len(shared)

    if document.extracted_text:
        extracted_tokens = re.findall(r"[a-z0-9\-\+]+", document.extracted_text.lower())
        shared = {token for token in extracted_tokens if len(token) > 4 and token in haystack}
        score += min(len(shared), 12)

    return score


def fetch_pdf_text(url: str) -> str | None:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
        },
    )

    try:
        with urlopen(request, timeout=12, context=TLS_CONTEXT) as response:
            content_type = response.headers.get("Content-Type", "")
            payload = response.read()
    except Exception:
        return None

    if not payload or ("pdf" not in content_type.lower() and not payload.startswith(b"%PDF")):
        return None

    try:
        reader = PdfReader(BytesIO(payload))
        pages = []
        for page in reader.pages[:8]:
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(page_text.strip())
        return normalize(" ".join(pages))
    except Exception:
        return None


def enrich_documents_from_remote_pdfs() -> None:
    documents: list[KnowledgeDocument] = []
    for document in KNOWLEDGE_BASE["documents"]:
        extracted_text = fetch_pdf_text(document.url)
        documents.append(
            KnowledgeDocument(
                id=document.id,
                title=document.title,
                url=document.url,
                summary=document.summary,
                facts=document.facts,
                keywords=document.keywords,
                extracted_text=extracted_text or document.extracted_text,
            )
        )
    KNOWLEDGE_BASE["documents"] = documents


def answer_question(question: str) -> dict[str, Any]:
    normalized_question = normalize(question)
    if not normalized_question:
        return {
            "answer": "Ask me about Team Sting, the squad, VideoAR, or SHUD.",
            "sources": [],
        }

    documents = KNOWLEDGE_BASE["documents"]
    ranked = sorted(
        ((score_document(normalized_question, document), document) for document in documents),
        key=lambda item: item[0],
        reverse=True,
    )
    matched = [document for score, document in ranked if score > 0][:2]

    generic_answers = [
        (
            re.compile(r"^(hi|hello|hey|ola|olá|good morning|good afternoon|good evening)\b"),
            "Hello! Ask me about Team Sting, members, unit, VideoAR, or SHUD.",
        ),
        (
            re.compile(r"\b(team|squad|who.*team|what.*team)\b"),
            "STING is the MyJourney team focused on augmented driving experiences and guidance-driven display concepts.",
        ),
        (
            re.compile(r"\b(member|members|people|integrant)\b"),
            "The current STING squad includes Pedro SK, Frederico RKD, Cleyde RKD, and Tiago RKD.",
        ),
        (
            re.compile(r"\b(unit|myjourney|organization|org)\b"),
            "The team belongs to the MyJourney unit.",
        ),
        (
            re.compile(r"\b(link|pulsar|access|internal)\b"),
            "The Pulsar and SharePoint links are intended for internal access and depend on each user's permissions.",
        ),
    ]

    if matched:
        answer_parts = []
        sources = []
        for document in matched:
            answer_parts.append(document.summary)
            answer_parts.extend(document.facts[:3])
            sources.append({"title": document.title, "url": document.url})
        return {"answer": " ".join(answer_parts), "sources": sources}

    for pattern, answer in generic_answers:
        if pattern.search(normalized_question):
            return {"answer": answer, "sources": []}

    return {
        "answer": KNOWLEDGE_BASE["fallback_answer"],
        "sources": [],
    }


class StingRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self.send_json({"status": "ok"})
            return

        if parsed.path == "/api/knowledge":
            self.send_json(
                {
                    "assistantName": KNOWLEDGE_BASE["assistantName"],
                    "statusText": KNOWLEDGE_BASE["statusText"],
                    "documents": [
                        {
                            "id": document.id,
                            "title": document.title,
                            "summary": document.summary,
                            "url": document.url,
                            "hasRemoteContent": bool(document.extracted_text),
                        }
                        for document in KNOWLEDGE_BASE["documents"]
                    ],
                }
            )
            return

        if parsed.path == "/api/ask":
            question = parse_qs(parsed.query).get("q", [""])[0]
            self.send_json(answer_question(question))
            return

        super().do_GET()

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.send_response(HTTPStatus.OK)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        super().do_HEAD()

    def send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def guess_type(self, path: str) -> str:
        if path.endswith(".js"):
            return "application/javascript; charset=utf-8"
        mime_type, _ = mimetypes.guess_type(path)
        return mime_type or "application/octet-stream"

    def log_message(self, format: str, *args: Any) -> None:
        BaseHTTPRequestHandler.log_message(self, format, *args)


def run_server(port: int = 8000) -> None:
    enrich_documents_from_remote_pdfs()
    server = ThreadingHTTPServer(("127.0.0.1", port), StingRequestHandler)
    print(f"STING local server running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
