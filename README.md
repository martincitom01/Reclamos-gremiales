# Reclamos-gremiales

Instrucciones y notas rápidas para desplegar en Netlify.

## Despliegue en Netlify (Frontend)

Pasos mínimos para desplegar la aplicación frontend en Netlify:

- En la configuración del sitio en Netlify, establecer la carpeta base a `frontend`.
- Comando de build: `yarn build` (o `npm run build` si usas npm).
- Carpeta a publicar: `build`.
- Añadir la variable de entorno `REACT_APP_BACKEND_URL` apuntando a la URL del backend (por ejemplo, `https://api.midominio.com`).
- Netlify ya aplica la regla SPA vía `netlify.toml` y `frontend/public/_redirects` incluidos en este repo.

Comandos locales para comprobar el build:

```bash
cd frontend
yarn install
yarn build
```

### Notas sobre el backend

El backend actual está implementado con FastAPI en la carpeta `backend/` y usa MongoDB. Netlify es ideal para el frontend estático; para usar Netlify Functions sería necesario migrar los endpoints de `backend/` a funciones serverless o desplegar el backend en otro proveedor (Heroku, Railway, DigitalOcean, etc.) y configurar `REACT_APP_BACKEND_URL` apuntando a esa URL.

## Despliegue automático (GitHub Actions → Netlify)

He añadido un workflow en `.github/workflows/deploy_netlify.yml` que construye `frontend` y despliega el contenido de `frontend/build` a Netlify.

Requisitos para que el workflow funcione:

- Crear dos secretos en el repositorio (Settings → Secrets):
  - `NETLIFY_AUTH_TOKEN` — token personal de Netlify (User settings → Applications → Personal access tokens).
  - `NETLIFY_SITE_ID` — el Site ID del sitio Netlify (lo encuentras en Site settings → Site information).

Una vez configurados los secretos, el workflow se ejecutará automáticamente en cada push a `main` o manualmente desde la pestaña "Actions".

Si prefieres que haga el primer deploy por ti, comparte `NETLIFY_AUTH_TOKEN` y `NETLIFY_SITE_ID` por un canal seguro o configúralos en el repositorio y ejecuto el workflow manualmente.
# Reclamos-gremiales

Instrucciones y notas rápidas para desplegar en Netlify.

## Despliegue en Netlify (Frontend)

Pasos mínimos para desplegar la aplicación frontend en Netlify:

- En la configuración del sitio en Netlify, establecer la carpeta base a `frontend`.
- Comando de build: `yarn build` (o `npm run build` si usas npm).
- Carpeta a publicar: `build`.
- Añadir la variable de entorno `REACT_APP_BACKEND_URL` apuntando a la URL del backend (por ejemplo, `https://api.midominio.com`).
- Netlify ya aplica la regla SPA vía `netlify.toml` y `frontend/public/_redirects` incluidos en este repo.

Comandos locales para comprobar el build:

```bash
cd frontend
yarn install
yarn build
```

### Notas sobre el backend

El backend actual está implementado con FastAPI en la carpeta `backend/` y usa MongoDB. Netlify es ideal para el frontend estático; para usar Netlify Functions sería necesario migrar los endpoints de `backend/` a funciones serverless o desplegar el backend en otro proveedor (Heroku, Railway, DigitalOcean, etc.) y configurar `REACT_APP_BACKEND_URL` apuntando a esa URL.
# Here are your Instructions
