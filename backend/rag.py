from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from pathlib import Path
import os

# Configurar embeddings gratuitos y locales
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Directorio para persistir la base de datos
CHROMA_DB_DIR = "chroma_db"
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"

def get_vectorstore():
    return Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

def add_documents_to_vectorstore(documents):
    """Agrega documentos a ChromaDB usando el mismo embedding local del proyecto."""
    if not documents:
        return None

    if os.path.exists(CHROMA_DB_DIR):
        vectorstore = get_vectorstore()
        vectorstore.add_documents(documents)
        return vectorstore

    return Chroma.from_documents(
        documents,
        embeddings,
        persist_directory=CHROMA_DB_DIR
    )

def load_knowledge_base():
    """Carga documentos curados de conocimiento financiero en ChromaDB."""
    documents = []
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        documents.append(Document(
            page_content=content,
            metadata={
                "source": str(path.name),
                "ticker": "GENERAL",
                "type": "knowledge_base",
            }
        ))

    return add_documents_to_vectorstore(documents)

def add_news_to_vectorstore(news_list, ticker):
    """Convierte una lista de noticias en documentos y los añade a ChromaDB."""
    documents = []
    for item in news_list:
        # Resolver si las propiedades están anidadas en 'content' (yfinance actual) o están en la raíz
        info = item.get("content", item) if isinstance(item.get("content"), dict) else item
        
        title = info.get("title")
        # Si no hay título, omitimos el elemento para no meter ruido a la DB
        if not title:
            continue
            
        summary = info.get("summary") or info.get("description") or "No disponible"
        
        # Obtener link / source
        link = info.get("link")
        if not link and isinstance(info.get("canonicalUrl"), dict):
            link = info.get("canonicalUrl").get("url")
            
        content = f"Título: {title}\nResumen: {summary}"
        doc = Document(
            page_content=content,
            metadata={"source": link or "No disponible", "ticker": ticker, "type": "news"}
        )
        documents.append(doc)
    
    if not documents:
        return None

    return add_documents_to_vectorstore(documents)

def query_market_knowledge(query, ticker=None):
    """Busca información relevante en la base de datos vectorial."""
    if not os.path.exists(CHROMA_DB_DIR):
        return "No hay información previa almacenada."
    
    vectorstore = get_vectorstore()
    
    # Si hay ticker, filtramos
    search_kwargs = {"k": 3}
    if ticker:
        search_kwargs["filter"] = {"ticker": ticker}
        
    results = vectorstore.similarity_search(query, **search_kwargs)
    return "\n\n".join([doc.page_content for doc in results])
