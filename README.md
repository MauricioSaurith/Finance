# Finance Agent - Proyecto Final IA

Finance Agent es un agente inteligente para analisis de mercados financieros. Integra RAG, herramientas de consulta en tiempo real y registro de operaciones en Notion.

## Problema que resuelve

Los inversionistas principiantes suelen consultar precios, noticias, fundamentales y notas de portafolio en herramientas separadas. Finance Agent centraliza ese flujo en un agente conversacional capaz de buscar datos actuales, recuperar conocimiento almacenado, explicar riesgos y registrar operaciones.

El uso de un agente inteligente se justifica porque el sistema debe decidir que herramienta usar segun la intencion del usuario: precio actual, fundamentales, noticias recientes, memoria historica o registro de una compra/venta.

## Arquitectura resumida

- **Frontend:** React + Vite.
- **Backend:** FastAPI.
- **LLM:** Groq con LangChain.
- **Tools:** yfinance, noticias, ChromaDB y Notion.
- **RAG:** ChromaDB con embeddings locales `all-MiniLM-L6-v2`.

El RAG combina dos fuentes:

1. Documentos curados en `backend/knowledge_base`.
2. Noticias financieras guardadas durante el uso del agente.

Para mas detalle ver:

- `docs/ARCHITECTURE.md`
- `docs/RUBRIC_ANALYSIS.md`
- `docs/EVALUATION_PLAN.md`

## Ejecucion del proyecto

### 1. Requisitos previos

- **Python 3.10+**
- **Node.js 18+**
- **Groq API Key**
- **Notion API Key y Database ID** si se quiere registrar portafolio

### 2. Configuracion del backend

1. Entra a la carpeta `backend`:

   ```bash
   cd backend
   ```

2. Crea un entorno virtual e instala dependencias:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Crea un archivo `.env` basado en `.env.example`.

4. Carga el conocimiento base en ChromaDB:

   ```bash
   python seed_knowledge.py
   ```

5. Inicia el servidor:

   ```bash
   python main.py
   ```

### 3. Configuracion del frontend

1. Abre una nueva terminal y entra a `frontend`:

   ```bash
   cd frontend
   ```

2. Instala dependencias:

   ```bash
   npm install
   ```

3. Inicia la aplicacion:

   ```bash
   npm run dev
   ```

## Caracteristicas principales

- **Agentic reasoning:** el LLM decide si necesita buscar precios, fundamentales, noticias o memoria.
- **RAG con ChromaDB:** combina documentos curados y noticias almacenadas.
- **Tools financieras:** yfinance para precio, fundamentales y noticias.
- **Portafolio en Notion:** registra compras y ventas detectadas en lenguaje natural.
- **Interfaz web:** chat y paneles de noticias/tendencias.

## Despliegue

El frontend puede desplegarse en Vercel. El backend FastAPI necesita un servicio persistente como Render, Railway o Fly.io, o una adaptacion a funciones serverless.

En produccion, el frontend debe usar una variable como `VITE_API_URL` para apuntar al backend desplegado.
