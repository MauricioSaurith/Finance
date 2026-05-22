import json
import os
import re
from typing import Any, Optional
from uuid import uuid4

import feedparser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel

from agent import get_finance_agent
from rag import ensure_knowledge_base_loaded
from tools import (
    add_to_notion_portfolio,
    get_market_news,
    get_stock_fundamentals,
    get_stock_price,
    search_knowledge_base,
    search_stored_news,
)

app = FastAPI(title="Finance Agent API")

MAX_CHAT_MESSAGES = 12
chat_sessions = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


COMPANY_TICKERS = {
    "apple": "AAPL",
    "aapl": "AAPL",
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "microsoft": "MSFT",
    "msft": "MSFT",
    "tesla": "TSLA",
    "tsla": "TSLA",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "googl": "GOOGL",
    "meta": "META",
}

NEWS_TICKER_KEYWORDS = {
    "apple": "AAPL",
    "iphone": "AAPL",
    "nvidia": "NVDA",
    "chips": "NVDA",
    "semiconductor": "NVDA",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "bitcoin": "BTC",
    "crypto": "BTC",
    "bank": "JPM",
    "banks": "JPM",
    "mortgage": "XLF",
    "rates": "TLT",
    "inflation": "SPY",
}


@app.on_event("startup")
async def load_project_knowledge():
    ensure_knowledge_base_loaded()


def get_or_create_session_id(session_id: Optional[str]):
    return session_id or str(uuid4())


def get_chat_history(session_id: str):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    return chat_sessions[session_id]


def append_chat_exchange(session_id: str, user_message: str, assistant_message: str):
    history = get_chat_history(session_id)
    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=assistant_message))

    if len(history) > MAX_CHAT_MESSAGES:
        del history[:-MAX_CHAT_MESSAGES]


def truncate_text(value: Any, limit=700):
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def format_intermediate_steps(intermediate_steps):
    trace = []

    for action, observation in intermediate_steps or []:
        trace.append(
            {
                "tool": getattr(action, "tool", "unknown"),
                "input": getattr(action, "tool_input", {}),
                "observation": truncate_text(observation),
            }
        )

    return trace


def build_single_trace(tool_name: str, tool_input: Any, observation: Any):
    return [
        {
            "tool": tool_name,
            "input": tool_input,
            "observation": truncate_text(observation),
        }
    ]


def infer_market_impact(title: str, summary: str):
    text = f"{title} {summary}".lower()
    matches = []
    for keyword, ticker in NEWS_TICKER_KEYWORDS.items():
        if keyword in text and ticker not in matches:
            matches.append(ticker)

    if matches:
        tickers = ", ".join(matches[:3])
        return (
            f"Posible impacto en {tickers}. La noticia puede mover expectativas "
            "de ingresos, costos, tasas o sentimiento del sector."
        )

    return (
        "Impacto general de mercado. Conviene revisar si afecta tasas, consumo, "
        "regulacion, crecimiento o apetito por riesgo."
    )


def infer_ticker_from_text(message: str):
    lower_message = message.lower()

    symbol_match = re.search(r"\$([a-z]{1,5})\b", lower_message)
    if symbol_match:
        return symbol_match.group(1).upper()

    for name, symbol in COMPANY_TICKERS.items():
        if re.search(rf"\b{re.escape(name)}\b", lower_message):
            return symbol

    upper_message = message.upper()
    for symbol in sorted(set(COMPANY_TICKERS.values())):
        if re.search(rf"\b{re.escape(symbol)}\b", upper_message):
            return symbol

    return None


def format_price_response(payload: dict):
    price = payload.get("currentPrice")
    if not isinstance(price, (int, float)):
        return "No pude recuperar un precio actual confiable para ese ticker."

    company_name = payload.get("longName") or payload.get("ticker")
    currency = payload.get("currency") or "USD"
    return (
        f"{company_name} ({payload.get('ticker')}) cotiza en {price} {currency}. "
        "Dato recuperado mediante yfinance."
    )


