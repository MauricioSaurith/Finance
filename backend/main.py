from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import re

from agent import get_finance_agent
from langchain_core.messages import HumanMessage, AIMessage
import feedparser
from langchain_groq import ChatGroq
import os
from tools import add_to_notion_portfolio, get_stock_price

app = FastAPI(title="Finance Agent API")

# Memoria simple en memoria (para el proyecto escolar)
chat_history = []

# ... (middleware stays the same)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

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

def infer_market_impact(title: str, summary: str):
    text = f"{title} {summary}".lower()
    matches = []
    for keyword, ticker in NEWS_TICKER_KEYWORDS.items():
        if keyword in text and ticker not in matches:
            matches.append(ticker)

    if matches:
        tickers = ", ".join(matches[:3])
        return f"Posible impacto en {tickers}. La noticia puede mover expectativas de ingresos, costos, tasas o sentimiento del sector."

    return "Impacto general de mercado. Conviene revisar si afecta tasas, consumo, regulacion, crecimiento o apetito por riesgo."

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
        summary = clean_feed_text(getattr(entry, "summary", getattr(entry, "description", "Sin resumen disponible")))
        link = getattr(entry, "link", "")
        results.append({
            "title": title,
            "summary": summary,
            "link": link,
            "analysis": infer_market_impact(title, summary),
        })

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

    lines.append("Nota: este analisis usa el RSS publico de NYT y reglas de impacto de mercado, sin gastar tokens del LLM.")
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
    price_data = json.loads(get_stock_price.invoke(ticker))
    price = price_data.get("currentPrice")

    if not isinstance(price, (int, float)):
        return f"No pude obtener el precio actual de {ticker}. Dame el precio y lo registro en Notion."

    result = add_to_notion_portfolio.invoke({
        "ticker": ticker,
        "action": action,
        "shares": shares,
        "price": float(price),
        "tweets": "No reportado",
        "paises": "Global",
    })
    return result

@app.get("/")
async def root():
    return {"status": "online", "message": "Finance Agent API is running"}

@app.post("/chat")
async def chat(request: ChatRequest):
    portfolio_response = handle_portfolio_intent(request.message)
    if portfolio_response:
        chat_history.append(HumanMessage(content=request.message))
        chat_history.append(AIMessage(content=portfolio_response))
        return {"response": portfolio_response}

    nyt_response = handle_nyt_intent(request.message)
    if nyt_response:
        chat_history.append(HumanMessage(content=request.message))
        chat_history.append(AIMessage(content=nyt_response))
        return {"response": nyt_response}

    agent_executor = get_finance_agent()
    
    if not agent_executor:
        return {
            "response": "Error: GROQ_API_KEY no configurada. Por favor, añade tu API Key al archivo .env"
        }

    try:
        response = agent_executor.invoke({
            "input": request.message,
            "chat_history": chat_history
        })
        
        # Guardar en historial
        chat_history.append(HumanMessage(content=request.message))
        chat_history.append(AIMessage(content=response["output"]))
        
        return {"response": response["output"]}
    except Exception as e:
        error_message = str(e)
        if "rate_limit" in error_message.lower() or "429" in error_message:
            return {
                "response": "Groq alcanzo el limite de tokens por hoy. Puedo seguir respondiendo flujos directos como NYT, Notion y algunas consultas con tools, pero el razonamiento general del agente puede fallar hasta que se libere cuota."
            }
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/nyt")
async def get_nyt_news():
    try:
        entries = fetch_nyt_business_news()
        
        # Analyze using Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"news": entries}
            
        llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", groq_api_key=api_key)
        
        results = []
        for e in entries:
            prompt = f"Analiza brevemente (1 o 2 lineas maximo) que accion de bolsa o ETF podria verse afectado por esta noticia y por que.\nTitulo: {e['title']}\nResumen: {e['summary']}"
            try:
                analysis = llm.invoke(prompt).content
            except Exception:
                analysis = e["analysis"]
            results.append({
                "title": e["title"],
                "summary": e["summary"],
                "link": e["link"],
                "analysis": analysis
            })
            
        return {"news": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tweets")
async def get_simulated_tweets():
    try:
        # Simulate top trending financial tweets and analyze them
        # In a real app we'd use X API or Stocktwits API
        mock_tweets = [
            {"user": "@WallStBull", "text": "Nvidia $NVDA just broke resistance again! AI demand is unmatched. Buying calls."},
            {"user": "@TechAnalyst", "text": "Apple $AAPL sales in China are slowing down significantly according to recent supply chain reports."},
            {"user": "@CryptoKing", "text": "Bitcoin $BTC holding strong at current levels, but $COIN might see a dip if volume drops."}
        ]
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"tweets": [{"user": t["user"], "text": t["text"], "analysis": "GROQ_API_KEY no configurada."} for t in mock_tweets]}
            
        llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", groq_api_key=api_key)
        
        results = []
        for t in mock_tweets:
            prompt = f"Analiza este tweet financiero en 1 línea e indica el sentimiento (Alcista/Bajista) para la acción mencionada.\nTweet: {t['text']}"
            analysis = llm.invoke(prompt).content
            results.append({
                "user": t["user"],
                "text": t["text"],
                "analysis": analysis
            })
            
        return {"tweets": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
