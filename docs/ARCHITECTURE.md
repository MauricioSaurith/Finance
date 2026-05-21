# Arquitectura de Finance Agent

## Objetivo

Finance Agent ayuda a analizar acciones y registrar decisiones de portafolio combinando un LLM, herramientas externas, RAG y una interfaz web.

## Componentes

```text
Usuario
  |
  v
Frontend React/Vite
  |
  v
Backend FastAPI
  |
  +--> Flujo deterministico de portafolio --> yfinance --> Notion
  |
  +--> Agente LangChain/Groq
          |
          +--> get_stock_price
          +--> get_stock_fundamentals
          +--> get_market_news --> ChromaDB
          +--> search_stored_news --> ChromaDB

ChromaDB
  |
  +--> Knowledge base curada
  +--> Noticias almacenadas durante el uso
```

## RAG

El RAG usa embeddings locales con `all-MiniLM-L6-v2` y ChromaDB como base vectorial persistente.

Fuentes del RAG:

- `backend/knowledge_base`: documentos curados sobre criterios de analisis financiero, uso de RAG y flujo de tools.
- Noticias recuperadas por `get_market_news`, almacenadas con metadata de ticker.

## Flujo del agente

1. El usuario envia un mensaje desde el frontend.
2. FastAPI recibe el mensaje en `/chat`.
3. Si el mensaje es una compra o venta para portafolio, se usa un flujo deterministico.
4. En los demas casos, el mensaje pasa al agente LangChain.
5. El agente decide si debe consultar precio, fundamentales, noticias o memoria vectorial.
6. El backend devuelve una respuesta al frontend.

## Justificacion de la ruta deterministica de portafolio

Registrar una compra o venta en Notion modifica un sistema externo. Por eso se evita depender por completo de una llamada de tool generada por el LLM. El backend extrae cantidad, ticker y accion de forma deterministica, valida datos faltantes y solo despues llama a Notion.

## Despliegue

El frontend puede desplegarse en Vercel.

El backend FastAPI necesita ejecutarse como servicio persistente o adaptarse a funciones serverless. Para una entrega estable se recomienda desplegar backend en Render, Railway o Fly.io y configurar en Vercel una variable `VITE_API_URL` apuntando a ese backend.
