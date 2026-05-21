# Plan de evaluacion funcional

Este documento propone pruebas para demostrar el desempeno del agente frente a la rubrica.

## Casos de prueba

| Caso | Input | Componente esperado | Resultado esperado |
| --- | --- | --- | --- |
| Precio actual | "Cual es el precio actual de Apple?" | `get_stock_price` | Respuesta con ticker, precio y moneda. |
| Fundamentales | "Analiza los fundamentales de Nvidia" | `get_stock_fundamentals` | Respuesta con market cap, PE, crecimiento y resumen. |
| Noticias recientes | "Busca noticias recientes de NVDA" | `get_market_news` + ChromaDB | Devuelve noticias y las guarda en memoria vectorial. |
| RAG historico | "Que recuerdas sobre noticias anteriores de Nvidia?" | `search_stored_news` | Recupera noticias previamente almacenadas. |
| RAG conceptual | "Como deberia analizar una accion antes de comprar?" | ChromaDB con knowledge base | Recupera criterios del corpus base. |
| Notion compra | "Compre 10 acciones de Apple, registralo en mi portafolio" | Flujo deterministico + Notion | Crea registro con ticker AAPL, accion Compra, cantidad y precio. |
| Faltan datos | "Registra mi compra de Apple" | Validacion backend | Solicita cantidad antes de registrar. |
| Empresa ambigua | "Compre 5 acciones, registralo" | Validacion backend | Solicita ticker o nombre de empresa. |

## Metricas cualitativas

- Relevancia: la respuesta usa informacion relacionada con la pregunta.
- Correctitud de tool: el sistema selecciona la herramienta esperada.
- Trazabilidad: la respuesta indica datos usados o contexto recuperado.
- Robustez: el sistema pide datos faltantes en vez de inventarlos.
- Control de riesgo: el agente evita recomendaciones absolutas.

## Fallos observados

- Groq puede rechazar llamadas de funcion si el modelo genera argumentos invalidos.
- Los datos financieros gratuitos pueden estar incompletos o retrasados.
- El retrieval puede recuperar contexto parecido pero insuficiente.
- La base de noticias depende de consultas previas del usuario.
- La integracion con Notion depende de que los nombres de propiedades coincidan exactamente.

## Mejoras futuras

- Mostrar fuentes recuperadas en la interfaz.
- Evitar duplicados en ChromaDB usando ids deterministas.
- Agregar evaluacion automatizada con prompts esperados.
- Separar backend en un servicio desplegable como Render, Railway o Fly.io.
- Agregar autenticacion antes de registrar operaciones reales en Notion.
