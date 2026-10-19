# API de usuarios — guía del proyecto

API REST de ejemplo (FastAPI + Pydantic v2). Almacén en memoria, sin base de datos:
el proyecto corre sin infraestructura.

## Estructura

- `main.py` — crea la app y monta los routers.
- `users/` — recurso de ejemplo. Cada recurso sigue el mismo patrón:
  - `routes.py` — rutas HTTP. Sin lógica de negocio: delega en `service.py`.
  - `service.py` — lógica de negocio. Única capa que habla con `repository.py`.
  - `schemas.py` — modelos Pydantic de entrada (`*Create`) y salida.
  - `repository.py` — acceso a datos (aquí, un `dict` en memoria).
- `core/errors.py` — catálogo de errores. Toda respuesta de error sale de aquí.
- `core/pagination.py` — modelo genérico `Page[T]` y función `paginate()`. Toda lista
  paginada pasa por aquí.
- `tests/` — un archivo por recurso: `test_<recurso>.py`.

## Convenciones

- Las rutas declaran `response_model=` y devuelven modelos Pydantic, nunca `dict` crudos.
- Los errores se levantan con las funciones de `core/errors.py`
  (`not_found`, `invalid_request`, `already_exists`), no con `HTTPException` a mano.
- La ruta delega en `service.py`; la lógica y las decisiones de error viven ahí.
- Identificadores en inglés y `snake_case`, sin abreviaturas. Mensajes de error en español.
- Cada endpoint nuevo lleva su test en el archivo del recurso, con al menos un caso
  feliz y un caso de error.
- Rutas específicas antes que rutas con parámetro: `/users/search` debe declararse
  **antes** de `/users/{user_id}`.

## Paginación

- Los endpoints de lista paginada reciben `page: int = Query(default=1)` y
  `size: int = Query(default=20)`, sin `ge`/`le`: el recorte no es un error, lo hace
  `paginate`. Un valor no numérico da 422 por la validación de tipo de FastAPI.
- Declaran `response_model=Page[<Modelo>]`. La respuesta es `{items, total, page, size}`
  con `page` y `size` ya recortados.
- El servicio filtra y **ordena por `id` ascendente** y luego llama a
  `core.pagination.paginate(items, page, size)`. `paginate` no filtra ni ordena: solo
  recorta y corta. Nunca se hace el `slice` ni el recorte a mano en rutas ni servicios.
- `paginate` recorta `page` a ≥ 1 y `size` a 1..100, y calcula `total` sobre la lista
  que recibe (ya filtrada). Una página fuera de rango devuelve `items: []` con el
  `total` correcto.
- Los valores por defecto y límites viven como constantes en `core/pagination.py`
  (`DEFAULT_PAGE`, `DEFAULT_SIZE`, `MAX_SIZE`) y las rutas las reutilizan.
- Los tests de límites verifican los **valores literales** del criterio (1, 20, 100),
  no las constantes, para que un cambio accidental de las constantes haga fallar el test.
- Todo endpoint de lista paginada lleva tests de: valores por defecto, recorte de
  `page`/`size`, página fuera de rango (`items: []` y `total` correcto), valor no
  numérico (422) y recorrido completo sin repetir ni saltar elementos.

## Cómo ejecutar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload          # API en http://127.0.0.1:8000  ·  /docs para el Swagger
pytest                             # tests
pytest --cov=. --cov-report=term-missing   # cobertura
ruff check .                       # linter
```

## Fuera de límites

- `migrations/` y `legacy/` — no modificar.