def format_fundamentals_response(payload: dict):
    summary = payload.get("businessSummary") or "No disponible."
    return (
        f"Fundamentales de {payload.get('ticker')}:\n"
        f"- Market cap: {payload.get('marketCap')}\n"
        f"- Forward PE: {payload.get('forwardPE')}\n"
        f"- Dividend yield: {payload.get('dividendYield')}\n"
        f"- Revenue growth: {payload.get('revenueGrowth')}\n"
        f"- Resumen del negocio: {summary}"
    )


def format_news_response(news_items, ticker: str):
    if not news_items:
        return f"No encontre noticias recientes para {ticker}."

    lines = [f"Noticias recientes de {ticker} recuperadas desde yfinance:"]
    for index, item in enumerate(news_items[:3], start=1):
        lines.append(
            f"{index}. {item.get('title')}\n"
            f"   Proveedor: {item.get('provider')}\n"
            f"   Fecha: {item.get('published_at')}\n"
            f"   Resumen: {item.get('summary')}\n"
            f"   Fuente: {item.get('link')}"
        )
    return "\n\n".join(lines)


def handle_market_data_fallback(message: str):
    text = message.lower()
    ticker = infer_ticker_from_text(message)

    asks_conceptual = any(
        phrase in text
        for phrase in [
            "como deberia analizar",
            "como analizar",
            "antes de comprar",
            "criterios de analisis",
            "gestion de riesgo",
            "framework",
            "analisis fundamental",
            "diversificacion",
        ]
    )
    if asks_conceptual:
        observation = search_knowledge_base.invoke({"query": message})
        response = f"Contexto recuperado desde el conocimiento base:\n\n{observation}"
        return response, build_single_trace("search_knowledge_base", {"query": message}, observation)

    asks_historical = any(
        word in text for word in ["anteriores", "historicas", "históricas", "previas", "pasadas", "recuerdas", "memoria"]
    ) and any(word in text for word in ["noticias", "news", "contexto"])
    if asks_historical:
        tool_input = {"query": message}
        if ticker:
            tool_input["ticker"] = ticker
        observation = search_stored_news.invoke(tool_input)
        response = f"Contexto historico recuperado desde la memoria vectorial:\n\n{observation}"
        return response, build_single_trace("search_stored_news", tool_input, observation)

    if ticker and any(word in text for word in ["precio", "cotiza", "cotizacion", "valor actual", "price"]):
        observation = get_stock_price.invoke(ticker)
        try:
            payload = json.loads(observation)
            response = format_price_response(payload)
        except json.JSONDecodeError:
            response = observation
        return response, build_single_trace("get_stock_price", {"ticker": ticker}, observation)

    if ticker and any(
        word in text
        for word in ["fundamentales", "market cap", "pe", "dividendo", "crecimiento", "ingresos", "valoracion"]
    ):
        observation = get_stock_fundamentals.invoke(ticker)
        try:
            payload = json.loads(observation)
            response = format_fundamentals_response(payload)
        except json.JSONDecodeError:
            response = observation
        return response, build_single_trace("get_stock_fundamentals", {"ticker": ticker}, observation)

    asks_recent_news = any(word in text for word in ["noticias", "news", "titulares", "catalizadores"]) and not any(
        word in text for word in ["anteriores", "historicas", "históricas", "previas", "pasadas", "nyt", "new york times"]
    )
    if ticker and asks_recent_news:
        observation = get_market_news.invoke(ticker)
        try:
            payload = json.loads(observation)
            response = format_news_response(payload, ticker)
        except json.JSONDecodeError:
            response = observation
        return response, build_single_trace("get_market_news", {"ticker": ticker}, observation)

    return None


def clean_feed_text(value: str):
    replacements = {
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00e2\u0080\u0099": "'",
        "\u00e2\u0080\u0098": "'",
        "\u00e2\u0080\u009c": '"',
        "\u00e2\u0080\u009d": '"',
        "\u00e2\u0080\u0093": "-",
        "\u00e2\u0080\u0094": "-",
        "\u00c2": "",
    }
    text = value or ""
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def fetch_nyt_business_news(limit=5):
    feed = feedparser.parse("https://rss.nytimes.com/services/xml/rss/nyt/Business.xml")
    results = []

    for entry in feed.entries[:limit]:
        title = clean_feed_text(getattr(entry, "title", "Sin titulo"))
        summary = clean_feed_text(
            getattr(entry, "summary", getattr(entry, "description", "Sin resumen disponible"))
        )
        link = getattr(entry, "link", "")
        results.append(
            {
                "title": title,
                "summary": summary,
                "link": link,
                "analysis": infer_market_impact(title, summary),
            }
        )

    return results


