# Flujo de decision del agente y uso de tools

Finance Agent debe decidir que componente usar segun la intencion del usuario.

## Consultar precio

Si el usuario pregunta por precio actual, valor de mercado o cotizacion de una accion, usar `get_stock_price`.

Ejemplo:

- "Cual es el precio actual de Apple?"
- "Como esta NVDA hoy?"

## Consultar fundamentales

Si el usuario pregunta por salud financiera, valoracion, crecimiento, PE, dividendos o descripcion del negocio, usar `get_stock_fundamentals`.

Ejemplo:

- "Apple esta cara por fundamentales?"
- "Compara el crecimiento de Microsoft y Nvidia."

## Consultar noticias recientes

Si el usuario pregunta por noticias actuales, catalizadores o eventos recientes, usar `get_market_news`.

Esta tool tambien guarda noticias en ChromaDB para futuras consultas.

## Consultar memoria o conocimiento historico

Si el usuario pregunta por contexto, conceptos, criterios de analisis o noticias previamente consultadas, usar `search_stored_news`.

Aunque el nombre de la tool menciona noticias, la base vectorial tambien puede contener documentos curados de conocimiento financiero.

## Registrar operaciones en Notion

Si el usuario informa que compro o vendio acciones y pide registrarlo en su portafolio, usar el flujo de portafolio:

1. Extraer accion: Compra o Venta.
2. Extraer cantidad.
3. Identificar ticker.
4. Obtener precio actual si el usuario no lo entrega.
5. Crear pagina en Notion con Ticker, Accion, Cantidad, Price, Fecha, Tweets y Paises.

Para este caso el backend incluye una ruta deterministica antes del agente LLM, porque registrar una operacion es una accion sensible y debe ser consistente.
