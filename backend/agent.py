from langchain_groq import ChatGroq
try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools import add_to_notion_portfolio, get_stock_price, get_stock_fundamentals, get_market_news, search_stored_news, search_web_for_tweets
from dotenv import load_dotenv
import os

load_dotenv()

def get_finance_agent():
    """Configura y devuelve el agente de análisis financiero."""
    
    # Usamos Groq por defecto por su velocidad y capa gratuita
    # Si no hay API key, fallará elegantemente
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    llm = ChatGroq(
        temperature=0, 
        model_name="llama--3.3-70b-versatile" if False else "llama-3.3-70b-versatile", 
        groq_api_key=api_key
    )

    tools = [get_stock_price, get_stock_fundamentals, get_market_news, search_stored_news, add_to_notion_portfolio, search_web_for_tweets]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un analista financiero experto. 
        Tu objetivo es ayudar a los usuarios a tomar decisiones informadas sobre el mercado.
        Utiliza las herramientas disponibles para obtener datos en tiempo real.
        Si el usuario dice que compro o vendio acciones y quiere registrarlo en su portafolio, utiliza 'add_to_notion_portfolio'. Si falta el precio, intenta obtenerlo con 'get_stock_price' antes de registrar la operacion.
        Si el usuario pide buscar informacion reciente en internet fuera de yfinance o NYT, utiliza 'search_web_for_tweets'.
        
        - Si te preguntan por noticias de mercado actuales o recientes para una acción, utiliza 'get_market_news'. Esto descargará noticias de tiempo real y de forma automática las guardará persistentes en ChromaDB para el futuro.
        - Si te preguntan por noticias históricas, contexto de días anteriores, comparaciones del pasado, o sobre información previamente almacenada, utiliza la herramienta 'search_stored_news' para buscar en la base de datos vectorial ChromaDB.
        
        Sé profesional, analítico y honesto sobre los riesgos financieros."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
