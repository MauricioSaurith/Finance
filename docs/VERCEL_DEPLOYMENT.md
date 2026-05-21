# Despliegue en Vercel

## Importante sobre llaves y secretos

No subas llaves reales a GitHub. Aunque el repositorio sea privado, las credenciales deben configurarse como variables de entorno en Vercel.

Los archivos `.env.example` del proyecto solo documentan que variables necesita la app. Los valores reales van en el panel de Vercel o en el proveedor donde se despliegue el backend.

## Frontend en Vercel

El frontend esta en la carpeta `frontend`.

Configuracion recomendada en Vercel:

- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`

Variable requerida:

```text
VITE_API_URL=https://tu-backend-desplegado.com
```

En desarrollo local puede quedar:

```text
VITE_API_URL=http://localhost:8000
```

## Backend

El backend es FastAPI y debe desplegarse como un servicio Python persistente, por ejemplo en Render, Railway, Fly.io o un servidor propio.

Variables requeridas para el backend:

```text
GROQ_API_KEY=...
NOTION_API_KEY=...
NOTION_DATABASE_ID=...
```

Si luego se migra de Groq a OpenAI, se debe agregar:

```text
OPENAI_API_KEY=...
```

## Flujo recomendado

1. Desplegar backend FastAPI en Render/Railway/Fly.io.
2. Copiar la URL publica del backend.
3. Crear proyecto en Vercel usando el directorio `frontend`.
4. Configurar `VITE_API_URL` con la URL del backend.
5. Redeploy del frontend.

## Por que no se suben secretos al repo

Si una llave queda en GitHub, puede ser copiada por terceros, usada para consumir creditos o modificar recursos externos como Notion. La practica profesional es mantener secretos fuera del codigo y administrarlos desde el entorno de despliegue.
