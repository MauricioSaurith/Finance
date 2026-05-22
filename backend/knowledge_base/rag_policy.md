# Politica de uso de RAG en Finance Agent

El RAG del proyecto combina conocimiento estable con memoria dinamica del mercado.

## 1. Conocimiento base

Documentos curados por el equipo del proyecto. Explican conceptos, criterios y reglas de analisis financiero que deben mantenerse estables durante la ejecucion.

Estos documentos se fragmentan en chunks pequenos y se guardan con metadata de fuente, tipo y chunk.

## 2. Memoria dinamica de mercado

Noticias recuperadas con herramientas como yfinance. Cuando el usuario consulta noticias recientes de una accion, el sistema almacena una version resumida de esas noticias en ChromaDB para permitir consultas posteriores.

Cada noticia guarda ticker, enlace y proveedor para mejorar la trazabilidad.

## 3. Memoria conversacional

La conversacion se mantiene por sesion, no de forma global.

Esto reduce contaminacion entre usuarios o entre pruebas diferentes y mejora la consistencia del agente durante la evaluacion.

## Por que no basta un chatbot simple

Un chatbot simple responde solo con el conocimiento del modelo. Finance Agent combina:

- LLM para interpretar intencion y redactar explicaciones.
- Tools para consultar precio, fundamentales, noticias y Notion.
- Embeddings para representar documentos y noticias como vectores.
- ChromaDB para recuperar contexto relevante.
- Memoria aislada por sesion para conservar el hilo sin mezclar conversaciones.

## Trazabilidad

Las respuestas del backend incluyen una traza de tools. Esa traza permite verificar:

- que tool fue invocada;
- con que input fue llamada;
- que observacion devolvio.

Esto ayuda a evaluar correctitud de tool, retrieval y posibles alucinaciones.

## Limitaciones

- Las noticias almacenadas dependen de las consultas hechas por el usuario.
- yfinance puede entregar datos incompletos o cambiar su formato.
- El retrieval puede recuperar contexto relacionado pero no necesariamente suficiente.
- El agente puede responder de forma generica si el modelo no decide usar retrieval.
- La traza ayuda a detectar errores, pero no reemplaza una evaluacion humana.

## Mitigaciones

- Mantener documentos base curados y separados de las noticias historicas.
- Usar ids deterministas para evitar duplicados al recargar documentos.
- Mostrar fuentes o contexto recuperado cuando sea posible.
- Usar rutas deterministicas para acciones criticas como registrar compras en Notion.
- Evaluar casos positivos, ambiguos y con datos faltantes.
