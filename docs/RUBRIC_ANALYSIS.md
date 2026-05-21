# Analisis frente a la rubrica

## 1. Definicion del problema y justificacion del agente

Estado actual estimado: Alto.

El problema es relevante: un usuario necesita analizar acciones y registrar decisiones de portafolio usando datos actuales, noticias y memoria historica. El uso de un agente se justifica porque la tarea combina varias decisiones: entender la intencion del usuario, seleccionar herramientas, recuperar contexto y generar una respuesta explicada.

Para aspirar a Superior, la entrega debe enfatizar que no es un chatbot financiero generico. El valor esta en combinar:

- Datos en tiempo real con `yfinance`.
- Noticias y memoria historica en ChromaDB.
- Documentos base de analisis financiero.
- LLM para explicar hallazgos y riesgos.
- Tool de Notion para registrar operaciones reales.

Riesgo evaluativo: si la justificacion no se escribe claramente, puede verse como una interfaz bonita sobre un LLM.

## 2. Diseno de la arquitectura del agente

Estado actual estimado: Alto, acercandose a Superior con la documentacion y corpus base.

Componentes existentes:

- Frontend React/Vite.
- API FastAPI.
- Agente LangChain con Groq.
- Tools financieras y de Notion.
- Embeddings locales con `all-MiniLM-L6-v2`.
- Vector database ChromaDB.
- Memoria conversacional en runtime.

Fortaleza: el sistema integra LLM, tools, embeddings y vector DB.

Debilidad: inicialmente el RAG funcionaba principalmente como memoria de noticias consultadas. Eso es valido, pero mas debil que un RAG con corpus curado. Ahora se agrego `backend/knowledge_base` para cargar conocimiento estable sobre analisis financiero y politicas de uso del RAG.

Para Superior, conviene explicar chunking, metadata, retrieval, flujo de decision y por que el registro en Notion usa una ruta deterministica para una accion sensible.

## 3. Implementacion tecnica y funcionamiento

Estado actual estimado: Basico/Alto antes de correcciones; Alto despues de los ajustes.

Funciona:

- Chat con agente.
- Consulta de precio y fundamentales.
- Consulta de noticias.
- Persistencia de noticias en ChromaDB.
- Registro de compras/ventas en Notion.
- Paneles frontend de NYT y tendencias simuladas.

Problemas encontrados y corregidos:

- La tool de Notion existia pero no estaba conectada al agente.
- `.env` no se cargaba directamente desde `tools.py`.
- El schema de Notion usaba `Price`, no `Precio`.
- La propiedad `Accion` tenia problema de codificacion y debia ser `Acción`.
- El modelo podia fallar generando llamadas de tool para registrar operaciones; se agrego un flujo deterministico en `/chat`.

Riesgos pendientes:

- Hay mojibake en varios textos del proyecto.
- El frontend tiene errores de lint.
- ChromaDB puede duplicar documentos si se ejecuta `seed_knowledge.py` muchas veces.
- El backend FastAPI no se despliega directamente en Vercel como un servidor tradicional.

## 4. Evaluacion, analisis critico e interpretacion

Estado actual estimado: Basico si solo se muestra la app; Alto/Superior si se presenta una matriz de pruebas.

Debe incluirse evidencia de:

- Respuestas con precio actual.
- Uso de noticias recientes.
- Recuperacion desde ChromaDB.
- Registro correcto en Notion.
- Fallos controlados cuando falta cantidad, ticker o credenciales.
- Limitaciones de yfinance, Groq y retrieval.

Para Superior, la evaluacion debe discutir alucinaciones, fallos de tools, consistencia, calidad de retrieval y mejoras futuras.

## Respuesta a la duda sobre RAG

Si, antes el RAG almacenaba principalmente noticias. Eso puede defenderse como memoria dinamica de mercado, pero es una version incompleta para una rubrica academica fuerte.

La comparacion con los companeros es util: ellos tienen un corpus documental estable sobre normativas. Para Finance Agent, el equivalente debe ser una base de conocimiento financiero curada mas memoria dinamica de noticias. Por eso se agrego `backend/knowledge_base`.

Recomendacion de presentacion:

"Nuestro RAG combina dos fuentes: un corpus base de criterios de analisis financiero y una memoria incremental de noticias recuperadas durante la interaccion. Esto permite responder tanto con principios estables como con eventos recientes del mercado."
