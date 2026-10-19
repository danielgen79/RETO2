# Registro de cambios

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto sigue [Versionado Semántico](https://semver.org/lang/es/).

## [Sin publicar]

## [0.2.0] - 2026-10-19

### Cambiado

- **Cambio incompatible:** `GET /users` y `GET /reports` devuelven un objeto paginado
  `{items, total, page, size}` en lugar de una lista. Los clientes existentes deben leer
  los elementos desde `items`.

### Agregado

- Parámetros `page` y `size` en `GET /users` y `GET /reports`, ambos opcionales, con
  valores por defecto `page=1` y `size=20`. `page` menor que 1 se recorta a 1 y `size`
  se recorta al rango 1..100; el recorte no es un error. Un valor no numérico responde 422.
- `core/pagination.py` con el modelo genérico `Page[T]` y la función `paginate`, que
  comparten ambos endpoints.
- Combinación de la paginación con `?user_id=` en `GET /reports`: `total` cuenta los
  reportes ya filtrados.
- Convención de Paginación en `CLAUDE.md`.
- Tests de paginación unitarios (`tests/test_pagination.py`) y de integración para
  `GET /users` y `GET /reports`.
- Test del caso feliz de `GET /reports/{report_id}`.

### Documentación

- `README.md` reescrito, con ejemplos verificados contra la API y la tabla de criterios
  de aceptación CA-01 a CA-10.
