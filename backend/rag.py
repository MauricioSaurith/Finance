from hashlib import sha1
from pathlib import Path
import os

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# Embeddings locales y gratuitos.
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

CHROMA_DB_DIR = "chroma_db"
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
KNOWLEDGE_CHUNK_SIZE = 900
knowledge_base_ready = False


def get_vectorstore():
    return Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)


def build_document_id(page_content: str, metadata: dict):
    raw = "||".join(
        [
            metadata.get("type", ""),
            metadata.get("source", ""),
            metadata.get("ticker", ""),
            str(metadata.get("chunk", "")),
            page_content.strip(),
        ]
    )
    return sha1(raw.encode("utf-8")).hexdigest()


def split_large_block(text: str, max_chars: int = KNOWLEDGE_CHUNK_SIZE):
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    if len(paragraphs) <= 1:
        return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            chunks.extend(
                paragraph[i : i + max_chars] for i in range(0, len(paragraph), max_chars)
            )
            current = ""

    if current:
        chunks.append(current)

    return chunks


def chunk_markdown_document(content: str):
    sections = []
    current_section = []

    for line in content.splitlines():
        if line.startswith("## ") and current_section:
            sections.append("\n".join(current_section).strip())
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section).strip())

    chunks = []
    for section in sections:
        chunks.extend(split_large_block(section))

    return [chunk for chunk in chunks if chunk]


def add_documents_to_vectorstore(documents, ids=None):
    """Agrega documentos a ChromaDB evitando duplicados por ids estables."""
    if not documents:
        return None

    doc_ids = ids or [
        build_document_id(document.page_content, document.metadata) for document in documents
    ]

    if os.path.exists(CHROMA_DB_DIR):
        vectorstore = get_vectorstore()
        existing_ids = set(vectorstore.get(include=[]).get("ids", []))

        documents_to_add = []
        ids_to_add = []
        for document, doc_id in zip(documents, doc_ids):
            if doc_id in existing_ids:
                continue
            documents_to_add.append(document)
            ids_to_add.append(doc_id)

        if documents_to_add:
            vectorstore.add_documents(documents_to_add, ids=ids_to_add)

        return vectorstore

    return Chroma.from_documents(
        documents,
        embeddings,
        persist_directory=CHROMA_DB_DIR,
        ids=doc_ids,
    )


def delete_documents_by_type(content_type: str):
    if not os.path.exists(CHROMA_DB_DIR):
        return

    vectorstore = get_vectorstore()
    try:
        vectorstore.delete(where={"type": content_type})
    except TypeError:
        vectorstore._collection.delete(where={"type": content_type})


def normalize_news_item(item, ticker=None):
    """Reduce la noticia a campos trazables y utiles para el LLM."""
    info = item.get("content", item) if isinstance(item.get("content"), dict) else item

    title = info.get("title")
    if not title:
        return None

    summary = info.get("summary") or info.get("description") or "No disponible"
    link = info.get("link")
    if not link and isinstance(info.get("canonicalUrl"), dict):
        link = info.get("canonicalUrl").get("url")

    provider = "No disponible"
    if isinstance(info.get("provider"), dict):
        provider = info["provider"].get("displayName") or provider

    published_at = info.get("pubDate") or info.get("displayTime") or "No disponible"

    return {
        "ticker": ticker or "GENERAL",
        "title": title,
        "summary": summary,
        "provider": provider,
        "published_at": published_at,
        "link": link or "No disponible",
    }


def load_knowledge_base():
    """Carga documentos curados de conocimiento financiero en ChromaDB."""
    global knowledge_base_ready
    delete_documents_by_type("knowledge_base")

    documents = []
    document_ids = []

    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        for chunk_index, chunk in enumerate(chunk_markdown_document(content), start=1):
            metadata = {
                "source": str(path.name),
                "ticker": "GENERAL",
                "type": "knowledge_base",
                "chunk": chunk_index,
            }
            documents.append(Document(page_content=chunk, metadata=metadata))
            document_ids.append(build_document_id(chunk, metadata))

    knowledge_base_ready = True
    return add_documents_to_vectorstore(documents, ids=document_ids)


def ensure_knowledge_base_loaded():
    """Garantiza que el corpus curado este disponible sin duplicarlo."""
    if knowledge_base_ready:
        return get_vectorstore() if os.path.exists(CHROMA_DB_DIR) else None
    return load_knowledge_base()


def add_news_to_vectorstore(news_list, ticker):
    """Convierte noticias normalizadas en documentos y las añade a ChromaDB."""
    documents = []
    document_ids = []

    for item in news_list:
        normalized = normalize_news_item(item, ticker=ticker)
        if not normalized:
            continue

        content = (
            f"Titulo: {normalized['title']}\n"
            f"Resumen: {normalized['summary']}\n"
            f"Proveedor: {normalized['provider']}\n"
            f"Publicado: {normalized['published_at']}\n"
            f"Enlace: {normalized['link']}"
        )
        metadata = {
            "source": normalized["link"],
            "ticker": ticker,
            "type": "news",
            "provider": normalized["provider"],
        }
        documents.append(Document(page_content=content, metadata=metadata))
        document_ids.append(build_document_id(content, metadata))

    if not documents:
        return None

    return add_documents_to_vectorstore(documents, ids=document_ids)


def build_filter(ticker=None, content_type=None):
    clauses = []

    if ticker:
        clauses.append({"ticker": ticker})

    if content_type:
        clauses.append({"type": content_type})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def format_retrieval_results(results):
    formatted = []
    seen_signatures = set()
    result_number = 0

    for document, _ in results:
        metadata = document.metadata or {}
        signature = (
            metadata.get("type", "unknown"),
            metadata.get("source", "No disponible"),
            document.page_content.strip(),
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        result_number += 1

        header = (
            f"Resultado {result_number} | tipo={metadata.get('type', 'unknown')} | "
            f"ticker={metadata.get('ticker', 'GENERAL')} | "
            f"fuente={metadata.get('source', 'No disponible')}"
        )
        if metadata.get("chunk"):
            header += f" | chunk={metadata['chunk']}"

        formatted.append(f"{header}\n{document.page_content}")

    return "\n\n".join(formatted)


def query_market_knowledge(query, ticker=None, content_type=None, k=3):
    """Busca informacion relevante en la base vectorial y conserva la fuente."""
    ensure_knowledge_base_loaded()

    if not os.path.exists(CHROMA_DB_DIR):
        return "No hay informacion previa almacenada."

    vectorstore = get_vectorstore()
    search_filter = build_filter(ticker=ticker, content_type=content_type)

    if search_filter:
        results = vectorstore.similarity_search_with_score(query, k=k, filter=search_filter)
    else:
        results = vectorstore.similarity_search_with_score(query, k=k)

    if not results:
        return "No encontre contexto suficientemente relevante en la base vectorial."

    return format_retrieval_results(results)


def query_knowledge_base(query, k=3):
    return query_market_knowledge(query=query, content_type="knowledge_base", k=k)


def query_stored_news(query, ticker=None, k=3):
    return query_market_knowledge(query=query, ticker=ticker, content_type="news", k=k)
