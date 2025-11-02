## Propósito
Breve guía para agentes de IA que colaboren en este repositorio Django + Tailwind. Contiene el "big picture", flujos de desarrollo, convenciones del proyecto y puntos clave a revisar antes de editar código.

## Visión general del proyecto
- Proyecto Django (generado con Django 5.2.5). Archivo principal de configuración: `ferreteria_sbenito/settings.py`.
- Estructura modular: las apps están en la carpeta `apps/` (ej.: `apps/core`, `apps/catalogo`, `apps/pedidos`). El proyecto añade `apps/` al `sys.path` en `settings.py`, por eso los imports y `include()` usan el namespace `apps.<app>`.
- Frontend con Tailwind vía la app `theme` y la dependencia `tailwind` (django-tailwind). Fuente de assets: `theme/static_src/` (ver `package.json`). La salida compilada de CSS se escribe en `theme/static/css/dist/styles.css`.
- Base de datos por defecto: SQLite en `db.sqlite3`. Static files: `STATICFILES_DIRS = [ BASE_DIR / 'static' ]` y `STATIC_ROOT = BASE_DIR / 'staticfiles'`.

## Flujo de desarrollo y comandos (Windows - cmd.exe)
- Crear y activar entorno virtual:
  - `python -m venv venv`
  - `\.\venv\Scripts\activate`
- Dependencias Python: este repositorio no incluye `requirements.txt`. Asumir al menos `Django==5.2.5` y `django-tailwind` y añadir un `requirements.txt` si vas a instalar paquetes.
- Frontend (Tailwind/PostCSS): ir a `theme\static_src` y ejecutar `npm install`. Las tareas de npm están en `theme/static_src/package.json`:
  - Desarrollo (watch): `npm run dev`  (equivalente a `postcss ./src/styles.css -o ../static/css/dist/styles.css --watch`)
  - Build: `npm run build`
- Comandos Django útiles (en la raíz del proyecto, con venv activado):
  - `python manage.py migrate`
  - `python manage.py createsuperuser`
  - `python manage.py tailwind start`  (inicia el watcher integrado por django-tailwind)
  - `python manage.py runserver`

## Convenciones y patrones del código
- Apps están dentro de `apps/` y se importan como `apps.<app>`. Ver esta línea en `settings.py`:
  - `sys.path.insert(0, str(BASE_DIR / 'apps'))`
- Las URLs principales se configuran en `ferreteria_sbenito/urls.py` y hacen `include(('apps.core.urls','core'))` para enrutar `apps/core/urls.py`.
- Templates globales en `templates/`, templates por app en `apps/<app>/templates/` (la configuración de TEMPLATES tiene `APP_DIRS=True`).
- Estilo del frontend: Tailwind con PostCSS. Archivo fuente principal: `theme/static_src/src/styles.css`.

## Puntos delicados detectados (lo que debes revisar antes de cambiar)
- `SECRET_KEY` está embebida en `settings.py`. No divulgar ni comprometer; si vas a publicar cambios, extraerla a variables de entorno.
- `DEBUG = True` en settings; revisa antes de preparar despliegues.
- `INTERNAL_IPS` contiene una probable errata: `"1227.0.0.1"` (debería ser `"127.0.0.1"`). Verifica antes de usar debug toolbar u otras herramientas que dependan de esta variable.
- `requirements.txt` está ausente aunque `arranque.txt` sugiere usarlo. Si vas a instalar dependencias automáticas, crea y mantiene `requirements.txt`.

## Integraciones externas y puntos de fusión
- django-tailwind: la app `tailwind` está en `INSTALLED_APPS` y `TAILWIND_APP_NAME = 'theme'` en `settings.py`.
- Node.js / npm: necesario para compilar CSS. `NPM_BIN_PATH` ya apunta a `C:\Program Files\nodejs\npm.cmd` en `settings.py`.
- PostCSS + tailwindcss + postcss-cli en `theme/static_src/package.json` (devDependencies).

## Archivos clave a revisar (ejemplos)
- `ferreteria_sbenito/settings.py` — configuración global (sys.path, INSTALLED_APPS, STATIC, TAILWIND_APP_NAME)
- `ferreteria_sbenito/urls.py` — enrutamiento principal
- `apps/core/urls.py`, `apps/core/views.py` — página principal (`index`)
- `theme/static_src/package.json` — scripts npm y flujo de compilación Tailwind
- `arranque.txt` — guía local del autor con pasos de setup útiles

Si alguna sección quedó incompleta o quieres que añada ejemplos de `requirements.txt` o snippets de configuración para CI (p. ej. cómo arrancar tailwind en GitHub Actions), dime qué prefieres y lo agrego.
