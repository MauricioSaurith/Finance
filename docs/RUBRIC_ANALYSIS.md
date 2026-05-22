# Analisis frente a la rubrica

## 1. Definicion del problema y justificacion del agente

Estado actual estimado: Alto.

El problema es relevante: un usuario necesita analizar acciones y registrar decisiones de portafolio usando datos actuales, noticias, memoria historica y criterios estables de analisis.

El uso de un agente se justifica porque la tarea combina varias decisiones:

- entender la intencion del usuario;
- seleccionar herramientas distintas segun el caso;
- recuperar contexto curado o historico;
- explicar hallazgos y riesgos;
- ejecutar una accion sensible en Notion con validaciones.

## 2. Diseno de la arquitectura del agente

Estado actual estimado: Alto/Superior.

Fortalezas actuales:

- Frontend React/Vite.
- API FastAPI.
- Agente LangChain con Groq.
- Tools financieras y de Notion.
- Embeddings locales con `all-MiniLM-L6-v2`.
- ChromaDB con corpus curado y noticias persistidas.
- Memoria conversacional aislada por sesion.
- Trazas de tools para evaluacion.

La arquitectura ya no depende solo de una memoria global. Eso mejora consistencia y facilita evaluar el comportamiento del agente.

## 3. Implementacion tecnica y funcionamiento

Estado actual estimado: Alto.

Mejoras incorporadas:

- Separacion entre `search_knowledge_base` y `search_stored_news`.
- Chunking del corpus curado.
- Ids deterministas para reducir duplicados en ChromaDB.
- Noticias resumidas antes de entregarlas al LLM, para reducir ruido y consumo.
- `session_id` para aislar memoria entre pruebas.
- `trace` en la respuesta para observar uso de tools.
- Flujo deterministico para operaciones de Notion.

Riesgos pendientes:

- El modelo aun puede contestar de forma generica si no decide usar retrieval.
- yfinance puede cambiar campos o devolver datos incompletos.
- Groq puede sufrir rate limits.
- El sistema todavia no tiene una evaluacion automatizada con scoring.

## 4. Evaluacion, analisis critico e interpretacion

Estado actual estimado: Alto, con mejor base para aspirar a Superior.

Lo que ahora se puede demostrar con evidencia:

- Respuestas con precio actual usando `get_stock_price`.
- Recuperacion de noticias recientes usando `get_market_news`.
- Recuperacion de contexto curado usando `search_knowledge_base`.
- Recuperacion de noticias almacenadas usando `search_stored_news`.
- Validacion segura cuando faltan cantidad o ticker.
- Aislamiento de memoria por sesion.
- Trazabilidad de tools mediante `trace`.

Lo que aun debes discutir explicitamente en la presentacion:

- alucinaciones o respuestas demasiado genericas;
- casos en que el retrieval trae contexto relacionado pero no suficiente;
- limitaciones de Groq, yfinance y Notion;
- posibles errores de seleccion de tools;
- mejoras futuras y tradeoffs del sistema.

## Juicio final

Con estas mejoras, el proyecto ya no solo "funciona": tambien deja evidencia observable para evaluar retrieval, consistencia, correctitud de tools y robustez.

Todavia no conviene afirmar que el sistema elimina las alucinaciones. Lo correcto es decir que ahora las hace mas detectables y auditables mediante sesiones limpias, contexto recuperado y trazas de tools.
