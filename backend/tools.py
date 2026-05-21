import yfinance as yf
from langchain.tools import tool
import json
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from rag import add_news_to_vectorstore, query_market_knowledge

load_dotenv()

@tool
def get_stock_price(ticker: str):
    """Obtiene el precio actual de una acciÃ³n. Ãštil para consultas rÃ¡pidas de mercado."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return json.dumps({
            "ticker": ticker,
            "currentPrice": info.get("currentPrice", "No disponible"),
            "currency": info.get("currency", "USD"),
            "longName": info.get("longName", ticker)
        })
    except Exception as e:
        return f"Error obteniendo precio para {ticker}: {str(e)}"

@tool
def get_stock_fundamentals(ticker: str):
    """Obtiene datos fundamentales de una empresa como ingresos, margen de beneficio y PE ratio."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return json.dumps({
            "ticker": ticker,
            "marketCap": info.get("marketCap"),
            "forwardPE": info.get("forwardPE"),
            "dividendYield": info.get("dividendYield"),
            "revenueGrowth": info.get("revenueGrowth"),
            "businessSummary": info.get("longBusinessSummary")[:500] + "..."
        })
    except Exception as e:
        return f"Error obteniendo fundamentales para {ticker}: {str(e)}"

@tool
def get_market_news(ticker: str):
    """Obtiene las noticias mÃ¡s recientes relacionadas con una acciÃ³n especÃ­fica y las almacena en la base de datos vectorial para consultas futuras."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if news:
            try:
                # Guardar noticias de manera asÃ­ncrona/transparente en ChromaDB
                add_news_to_vectorstore(news, ticker)
            except Exception as db_err:
                print(f"Advertencia: No se pudieron guardar las noticias en ChromaDB: {str(db_err)}")
        return json.dumps(news[:5]) # Devolver solo las 5 mÃ¡s recientes
    except Exception as e:
        return f"Error obteniendo noticias para {ticker}: {str(e)}"

@tool
def search_stored_news(query: str, ticker: str = None):
    """Busca informaciÃ³n de noticias previamente almacenadas en la base de datos vectorial ChromaDB.
    Ãštil para consultar contexto histÃ³rico, comparar noticias del pasado o recuperar informaciÃ³n archivada sobre un ticker o tema de mercado."""
    try:
        return query_market_knowledge(query, ticker)
    except Exception as e:
        return f"Error buscando noticias en la base de datos vectorial: {str(e)}"

@tool
def add_to_notion_portfolio(ticker: str, action: str, shares: float, price: float, tweets: str = "No reportado", paises: str = "Global"):
    """Registra una decisiÃ³n de inversiÃ³n en la base de datos de Notion.
    action debe ser 'Compra' o 'Venta'.
    tweets: Un resumen corto de los tweets o sentimiento general del pÃºblico sobre la acciÃ³n.
    paises: Los paÃ­ses mÃ¡s relevantes involucrados en las noticias recientes de esta empresa.
    """
    notion_api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not notion_api_key or not database_id:
        return "Error: Las credenciales de Notion no estÃ¡n configuradas en el archivo .env"
        
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Ticker": {
                "title": [{"text": {"content": ticker.upper()}}]
            },
            "Acción": {
                "select": {"name": action.capitalize()}
            },
            "Cantidad": {
                "number": float(shares)
            },
            "Price": {
                "number": float(price)
            },
            "Fecha": {
                "date": {"start": datetime.now().isoformat()}
            },
            "Tweets": {
                "rich_text": [{"text": {"content": tweets}}]
            },
            "Paises": {
                "rich_text": [{"text": {"content": paises}}]
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in (200, 201):
            return f"Exito: se ha registrado la {action.lower()} de {shares} acciones de {ticker} a ${price} en tu portafolio de Notion."
        else:
            return f"Error guardando en Notion: {response.text}"
    except Exception as e:
        return f"ExcepciÃ³n al conectar con Notion: {str(e)}"

@tool
def search_web_for_tweets(query: str):
    """Busca en internet (incluyendo Twitter/X y noticias) sobre un tema o empresa.
    Ãštil para encontrar tweets recientes, el sentimiento del pÃºblico y saber quÃ© paÃ­ses estÃ¡n involucrados en una noticia.
    Para buscar tweets, aÃ±ade 'site:twitter.com' a tu query, o simplemente busca 'opiniones recientes sobre [empresa]'.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No se encontraron resultados en la web."
            
            formatted_results = []
            for r in results:
                formatted_results.append(f"TÃ­tulo: {r.get('title')}\nResumen: {r.get('body')}\nEnlace: {r.get('href')}")
                
            return "\n\n".join(formatted_results)
    except ImportError:
        return "Error: La librerÃ­a duckduckgo-search no estÃ¡ instalada. Ejecuta 'pip install duckduckgo-search'."
    except Exception as e:
        return f"Error buscando en la web: {str(e)}"
