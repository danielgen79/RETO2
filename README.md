# m2-api-base

API REST de usuarios y reportes construida con **FastAPI** y **Pydantic v2**. Los datos
viven en memoria (sin base de datos): el proyecto corre sin infraestructura y cada
arranque parte de los datos semilla (4 usuarios).

Es un proyecto pequeño con capas separadas, catálogo de errores, paginación compartida
y una suite de tests. Las convenciones del código están en [`CLAUDE.md`](CLAUDE.md).

## Instalación y ejecución (Windows)

Requiere Python 3.10 o superior.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload
```

- API: <http://127.0.0.1:8000>
- Documentación interactiva (Swagger): <http://127.0.0.1:8000/docs>

En Linux o macOS, activa el entorno con `source .venv/bin/activate`.

## Tests, lint y cobertura

```bash
pytest                                       # suite de tests
ruff check .                                 # linter
pytest --cov=core --cov=users --cov=reports --cov-branch --cov-report=term-missing   # cobertura
```

## Endpoints

| Método | Ruta                   | Descripción                                                    |
|--------|------------------------|----------------------------------------------------------------|
| GET    | `/health`              | Estado del servicio                                            |
| GET    | `/users`               | Lista paginada de usuarios                                     |
| GET    | `/users/{user_id}`     | Un usuario por id (404 si no existe)                           |
| POST   | `/users`               | Crea un usuario (201; 409 si el email ya existe; 422 si es inválido) |
| GET    | `/reports`             | Lista paginada de reportes; filtro opcional `?user_id=`        |
| GET    | `/reports/export`      | Exporta los reportes a CSV en el servidor (requiere cabecera `X-Export-Token`; 401 si es inválido) |
| GET    | `/reports/{report_id}` | Un reporte por id (404 si no existe)                           |
| POST   | `/reports`             | Crea un reporte (201; 422 si el cuerpo supera 500 caracteres)  |

El token de `/reports/export` se lee de la variable de entorno `EXPORT_API_TOKEN` y el
directorio de salida de `EXPORT_DIR` (por defecto `exports`).

## Paginación

`GET /users` y `GET /reports` están paginados. Ambos pasan por una única función
compartida, `core/pagination.py::paginate`.

### Parámetros

| Parámetro | Tipo | Por defecto | Notas                                                    |
|-----------|------|-------------|----------------------------------------------------------|
| `page`    | int  | 1           | Un valor menor que 1 se recorta a 1                      |
| `size`    | int  | 20          | Se recorta al rango 1..100                               |
| `user_id` | int  | —           | Solo en `/reports`: filtra antes de paginar              |

El recorte no es un error. Un valor no numérico o vacío (`page=abc`, `size=2.5`,
`?page=`) responde **422**.

### Forma de la respuesta

```json
{ "items": [...], "total": 4, "page": 1, "size": 20 }
```

`page` y `size` son los valores ya recortados. `size` es el tamaño aplicado, no el número
de items devueltos. `total` cuenta todos los registros que cumplen el filtro, no solo los
de la página.

### Ejemplos

> **PowerShell:** `curl` es un alias de `Invoke-WebRequest`, con otra sintaxis y otra
> salida. Usa `curl.exe` en su lugar. En `cmd` funciona `curl` tal cual.
>
> Los valores de `created_at` de los ejemplos son ilustrativos: no son fijos, cada
> registro guarda la hora en que se creó (los usuarios semilla, la del arranque del
> servidor), así que en tu respuesta serán distintos.

Usuarios, página 1 de tamaño 2:

```bash
curl "http://127.0.0.1:8000/users?page=1&size=2"
```

```json
{
  "items": [
    {"name": "Ada Lovelace", "email": "ada@example.com", "id": 1, "created_at": "2026-01-01T10:00:00Z"},
    {"name": "Alan Turing", "email": "alan@example.com", "id": 2, "created_at": "2026-01-01T10:00:00Z"}
  ],
  "total": 4,
  "page": 1,
  "size": 2
}
```

Recorte silencioso: `size=500` se aplica como 100.

```bash
curl "http://127.0.0.1:8000/users?size=500"
# → {"items": [...], "total": 4, "page": 1, "size": 100}
```

Al arrancar no hay reportes (`GET /reports` responde `items: []` y `total: 0`). Crea
algunos antes de listarlos. Ejemplo para `cmd` de Windows, con las comillas dobles del
JSON escapadas (repítelo cambiando `title` para crear varios):

```bat
curl -X POST "http://127.0.0.1:8000/reports" -H "Content-Type: application/json" -d "{\"user_id\": 1, \"title\": \"reporte 0\", \"body\": \"algo pasó\"}"
```

Reportes de un usuario, paginados (`total` cuenta solo los de ese usuario). El resultado
depende de los reportes que hayas creado; el de abajo supone 5 reportes del usuario 1:

```bash
curl "http://127.0.0.1:8000/reports?user_id=1&page=1&size=2"
```

```json
{
  "items": [
    {"user_id": 1, "title": "reporte 0", "body": "algo pasó", "id": 1, "created_at": "2026-01-01T10:00:00Z"},
    {"user_id": 1, "title": "reporte 1", "body": "algo pasó", "id": 2, "created_at": "2026-01-01T10:00:00Z"}
  ],
  "total": 5,
  "page": 1,
  "size": 2
}
```

Valor no numérico:

```bash
curl -i "http://127.0.0.1:8000/users?page=abc"
```

```
HTTP/1.1 422 Unprocessable Content
```

```json
{"detail":[{"type":"int_parsing","loc":["query","page"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"abc"}]}
```

### Criterios de aceptación

Los tests citan estos códigos (CA-XX) en sus docstrings, así que se puede ir de un test
al criterio que verifica. Están definidos en `EVIDENCIA.md`, sección 1.

| ID    | Criterio |
|-------|----------|
| CA-01 | `GET /users` y `GET /reports` aceptan `?page=` y `?size=`, ambos opcionales. |
| CA-02 | Valores por defecto: `page=1`, `size=20`. |
| CA-03 | `size` se recorta al rango 1..100 (`size=0` o negativo → 1; `size=1000` → 100) y `page` menor a 1 se recorta a 1. El recorte no devuelve error. |
| CA-04 | Valores no numéricos o vacíos (`page=abc`, `size=2.5`, `?page=`) → 422. |
| CA-05 | La respuesta es `{items, total, page, size}`, con `page` y `size` ya recortados. `size` es el tamaño aplicado, no el número de items devueltos. |
| CA-06 | `total` cuenta todos los registros que cumplen el filtro, no solo los de la página. |
| CA-07 | En `GET /reports`, `?user_id=` se combina con la paginación. Un `user_id` sin reportes (o inexistente) → 200 con `items: []` y `total: 0`. |
| CA-08 | Una página fuera de rango → 200 con `items: []` y el `total` correcto. |
| CA-09 | El orden es estable por `id` ascendente: recorrer todas las páginas no repite ni salta elementos. |
| CA-10 | La paginación vive en una sola función compartida, `core/pagination.py::paginate`, que solo recorta y corta. Cada servicio filtra y ordena por `id` antes de llamarla. |

### Comportamientos a tener en cuenta

- **El recorte es silencioso.** Si pides `size=500`, la API responde 200 y no avisa: el
  cliente lo detecta mirando el `size` de la respuesta.
- **Un `user_id` sin reportes (o inexistente) da 200 con `total: 0`**, no 404.
- **El orden por `id` garantiza un recorrido estable** (sin repetir ni saltar elementos)
  mientras no haya borrados entre una petición y la siguiente. La API no ofrece borrado
  hoy; si se añade, habría que revisar esta garantía.

### Cambio incompatible

`GET /users` y `GET /reports` pasaron de devolver una lista (`[...]`) a devolver un
objeto paginado (`{items, total, page, size}`). Los clientes existentes deben leer los
elementos desde `items`.

## Estructura del proyecto

```
main.py              crea la app y monta los routers
core/
  errors.py          catálogo de errores (not_found, invalid_request, already_exists, ...)
  pagination.py      Page[T], paginate() y las constantes de paginación
users/               recurso de usuarios
reports/             recurso de reportes (incluye export.py)
  routes.py          rutas HTTP, sin lógica de negocio
  service.py         lógica de negocio; única capa que habla con repository.py
  schemas.py         modelos Pydantic de entrada y salida
  repository.py      acceso a datos (dict en memoria)
tests/               un archivo por recurso (test_<recurso>.py) y test_pagination.py
migrations/, legacy/ fuera de límites: no modificar
```

Las convenciones (capas, errores, nombres, paginación, tests) están en
[`CLAUDE.md`](CLAUDE.md). Léelo antes de contribuir.

## Extensiones futuras

Si aparece un tercer recurso paginado, conviene extraer `page` y `size` a una
dependencia compartida de FastAPI (por ejemplo `PaginationParams`) en vez de repetir las
dos declaraciones `Query(...)` en cada ruta.