def format_nyt_analysis(news):
    if not news:
        return "No pude recuperar noticias del New York Times en este momento."

    lines = ["Estas son las ultimas noticias de NYT Business que pude recuperar y su lectura de mercado:"]
    for idx, item in enumerate(news, start=1):
        lines.append(
            f"{idx}. {item['title']}\n"
            f"   Resumen: {item['summary']}\n"
            f"   Analisis: {item['analysis']}\n"
            f"   Fuente: {item['link']}"
        )

    lines.append(
        "Nota: este analisis usa el RSS publico de NYT y reglas de impacto de mercado, "
        "sin gastar tokens del LLM."
    )
    return "\n\n".join(lines)


def handle_nyt_intent(message: str):
    text = message.lower()
    mentions_nyt = "new york times" in text or "nyt" in text
    asks_news = any(word in text for word in ["noticias", "news", "titulares", "ultimas", "ultimos", "hoy"])

    if not mentions_nyt or not asks_news:
        return None

    return format_nyt_analysis(fetch_nyt_business_news())


def handle_portfolio_intent(message: str):
    text = message.lower()
    is_buy = any(word in text for word in ["compre", "compré", "comprar", "compra", "comprado"])
    is_sell = any(word in text for word in ["vendi", "vendí", "vender", "venta", "vendido"])
    wants_portfolio = "portafolio" in text or "notion" in text or "registr" in text

    if not wants_portfolio or not (is_buy or is_sell):
        return None

    shares_match = re.search(r"(\d+(?:[.,]\d+)?)\s+acciones", text)
    if not shares_match:
        return "Necesito saber cuantas acciones fueron para registrar la operacion en Notion."

    ticker = None
    symbol_match = re.search(r"\$([a-z]{1,5})\b", text)
    if symbol_match:
        ticker = symbol_match.group(1).upper()
    else:
        for name, symbol in COMPANY_TICKERS.items():
            if re.search(rf"\b{re.escape(name)}\b", text):
                ticker = symbol
                break

    if not ticker:
        return "Necesito el ticker o nombre de la empresa para registrar la operacion en Notion."

    action = "Compra" if is_buy else "Venta"
    shares = float(shares_match.group(1).replace(",", "."))

    try:
        price_data = json.loads(get_stock_price.invoke(ticker))
    except json.JSONDecodeError:
        return f"No pude obtener el precio actual de {ticker}. Dame el precio y lo registro en Notion."

    price = price_data.get("currentPrice")
    if not isinstance(price, (int, float)):
        return f"No pude obtener el precio actual de {ticker}. Dame el precio y lo registro en Notion."

    result = add_to_notion_portfolio.invoke(
        {
            "ticker": ticker,
            "action": action,
            "shares": shares,
            "price": float(price),
            "tweets": "No reportado",
            "paises": "Global",
        }
    )
    return result


@app.get("/")
async def root():
    return {"status": "online", "message": "Finance Agent API is running"}


@app.delete("/chat/{session_id}")
async def reset_chat(session_id: str):
    chat_sessions.pop(session_id, None)
    return {"status": "reset", "session_id": session_id}


