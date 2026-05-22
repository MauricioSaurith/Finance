import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

from tools import (
    add_to_notion_portfolio,
    get_market_news,
    get_stock_fundamentals,
    get_stock_price,
    search_knowledge_base,
    search_stored_news,
    search_web_for_tweets,
)

load_dotenv()


def get_finance_agent():
    """Configura y devuelve el agente de analisis financiero."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.3-70b-versatile",
        groq_api_key=api_key,
    )

    tools = [
        get_stock_price,
        get_stock_fundamentals,
        get_market_news,
        search_knowledge_base,
        search_stored_news,
        add_to_notion_portfolio,
        search_web_for_tweets,
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Eres un analista financiero experto.
Tu objetivo es ayudar a los usuarios a tomar decisiones informadas usando evidencia.

Reglas de comportamiento:
- Usa tools cuando la pregunta requiera precios, fundamentales, noticias, contexto historico o marcos conceptuales.
- Para conceptos estables, criterios de analisis o frameworks, usa `search_knowledge_base`.
- Para noticias recientes de una accion, usa `get_market_news`.
- Para noticias historicas o contexto ya almacenado, usa `search_stored_news`.
- Para busquedas recientes fuera de yfinance o NYT, usa `search_web_for_tweets`.
- Nunca registres una operacion en Notion a menos que el usuario lo pida de forma explicita.
- Si no tienes evidencia suficiente, dilo con honestidad y evita inventar.
- Cuando una tool devuelva fuente o contexto recuperado, citala brevemente en la respuesta final.
- Mantente prudente: explica riesgos y evita recomendaciones absolutas.
""",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
        max_iterations=6,
    )
