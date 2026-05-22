# Flujo de decision del agente y uso de tools

Finance Agent decide que componente usar segun la intencion del usuario y segun el riesgo de la accion solicitada.

## Regla general

El agente no debe responder solo con memoria del modelo cuando existe una tool o una fuente recuperable mas confiable.

Si el LLM falla al llamar una tool o entra en rate limit, el backend puede activar un fallback directo para intenciones claras como precio, fundamentales, noticias recientes, conocimiento base o noticias historicas.

## Consultar precio actual

Si el usuario pregunta por precio actual, valor de mercado o cotizacion de una accion, usar `get_stock_price`.

Ejemplos:

- "Cual es el precio actual de Apple?"
- "Como esta NVDA hoy?"

## Consultar fundamentales

Si el usuario pregunta por salud financiera, valoracion, crecimiento, PE, dividendos o descripcion del negocio, usar `get_stock_fundamentals`.

Ejemplos:

- "Apple esta cara por fundamentales?"
- "Compara el crecimiento de Microsoft y Nvidia."

## Consultar noticias recientes

Si el usuario pregunta por noticias actuales, catalizadores o eventos recientes, usar `get_market_news`.

Esta tool devuelve una version resumida de las noticias y tambien las guarda en ChromaDB para consultas futuras.

## Consultar conocimiento base

Si el usuario pregunta por criterios de analisis, marcos conceptuales, gestion de riesgo o como evaluar una accion antes de comprar, usar `search_knowledge_base`.

Este retrieval debe recuperar fragmentos del corpus curado del proyecto, no solo una respuesta generica del LLM.

## Consultar memoria historica

Si el usuario pregunta por noticias previas, contexto de dias anteriores o informacion ya almacenada sobre un ticker, usar `search_stored_news`.

Esta tool debe recuperar noticias persistidas en ChromaDB con fuente y ticker.

## Buscar en web abierta

Si el usuario pide referencias recientes fuera de yfinance o NYT, usar `search_web_for_tweets`.

Ejemplos:

- "Busca opiniones recientes sobre Tesla en X."
- "Encuentra comentarios recientes sobre Coinbase."

## Registrar operaciones en Notion

Si el usuario informa que compro o vendio acciones y pide registrarlo en su portafolio, usar el flujo de portafolio:

1. Confirmar que el usuario realmente pidio registrar la operacion.
2. Extraer accion: Compra o Venta.
3. Extraer cantidad.
4. Identificar ticker.
5. Obtener precio actual si el usuario no lo entrega.
6. Crear pagina en Notion con Ticker, Accion, Cantidad, Price, Fecha, Tweets y Paises.

Para este caso el backend incluye una ruta deterministica antes del agente LLM, porque registrar una operacion es una accion sensible y debe ser consistente.

## Evidencia para evaluacion

El backend devuelve una traza de tools por respuesta. Esa traza sirve para evaluar:

- Si el agente uso la tool correcta.
- Si el retrieval vino de conocimiento base o noticias almacenadas.
- Si la respuesta final estuvo apoyada por evidencia y no por improvisacion.
