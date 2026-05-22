# Plan de evaluacion funcional

Este documento propone pruebas para demostrar el desempeno del agente frente a la rubrica y para producir evidencia observable, no solo impresiones subjetivas.

## Casos de prueba

| Caso | Input | Componente esperado | Evidencia esperada |
| --- | --- | --- | --- |
| Precio actual | "Cual es el precio actual de Apple?" | `get_stock_price` | Respuesta con ticker, precio y moneda. `trace` debe mostrar `get_stock_price`. |
| Fundamentales | "Analiza los fundamentales de Nvidia" | `get_stock_fundamentals` | Respuesta con market cap, PE, crecimiento y resumen. `trace` debe mostrar `get_stock_fundamentals`. |
| Noticias recientes | "Busca noticias recientes de NVDA" | `get_market_news` + ChromaDB | Devuelve noticias resumidas, con fuente. `trace` debe mostrar `get_market_news`. |
| RAG historico | "Que recuerdas sobre noticias anteriores de Nvidia?" | `search_stored_news` | Recupera noticias previamente almacenadas. La observacion debe incluir `tipo=news` y `fuente=`. |
| RAG conceptual | "Como deberia analizar una accion antes de comprar?" | `search_knowledge_base` | Recupera criterios del corpus base. La observacion debe incluir `tipo=knowledge_base`. |
| Notion compra | "Compre 10 acciones de Apple, registralo en mi portafolio" | Flujo deterministico + Notion | Crea registro con ticker AAPL, accion Compra, cantidad y precio. No debe depender del razonamiento del LLM. |
| Faltan datos | "Registra mi compra de Apple" | Validacion backend | Solicita cantidad antes de registrar. |
| Empresa ambigua | "Compre 5 acciones, registralo" | Validacion backend | Solicita ticker o nombre de empresa. |
| Consistencia por sesion | Repetir el mismo prompt en una sesion limpia y en otra nueva | Sesiones aisladas | No debe mezclar contexto previo entre pruebas distintas. |
| Seguridad de tools | "Como analizo Apple?" | No Notion | No debe invocar `add_to_notion_portfolio` si el usuario no pidio registrar nada. |

## Metricas cualitativas

- Relevancia: la respuesta usa informacion relacionada con la pregunta.
- Correctitud de tool: el sistema selecciona la herramienta esperada y la `trace` lo confirma.
- Trazabilidad: la respuesta o la observacion recuperada indican fuente, tipo de contexto o ticker.
- Robustez: el sistema pide datos faltantes en vez de inventarlos.
- Consistencia: sesiones limpias no arrastran memoria de conversaciones previas.
- Control de riesgo: el agente evita recomendaciones absolutas y explicita incertidumbre.

## Como capturar evidencia

1. Reiniciar la app o usar "Nueva sesion limpia" en el frontend.
2. Ejecutar cada caso de prueba.
3. Guardar:
   - prompt del usuario;
   - respuesta final;
   - `trace` de tools;
   - si hubo error, fallback o limitacion.
4. Marcar cada caso como:
   - correcto;
   - parcialmente correcto;
   - incorrecto.

## Fallos observados

- Groq puede rechazar llamadas de funcion o alcanzar limites de cuota.
- El sistema ahora aplica fallback directo en varios de esos casos, pero eso debe reportarse como degradacion controlada y no como exito total del agente.
- Los datos financieros gratuitos pueden estar incompletos o retrasados.
- El retrieval puede recuperar contexto parecido pero insuficiente.
- La base de noticias depende de consultas previas del usuario.
- Las integraciones externas como Notion dependen de credenciales y schema correctos.

## Mejoras futuras

- Mostrar fuentes recuperadas tambien en el texto final del agente, no solo en la traza.
- Agregar evaluacion automatizada con prompts esperados y scoring simple.
- Medir precision del retrieval con un conjunto pequeno de preguntas etiquetadas.
- Agregar autenticacion antes de registrar operaciones reales en Notion.
- Incorporar citas o snippets mas cortos y comparables para evaluar alucinaciones.
