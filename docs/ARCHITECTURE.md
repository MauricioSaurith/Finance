# Arquitectura de Finance Agent

## Objetivo

Finance Agent ayuda a analizar acciones y registrar decisiones de portafolio combinando un LLM, herramientas externas, RAG, memoria por sesion y una interfaz web.

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
  +--> Memoria por sesion + trazas de tools
  |
  +--> Flujo deterministico de portafolio --> yfinance --> Notion
  |
  +--> Agente LangChain/Groq
          |
          +--> get_stock_price
          +--> get_stock_fundamentals
          +--> get_market_news --> ChromaDB
          +--> search_knowledge_base --> ChromaDB
          +--> search_stored_news --> ChromaDB
          +--> search_web_for_tweets

ChromaDB
  |
  +--> Knowledge base curada
  +--> Noticias almacenadas durante el uso
```

## RAG

El RAG usa embeddings locales con `all-MiniLM-L6-v2` y ChromaDB como base vectorial persistente.

Fuentes del RAG:

- `backend/knowledge_base`: documentos curados sobre criterios de analisis financiero, flujo de tools y politicas de uso del sistema.
- Noticias recuperadas por `get_market_news`, almacenadas con metadata de ticker, proveedor y fuente.

Mejoras recientes del retrieval:

- chunking de documentos curados;
- ids deterministas para evitar duplicados;
- separacion entre `search_knowledge_base` y `search_stored_news`;
- formato de salida con fuente, tipo y ticker.

## Flujo del agente

1. El usuario envia un mensaje desde el frontend.
2. FastAPI recibe el mensaje en `/chat`.
3. Cada conversacion usa un `session_id`, para aislar memoria y evitar contaminar pruebas.
4. Si el mensaje es una compra o venta para portafolio, se usa un flujo deterministico.
5. En los demas casos, el mensaje pasa al agente LangChain.
6. El agente decide si debe consultar precio, fundamentales, noticias, conocimiento base o memoria vectorial.
7. Si el agente falla por quota o por una llamada invalida de tool, el backend puede usar un fallback directo para intenciones claras.
8. El backend devuelve la respuesta y una traza de tools al frontend.

## Justificacion de la ruta deterministica de portafolio

Registrar una compra o venta en Notion modifica un sistema externo. Por eso se evita depender por completo de una llamada de tool generada por el LLM. El backend extrae cantidad, ticker y accion de forma deterministica, valida datos faltantes y solo despues llama a Notion.

## Evidencia para la rubrica

La arquitectura ahora produce evidencia observable para evaluar:

- uso correcto de tools mediante `trace`;
- retrieval mediante resultados con fuente y tipo;
- consistencia mediante sesiones aisladas;
- robustez mediante validacion deterministica en acciones sensibles.

## Despliegue

El frontend puede desplegarse en Vercel.

El backend FastAPI necesita ejecutarse como servicio persistente o adaptarse a funciones serverless. Para una entrega estable se recomienda desplegar backend en Render, Railway o Fly.io y configurar en Vercel una variable `VITE_API_URL` apuntando a ese backend.
