import json
import os
from datetime import datetime

import requests
import yfinance as yf
from dotenv import load_dotenv
from langchain.tools import tool

from rag import (
    add_news_to_vectorstore,
    normalize_news_item,
    query_knowledge_base,
    query_stored_news,
)

load_dotenv()


@tool
def get_stock_price(ticker: str):
    """Obtiene el precio actual de una accion para consultas rapidas de mercado."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return json.dumps(
            {
                "ticker": ticker,
                "currentPrice": info.get("currentPrice", "No disponible"),
                "currency": info.get("currency", "USD"),
                "longName": info.get("longName", ticker),
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        return f"Error obteniendo precio para {ticker}: {exc}"


@tool
def get_stock_fundamentals(ticker: str):
    """Obtiene datos fundamentales de una empresa como market cap, PE y crecimiento."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        business_summary = info.get("longBusinessSummary") or "No disponible"

        return json.dumps(
            {
                "ticker": ticker,
                "marketCap": info.get("marketCap"),
                "forwardPE": info.get("forwardPE"),
                "dividendYield": info.get("dividendYield"),
                "revenueGrowth": info.get("revenueGrowth"),
                "businessSummary": f"{business_summary[:500]}...",
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        return f"Error obteniendo fundamentales para {ticker}: {exc}"


@tool
def get_market_news(ticker: str):
    """Obtiene noticias recientes de una accion y guarda una version persistente en ChromaDB."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news or []

        if news:
            try:
                add_news_to_vectorstore(news, ticker)
            except Exception as db_err:
                print(f"Advertencia: No se pudieron guardar noticias en ChromaDB: {db_err}")

        normalized_news = []
        for item in news[:5]:
            normalized = normalize_news_item(item, ticker=ticker)
            if normalized:
                normalized_news.append(normalized)

        if not normalized_news:
            return "No se encontraron noticias recientes para ese ticker."

        return json.dumps(normalized_news, ensure_ascii=False)
    except Exception as exc:
        return f"Error obteniendo noticias para {ticker}: {exc}"


@tool
def search_knowledge_base(query: str):
    """Busca criterios y marcos conceptuales en el corpus curado del proyecto."""
    try:
        return query_knowledge_base(query)
    except Exception as exc:
        return f"Error buscando conocimiento base en la base vectorial: {exc}"


@tool
def search_stored_news(query: str, ticker: str = None):
    """Busca noticias historicas previamente almacenadas en ChromaDB."""
    try:
        return query_stored_news(query, ticker)
    except Exception as exc:
        return f"Error buscando noticias almacenadas en la base vectorial: {exc}"


@tool
def add_to_notion_portfolio(
    ticker: str,
    action: str,
    shares: float,
    price: float,
    tweets: str = "No reportado",
    paises: str = "Global",
):
    """Registra una decision de inversion en Notion."""
    notion_api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_api_key or not database_id:
        return "Error: Las credenciales de Notion no estan configuradas en el archivo .env"

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Ticker": {
                "title": [{"text": {"content": ticker.upper()}}],
            },
            "Acción": {
                "select": {"name": action.capitalize()},
            },
            "Cantidad": {
                "number": float(shares),
            },
            "Price": {
                "number": float(price),
            },
            "Fecha": {
                "date": {"start": datetime.now().isoformat()},
            },
            "Tweets": {
                "rich_text": [{"text": {"content": tweets}}],
            },
            "Paises": {
                "rich_text": [{"text": {"content": paises}}],
            },
        },
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code in (200, 201):
            return (
                f"Exito: se ha registrado la {action.lower()} de {shares} acciones "
                f"de {ticker} a ${price} en tu portafolio de Notion."
            )
        return f"Error guardando en Notion: {response.text}"
    except Exception as exc:
        return f"Excepcion al conectar con Notion: {exc}"


@tool
def search_web_for_tweets(query: str):
    """Busca en internet referencias recientes a una empresa, tema o ticker."""
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No se encontraron resultados en la web."

            formatted_results = []
            for result in results:
                formatted_results.append(
                    "\n".join(
                        [
                            f"Titulo: {result.get('title')}",
                            f"Resumen: {result.get('body')}",
                            f"Enlace: {result.get('href')}",
                        ]
                    )
                )

            return "\n\n".join(formatted_results)
    except ImportError:
        return (
            "Error: La libreria duckduckgo-search no esta instalada. "
            "Ejecuta 'pip install duckduckgo-search'."
        )
    except Exception as exc:
        return f"Error buscando en la web: {exc}"