@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = get_or_create_session_id(request.session_id)
    fallback_response = handle_market_data_fallback(request.message)

    portfolio_response = handle_portfolio_intent(request.message)
    if portfolio_response:
        append_chat_exchange(session_id, request.message, portfolio_response)
        return {"response": portfolio_response, "session_id": session_id, "trace": []}

    nyt_response = handle_nyt_intent(request.message)
    if nyt_response:
        append_chat_exchange(session_id, request.message, nyt_response)
        return {"response": nyt_response, "session_id": session_id, "trace": []}

    agent_executor = get_finance_agent()
    if not agent_executor:
        if fallback_response:
            response_text, trace = fallback_response
            response_text += "\n\nNota: use un flujo directo porque el agente LLM no estaba disponible."
            append_chat_exchange(session_id, request.message, response_text)
            return {"response": response_text, "session_id": session_id, "trace": trace}
        return {
            "response": "Error: GROQ_API_KEY no configurada. Por favor, añade tu API Key al archivo .env",
            "session_id": session_id,
            "trace": [],
        }

    try:
        response = agent_executor.invoke(
            {
                "input": request.message,
                "chat_history": get_chat_history(session_id),
            }
        )
        assistant_response = response["output"]
        trace = format_intermediate_steps(response.get("intermediate_steps"))

        append_chat_exchange(session_id, request.message, assistant_response)
        return {
            "response": assistant_response,
            "session_id": session_id,
            "trace": trace,
        }
    except Exception as exc:
        error_message = str(exc)
        can_fallback = (
            "rate_limit" in error_message.lower()
            or "429" in error_message
            or "failed to call a function" in error_message.lower()
            or "failed_generation" in error_message.lower()
        )
        if can_fallback and fallback_response:
            response_text, trace = fallback_response
            response_text += "\n\nNota: use un flujo directo porque el agente no pudo completar la llamada de tools."
            append_chat_exchange(session_id, request.message, response_text)
            return {
                "response": response_text,
                "session_id": session_id,
                "trace": trace,
            }
        if "rate_limit" in error_message.lower() or "429" in error_message:
            return {
                "response": (
                    "Groq alcanzo el limite de tokens por hoy. Puedo seguir respondiendo "
                    "flujos directos como NYT y Notion, pero el razonamiento general del "
                    "agente puede fallar hasta que se libere cuota."
                ),
                "session_id": session_id,
                "trace": [],
            }
        raise HTTPException(status_code=500, detail=error_message)


@app.get("/nyt")
async def get_nyt_news():
    try:
        entries = fetch_nyt_business_news()

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"news": entries}

        llm = ChatGroq(
            temperature=0,
            model_name="llama-3.3-70b-versatile",
            groq_api_key=api_key,
        )

        results = []
        for entry in entries:
            prompt = (
                "Analiza brevemente (1 o 2 lineas maximo) que accion de bolsa o ETF "
                "podria verse afectado por esta noticia y por que.\n"
                f"Titulo: {entry['title']}\n"
                f"Resumen: {entry['summary']}"
            )
            try:
                analysis = llm.invoke(prompt).content
            except Exception:
                analysis = entry["analysis"]

            results.append(
                {
                    "title": entry["title"],
                    "summary": entry["summary"],
                    "link": entry["link"],
                    "analysis": analysis,
                }
            )

        return {"news": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tweets")
async def get_simulated_tweets():
    try:
        mock_tweets = [
            {
                "user": "@WallStBull",
                "text": "Nvidia $NVDA just broke resistance again! AI demand is unmatched. Buying calls.",
            },
            {
                "user": "@TechAnalyst",
                "text": "Apple $AAPL sales in China are slowing down significantly according to recent supply chain reports.",
            },
            {
                "user": "@CryptoKing",
                "text": "Bitcoin $BTC holding strong at current levels, but $COIN might see a dip if volume drops.",
            },
        ]

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {
                "tweets": [
                    {
                        "user": tweet["user"],
                        "text": tweet["text"],
                        "analysis": "GROQ_API_KEY no configurada.",
                    }
                    for tweet in mock_tweets
                ]
            }

        llm = ChatGroq(
            temperature=0,
            model_name="llama-3.3-70b-versatile",
            groq_api_key=api_key,
        )

        results = []
        for tweet in mock_tweets:
            prompt = (
                "Analiza este tweet financiero en 1 linea e indica el sentimiento "
                "(Alcista/Bajista) para la accion mencionada.\n"
                f"Tweet: {tweet['text']}"
            )
            analysis = llm.invoke(prompt).content
            results.append(
                {
                    "user": tweet["user"],
                    "text": tweet["text"],
                    "analysis": analysis,
                }
            )

        return {"tweets": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
