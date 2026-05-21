# Marco de analisis de inversiones

Este documento define criterios generales para que el agente financiero analice una empresa de forma consistente.

## Principios

- Una decision de inversion debe considerar precio, fundamentales, noticias recientes, contexto macroeconomico y riesgo.
- Un precio al alza no implica necesariamente una buena compra; puede reflejar expectativas ya incorporadas por el mercado.
- Una caida de precio no implica necesariamente oportunidad; puede reflejar deterioro real del negocio.
- La diversificacion reduce riesgo especifico, pero no elimina riesgo de mercado.
- El agente debe evitar recomendaciones absolutas y explicar incertidumbre.

## Variables fundamentales

- Capitalizacion de mercado: dimension de la empresa y sensibilidad esperada ante noticias.
- Forward PE: relacion entre precio y ganancias esperadas. Valores altos pueden indicar crecimiento esperado o sobrevaloracion.
- Crecimiento de ingresos: senal de expansion del negocio.
- Margen de beneficio: capacidad de convertir ingresos en utilidad.
- Dividend yield: retorno por dividendos, mas relevante en empresas maduras.

## Lectura de noticias

Las noticias se deben interpretar segun impacto potencial en ingresos, costos, regulacion, reputacion, oferta, demanda o expectativas.

Ejemplos:

- Una noticia sobre demanda de chips puede afectar a NVDA, AMD, TSM o proveedores relacionados.
- Una noticia sobre ventas de iPhone puede afectar a AAPL y a su cadena de suministro.
- Una noticia sobre tasas de interes puede afectar empresas de crecimiento, bancos y consumo.

## Salida esperada del agente

Cuando el usuario pregunta por una accion, el agente debe:

1. Identificar ticker o empresa.
2. Consultar precio y datos fundamentales si son necesarios.
3. Consultar noticias recientes si el usuario pide contexto actual.
4. Recuperar conocimiento historico o conceptual desde ChromaDB cuando aporte contexto.
5. Responder con conclusion, evidencia y riesgos.

El agente no debe presentar su respuesta como asesoria financiera personalizada.
