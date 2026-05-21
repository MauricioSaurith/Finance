# Politica de uso de RAG en Finance Agent

El RAG del proyecto tiene dos tipos de conocimiento:

## 1. Conocimiento base

Documentos curados por el equipo del proyecto. Explican conceptos, criterios y reglas de analisis financiero que deben mantenerse estables durante la ejecucion.

Este conocimiento permite que el agente no dependa solamente de lo que el LLM recuerde, sino que recupere instrucciones y criterios desde una base vectorial.

## 2. Memoria dinamica de mercado

Noticias recuperadas con herramientas como yfinance. Cuando el usuario consulta noticias recientes de una accion, el sistema almacena esas noticias en ChromaDB para permitir consultas posteriores.

Esto convierte al RAG en una memoria historica incremental de eventos de mercado observados durante el uso del sistema.

## Por que no basta un chatbot simple

Un chatbot simple responde solo con el conocimiento del modelo. Finance Agent combina:

- LLM para interpretar intencion y generar explicaciones.
- Tools para consultar precio, fundamentales, noticias y Notion.
- Embeddings para representar documentos y noticias como vectores.
- ChromaDB para recuperar contexto relevante.
- Memoria conversacional para sostener el dialogo.

## Limitaciones

- Las noticias almacenadas dependen de las consultas hechas por el usuario.
- yfinance puede entregar datos incompletos o cambiar su formato.
- El retrieval puede recuperar contexto relacionado pero no necesariamente suficiente.
- El agente puede fallar si el modelo genera una llamada de tool invalida.

## Mitigaciones

- Mantener documentos base curados.
- Mostrar fuentes o contexto cuando sea posible.
- Usar rutas deterministicas para acciones criticas como registrar compras en Notion.
- Evaluar casos positivos, casos ambiguos y casos donde faltan datos.
