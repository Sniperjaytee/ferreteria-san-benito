Ferretería San Benito — MVP Quickstart (PostgreSQL + Tailwind)

- Python 3.11+
- Node.js (para compilar Tailwind si deseas recompilar)
- PostgreSQL (por defecto)

Run locally (Windows/macOS/Linux)

1) Crear venv e instalar dependencias
   - Windows: `py -m venv venv && .\venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv venv && source venv/bin/activate`
   - Instalar: `pip install -r requirements.txt`

2) Configurar base de datos PostgreSQL (por defecto)
   - Crea la BD: `createdb db_ferreteria` (o desde PgAdmin)
   - Variables opcionales (si tus credenciales/host son distintos):
     - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
   - Aplicar migraciones: `python manage.py migrate`
   - Crear admin: `python manage.py createsuperuser`

3) Poblar datos demo (descarga imágenes)
   - `python manage.py seed_demo_catalog`
   - Opcional limpieza (si ya existían categorías de pruebas): `python manage.py clean_demo_catalog`

4) Ejecutar el sitio
   - `python manage.py runserver`
   - App: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

Opcional: usar SQLite (rápido sin Postgres)

Exporta `USE_SQLITE=1` y vuelve a migrar/levantar:
- `USE_SQLITE=1`

Tailwind (CSS)

- Ya hay CSS compilado. Para ver cambios al vuelo: `python manage.py tailwind start`
- Si no tienes Node, instala desde `theme/static_src`: `cd theme/static_src && npm install && cd ../..`

Qué incluye el MVP

- Inicio con destacados y categorías (core/index)
- Listado y detalle de productos (catalogo)
- Carrito, vista y checkout básico (pedidos)
- Selector de moneda y conversión básica
- Admin con tema Jazzmin
