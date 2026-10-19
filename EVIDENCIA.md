# Evidencia del proceso — Reto Módulo 2

**Feature:** C · Paginación en GET /users y GET /reports
**Rama:** reto-m2 (base: solucion-clase4)
**Herramienta:** Claude Code

## 0. Línea base

Rama "reto-m2" creada desde "solucion-clase4". Dependencias instaladas con
pip install -r requirements.txt`.

> pytest
16 passed in 0.26s

> ruff check .
All checks passed!


## 1. Especificación y contexto
### Exploración del repo
Lee CLAUDE.md y explora el repo. Resúmeme la arquitectura: capas, dónde viven
rutas, modelos, servicios/repositorio y tests, y las convenciones que debo
respetar. No modifiques ningún archivo.

**Respuesta de Claude Code:**
Arquitectura de m2-api-base

API REST con FastAPI y Pydantic v2. Los datos viven en memoria, sin base de datos. No modifiqué ningún archivo.

Capas

HTTP → routes.py → service.py → repository.py (dict en memoria)
          │            │
          │            └─ decide los errores de dominio (core/errors.py)
          └─ valida entrada/salida con schemas.py (Pydantic)

┌──────────┬─────────────────────────┬─────────────────────────────────────────────────────────────────────────────┐
│   Capa   │         Archivo         │                               Responsabilidad                               │
├──────────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ Entrada  │ main.py                 │ Crea la FastAPI, monta los routers de users y reports, y expone /health.    │
├──────────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ Rutas    │ <recurso>/routes.py     │ Un APIRouter(prefix=..., tags=[...]). Usa response_model= y delega en el    │
│          │                         │ servicio. No tiene lógica de negocio.                                       │
├──────────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ Servicio │ <recurso>/service.py    │ Lógica de negocio. Es la única capa que habla con repository.py y la que    │
│          │                         │ levanta los errores de dominio.                                             │
├──────────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ Modelos  │ <recurso>/schemas.py    │ Modelos Pydantic: *Base, *Create (entrada) y el modelo de salida, con id y  │
│          │                         │ created_at.                                                                 │
├──────────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ Datos    │ <recurso>/repository.py │ dict más contador de ids en el módulo, con add, get, list_all y reset().    │
│          │                         │ users también tiene find_by_email y datos semilla.                          │
├──────────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
│ Errores  │ core/errors.py          │ Catálogo: not_found (404), invalid_request (422), already_exists (409) y    │
│          │                         │ unauthorized (401).                                                         │
└──────────┴─────────────────────────┴─────────────────────────────────────────────────────────────────────────────┘

Recursos

- users/ es el patrón de referencia, con las rutas GET /users, GET /users/{user_id} y POST /users.
- reports/ sigue el mismo patrón y añade export.py:
  - GET /reports, con filtro opcional ?user_id=.
  - GET /reports/export, que exige la cabecera X-Export-Token.
  - GET /reports/{report_id} y POST /reports.
  - export.py genera el CSV, compara el token con hmac.compare_digest y escribe solo dentro de EXPORT_DIR.
  - reports/repository.py usa un threading.Lock para que los ids sean únicos bajo concurrencia.

Tests

Están en tests/, con un archivo por recurso: test_users.py, test_reports.py y test_export.py. conftest.py tiene dos fixtures:
- _reset_data es autouse y llama a reset() de ambos repositorios antes y después de cada test.
- client devuelve un TestClient(app).

Los nombres de los tests están en español, con el formato test_<accion>_<condicion>_devuelve_<codigo>.

Convenciones a respetar

1. Las rutas declaran response_model= y devuelven modelos Pydantic, nunca dict crudos.
2. Los errores se levantan con las funciones de core/errors.py, no con HTTPException a mano. Las decisiones de error viven en service.py.
3. Las rutas no tienen lógica: delegan en el servicio. El servicio es el único que toca el repositorio.
4. Los identificadores van en inglés, snake_case y sin abreviaturas. Los mensajes de error van en español.
5. Cada endpoint nuevo lleva su test en el archivo del recurso, con al menos un caso feliz y uno de error.
6. Las rutas específicas se declaran antes que las que llevan parámetro. Por ejemplo, /reports/export va antes de /reports/{report_id}, y /users/search iría antes de /users/{user_id}.
7. El linter es ruff (línea de 100, reglas E,F,I,UP,B, Python ≥3.10). pytest corre sobre tests/ con -q.

Fuera de límites

migrations/ y legacy/ no se tocan. También están en .claudeignore.

Desviaciones del código respecto a CLAUDE.md

- HTTPException en rutas: reports/routes.py usa errors.unauthorized(...) directamente en la ruta, no en el servicio. Es la única decisión de error que vive fuera de service.py.
- Excepción de capas: export_reports llama a export.py desde la ruta, sin pasar por service.py. export.py también lee repository directamente, lo que se salta la regla de que solo el servicio habla con el repositorio.
- Identificador en español: nombre en export_to_file rompe la convención de identificadores en inglés.
- Ruta de prueba sin implementar: /users/search aparece en CLAUDE.md, pero no existe todavía en users/routes.py.
- unauthorized sin documentar: CLAUDE.md lista tres funciones de errores, pero core/errors.py tiene también unauthorized.

#### Mis notas sobre la exploración
La exploración cambió mi borrador de criterios en tres puntos:
- **No existe `parse_pagination`** en esta rama. La lógica compartida se creará
  en `core/pagination.py` y requiere una convención nueva en CLAUDE.md.
- **`GET /reports` ya filtra por `?user_id=`**. El `total` debe contar los
  registros filtrados; por eso agregué el criterio CA-07.
- **`users` tiene datos semilla**. Los tests no pueden asumir una lista vacía.

### Criterios de aceptación

Cada criterio es verificable y se traduce en al menos un test, que lo cita
por su identificador (CA-XX).

| ID | Criterio |
|---|---|
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

### Plan de implementación propuesto por la IA
**Prompt:**
Voy a implementar paginación con estos criterios:
  1. GET /users y GET /reports aceptan ?page= y ?size=, ambos opcionales.
  2. Valores por defecto: page=1, size=20.
  3. size se recorta a 1..100 y page menor a 1 se recorta a 1. No devuelven error.
  4. Valores no numéricos (page=abc, size=2.5) → 422.
  5. La respuesta es {items, total, page, size}, con los valores ya recortados en page y size.
  6. total cuenta todos los registros que cumplen el filtro, no solo los de la página.
     7 .En GET /reports, ?user_id= se combina con la paginación.
  8. Una página fuera de rango → 200 con items: [] y el total correcto.
     9 .El orden es estable por id ascendente; recorrer todas las páginas no repite ni salta elementos.
     10.La lógica vive en una sola función compartida en core/ y la usan ambos servicios.
     Antes de escribir código:
  1. Lista los archivos que crearías o modificarías, respetando las capas.
  2. Dime qué tests existentes de test_users.py y test_reports.py se rompen
     al cambiar la respuesta de lista a objeto.
  3. Propón cómo modelar la respuesta paginada en Pydantic para reutilizarla
     en ambos recursos.
  4. Redacta la convención nueva para agregar a CLAUDE.md sobre core/pagination.py.
  5. Señala ambigüedades en mis criterios.
     No implementes nada todavía.
	 
**Respuesta de Claude Code:**
Plan de paginación (sin implementar)

1. Archivos a crear o modificar

┌──────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────┐
│           Archivo            │                                      Cambio                                      │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ core/pagination.py (nuevo)   │ Contiene el modelo Page[T], la función paginate(items, page, size) y las         │
│                              │ constantes DEFAULT_PAGE, DEFAULT_SIZE y MAX_SIZE.                                │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ users/service.py             │ list_users(page, size) llama a paginate(repository.list_all(), ...).             │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ users/routes.py              │ GET /users recibe page y size como Query y declara response_model=Page[User].    │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ reports/service.py           │ list_reports(user_id, page, size) filtra y luego llama a paginate.               │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ reports/routes.py            │ GET /reports recibe page y size además de user_id y declara                      │
│                              │ response_model=Page[Report].                                                     │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ tests/test_pagination.py     │ Tests unitarios de paginate, porque es lógica compartida de core/.               │
│ (nuevo)                      │                                                                                  │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ tests/test_users.py          │ Se ajusta un test y se añaden los casos de paginación de /users.                 │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ tests/test_reports.py        │ Se ajusta un test y se añaden los casos de paginación de /reports.               │
├──────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────┤
│ CLAUDE.md                    │ Se añade la convención nueva (punto 4).                                          │
└──────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────┘

No hace falta tocar repository.py, schemas.py, core/errors.py, main.py ni export.py.

Una decisión de diseño: paginate trabaja sobre una lista ya filtrada y ordenada, así que el servicio sigue siendo la única capa que habla con el repositorio. Hoy el repositorio devuelve los datos en orden de inserción, que coincide con el id ascendente. Aun así, paginate debería ordenar por id de forma explícita para que el criterio 9 no dependa de un detalle del dict.

2. Tests existentes que se rompen

Se rompen dos tests. El resto no cambia, porque solo consultan /users/{id} o /reports/{id}, o crean datos.

- test_users.py::test_list_users_devuelve_los_seed, en la línea 15. len(response.json()) == 4 ahora mide las claves del objeto (items, total, page, size), que son 4. Es una coincidencia: el test pasaría por casualidad con un significado distinto. Hay que cambiarlo a body["total"] == 4 y len(body["items"]) == 4.
- test_reports.py::test_list_reports_filtra_por_user_id, en las líneas 39 a 41. len(cuerpos) == 1 pasa a valer 4 (las claves del objeto) y cuerpos[0] lanza KeyError. Hay que leer cuerpos["items"].

test_export.py no se ve afectado. Tampoco test_ids_unicos_bajo_concurrencia, que usa el repositorio directamente.

3. Modelo Pydantic reutilizable

Un modelo genérico en core/pagination.py (Pydantic v2 admite BaseModel con Generic):

from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

Cada ruta lo usa así: response_model=Page[User] y response_model=Page[Report]. Swagger muestra dos esquemas con nombre propio (Page_User_, Page_Report_).

Firma de la función compartida:

def paginate(items: Sequence[T], page: int, size: int) -> Page[T]

Recorta page y size, ordena por id, corta con un slice y devuelve el Page con los valores ya recortados.

Para recibir los parámetros sin errores por valores fuera de rango, las rutas declaran page: int = Query(default=1) y size: int = Query(default=20). No llevan ge/le, porque eso produciría 422 en lugar de recortar. El recorte lo hace paginate. Los valores no numéricos dan 422 automáticamente por la validación de tipo de FastAPI.

4. Convención nueva para CLAUDE.md

Texto propuesto, para la sección Convenciones y una línea en Estructura:

▎ Estructura: core/pagination.py — modelo genérico Page[T] y función paginate(). Toda lista paginada pasa por aquí.
▎
▎ Paginación:
▎ - Los endpoints de lista paginada reciben page: int = Query(default=1) y size: int = Query(default=20), sin ge/le: el recorte lo hace paginate.
▎ - Declaran response_model=Page[<Modelo>].
▎ - El servicio filtra y luego llama a core.pagination.paginate(items, page, size). Nunca se hace slice a mano en rutas ni servicios, ni se reimplementa el recorte.
▎ - paginate recorta page a ≥1 y size a 1..100, ordena por id ascendente y devuelve Page con total calculado sobre la lista ya filtrada.
▎ - Los valores límite viven como constantes en core/pagination.py. No se repiten en rutas ni en tests.
▎ - Todo endpoint de lista paginada lleva tests de: valores por defecto, recorte de page/size, página fuera de rango (items: [] y total correcto) y valor no numérico (422).

5. Ambigüedades en los criterios

1. size=0, size=-5, size=1000. El criterio 3 dice que se recorta a 1..100. Entiendo que size=0 pasa a 1 y size=1000 pasa a 100. Otra lectura razonable sería que size=0 volviera al valor por defecto de 20. Confirma cuál.
2. Parámetro vacío (?page=). FastAPI lo rechaza como entero inválido y da 422. Confirma que es lo que quieres, o si debe tratarse como ausente.
3. Enteros enormes (page=99999999999999999999). Python los acepta. Con un slice no hay error, pero el cálculo del offset es innecesariamente grande. Propongo aceptarlos y devolver items: [], salvo que prefieras un tope.
4. Qué se considera numérico. size=2.5 da 422 (criterio 4), pero size=+3 o size=03 sí los acepta FastAPI como enteros. Propongo aceptar lo que acepte Pydantic y no añadir reglas propias.
5. user_id sin coincidencias. Criterio 7: user_id para un usuario que no existe, ¿es 200 con total: 0 o 404? Hoy el servicio no valida la existencia del usuario, así que propongo mantener 200 con total: 0.
6. Orden por id en reportes. El criterio 9 dice id ascendente. Hoy el orden de inserción ya lo cumple, pero lo hace por casualidad. Propongo ordenar explícitamente en paginate, lo que exige que cualquier elemento tenga id. ¿Te vale como contrato, o prefieres que paginate reciba una clave de orden?
7. Estabilidad con escrituras concurrentes. "Recorrer todas las páginas no repite ni salta" solo se garantiza si no se crean elementos entre peticiones. Con ids ascendentes y sin borrados, crear elementos nuevos nunca repite ni salta (los nuevos van al final). Si más adelante hay borrados, la garantía cambia. Propongo documentarlo y no tratarlo ahora.
8. Compatibilidad hacia atrás. Cambiar la respuesta de lista a objeto rompe a cualquier cliente existente de GET /users y GET /reports. Confirma que es un cambio aceptado, sin versionado.
9. Criterio 5 y las claves de la respuesta. size devuelve el tamaño solicitado ya recortado, no el número real de items de la página. Es decir, la última página puede tener menos items que size. Lo digo para que no sea una sorpresa.
10. Recorte silencioso. El recorte sin error significa que un cliente con size=500 recibe 100 y solo lo nota leyendo size en la respuesta. Es lo que pides y es coherente con el criterio 5. Solo señalo que es la única señal.

**Hallazgo importante:** `test_list_users_devuelve_los_seed` seguiría pasando
por coincidencia, porque el objeto nuevo también tiene 4 claves. Sin revisar
el plan, el test habría quedado verde midiendo algo distinto.

### Decisiones sobre ambigüedades

Claude Code señaló 10 ambigüedades en la primera versión de los criterios.
Estas fueron mis decisiones:

| Ambigüedad | Decisión | Justificación |
|---|---|---|
| `size=0` | Se recorta a 1 (no vuelve al valor por defecto) | Es la lectura literal de "recortar a 1..100" y da límites claros para testear. |
| `?page=` vacío | 422 | Es el comportamiento estándar de FastAPI; no justifica código extra. |
| Enteros enormes | 200 con `items: []`, sin tope | Python los maneja sin error. |
| Qué es numérico | Lo que acepte Pydantic (`+3`, `03` son válidos) | Evita inventar reglas propias. |
| `user_id` inexistente | 200 con `total: 0` | Mantiene el comportamiento actual del filtro; no romper lo existente. |
| Quién ordena | El servicio, no `paginate` | `paginate` es genérica y no debe asumir que todo `T` tiene `id`. **Corrección a la propuesta de la IA.** |
| Escrituras concurrentes | Se documenta en el README, no se trata ahora | Sin borrados, los ids ascendentes garantizan el criterio CA-09. |
| Lista → objeto | Se acepta como breaking change, con salto de versión en el CHANGELOG | Lo pide la feature; se documenta con honestidad. |
| Recorte silencioso | Se acepta y se documenta en el README | `size` en la respuesta es la señal para el cliente. |
| Constantes en tests | Los tests de límites verifican los valores literales (1, 20, 100), no las constantes | Si los tests importan `MAX_SIZE`, una mutación de 100 a 1000 pasa sin ser detectada. **Corrección a la propuesta de la IA.** |

**Fuera de alcance:** las desviaciones a CLAUDE.md que encontró la
exploración (`HTTPException` en rutas, `export.py` saltándose el servicio,
identificador `nombre`) no se corrigen en esta feature.
### Contexto dado a la IA
**Convención nueva en CLAUDE.md.** La feature introduce core/pagination.py
como lógica compartida, por lo que se agregará una sección de Paginación a
CLAUDE.md antes de generar el código. Así, futuras features (o futuras
sesiones de IA) paginan de la misma forma sin reimplementar el recorte.
### Patrón elegido y justificación
**Patrón:** skeleton-first, ejecutado de forma incremental (una iteración
corta por paso, con revisión del diff y un commit al final de cada una).

**Justificación:**

1. **La feature toca varias capas y dos recursos a la vez.** Son 7 archivos
   entre core/, users/ y reports/. Aprobar primero las firmas, el modelo
   Page[T] y la ubicación de cada responsabilidad permite detectar errores
   de diseño antes de que haya lógica que rehacer.

2. **La decisión de diseño más riesgosa está en las firmas, no en la lógica.**
   La IA propuso que paginate ordenara por id, lo que acoplaba una función
   genérica a un detalle de los recursos actuales. Lo corregí en la etapa de
   diseño (el servicio ordena y paginate solo recorta y corta), antes de
   escribir la implementación.

3. **Hay una trampa conocida en la validación.** Usar Query(ge=1, le=100)
   devolvería 422 en lugar de recortar, contradiciendo el criterio CA-03.
   Revisar la firma de las rutas por separado hace visible esa decisión.

4. **El modo incremental deja el proceso en el historial de git.** Cada
   iteración es un commit pequeño y verificable (pytest + ruff check .),
   lo que facilita revisar el diff completo y documentar qué se aceptó o
   rechazó en cada paso.

**Por qué no test-first:** también era viable, porque los criterios ya están
numerados y son verificables. Pero el contrato de la respuesta (Page[T]) y
la ubicación de la lógica compartida no estaban definidos al inicio, y los
tests habrían dependido de decisiones de diseño todavía abiertas. Con
skeleton-first, las firmas se fijan primero y los tests se escriben después
desde los criterios, no desde la implementación.
## 2. Generación de código
### Iteraciones (prompt → respuesta → revisión → ajuste)
#### Iteración 1 · Convención de paginación en CLAUDE.md
**Prompt:**
Decisiones sobre tu plan:
  - Acepto tus propuestas para las ambigüedades 1-5 y 7-10.
  - Rechazo que paginate ordene por id: paginate solo recorta y corta. El
    servicio filtra y ordena por id antes de llamar a paginate.
  - Rechazo la regla "los valores límite no se repiten en tests": los tests de
    límites deben verificar los valores literales del criterio (1, 20, 100) para
    que una mutación de las constantes sea detectable.

  Actualiza solo CLAUDE.md con la convención de paginación corregida según
  estas decisiones. No toques ningún otro archivo todavía.
**Revisión:** Claude Code propuso dos ediciones y las aprobé una por una.
Verifiqué que la convención incluyera mis dos correcciones: el servicio
ordena por `id` (no `paginate`) y los tests de límites usan valores
literales (1, 20, 100). Además agregó por su cuenta el test de recorrido
completo, que corresponde al criterio CA-09.

**Commit:** `docs: agrega convención de paginación a CLAUDE.md`
#### Iteración 2 · Esqueleto (skeleton-first)
**Prompt:**
Skeleton-first, siguiendo @users/routes.py y @users/service.py como modelo
y la convención de Paginación de @CLAUDE.md:

1. Crea core/pagination.py con el modelo Page[T], las constantes
   DEFAULT_PAGE, DEFAULT_SIZE y MAX_SIZE, y la firma de paginate con su
   docstring, pero con el cuerpo en raise NotImplementedError.
2. Agrega page y size a GET /users y GET /reports, con
   response_model=Page[...], delegando en el servicio.
3. Ajusta las firmas de list_users y list_reports para recibir page y size,
   con el cuerpo en raise NotImplementedError.

No implementes la lógica todavía. No toques los tests.
**Revisión:** aprobé 7 ediciones una por una. Lo que verifiqué:
- Las rutas usan `Query` sin `ge`/`le`, así que los valores fuera de rango
  no darán 422 (CA-03). La IA no cayó en esta trampa porque la convención
  ya estaba en CLAUDE.md: preparar el contexto antes de generar funcionó.
- `GET /reports` conserva `user_id` y la ruta sigue antes de `/export` y de
  `/{report_id}`.
- El esqueleto borró la lógica del filtro por `user_id`. Claude Code lo
  señaló en su resumen; queda como punto a verificar en la implementación
  para no romper CA-07 ni el comportamiento existente.

**Observación:** el mínimo de `size` (1) no tiene constante propia; solo el
máximo. La IA lo detectó y propuso agregar `MIN_SIZE`.

**Resultado:** la app importa sin errores y `ruff check .` pasa. `pytest`
no se ejecutó: las funciones lanzan `NotImplementedError`, como se espera
en esta etapa.

**Commit:** `feat: esqueleto de paginación en GET /users y GET /reports`

#### Iteración 3 · Implementación
**Prompt:**
Implementa la lógica del esqueleto según los criterios CA-01 a CA-10 y la
convención de Paginación de @CLAUDE.md:

1. Agrega MIN_SIZE = 1 en core/pagination.py e implementa paginate:
   recorta page a >= 1 y size a MIN_SIZE..MAX_SIZE, corta con slice y
   devuelve Page con total sobre todos los items recibidos.
2. Implementa list_users: obtiene los usuarios del repositorio, los ordena
   por id ascendente y llama a paginate.
3. Implementa list_reports: restaura el filtro por user_id que se borró en
   el esqueleto, ordena por id ascendente y llama a paginate.

No modifiques los tests todavía. Al terminar corre pytest y ruff check .
y muéstrame el resultado completo, aunque haya tests fallando.

**Revisión:** aprobé las ediciones una por una. Verifiqué:
- El inicio del slice es `(page - 1) * size`.
- `total = len(items)` cuenta la lista completa ya filtrada (CA-06).
- `list_reports` restauró el filtro por `user_id` que borró el esqueleto,
  y lo aplica antes de ordenar y paginar (CA-07).
- Ambos servicios ordenan por `id` antes de llamar a `paginate` (CA-09).

**Code smell detectado:** `paginate` usa `max(page, DEFAULT_PAGE)`, mezclando
el valor por defecto con el mínimo. Lo dejé para el refactor del paso 4
(introducir `MIN_PAGE`).

**Resultado:**
```
1 failed, 15 passed
FAILED tests/test_reports.py::test_list_reports_filtra_por_user_id
ruff check .: All checks passed!
```

**Hallazgo:** se cumplió la predicción del plan.
- `test_list_reports_filtra_por_user_id` falla porque lee la respuesta como
  lista. La lógica es correcta (total: 1, items con el reporte del usuario 1).
- `test_list_users_devuelve_los_seed` **pasa por casualidad**:
  `len(response.json()) == 4` cuenta las 4 claves del objeto
  (items, total, page, size), no los 4 usuarios semilla. Un test en verde
  que ya no verifica lo que dice: verde no es probado.

**Commit:** `feat: implementa paginación en GET /users y GET /reports`

### Decisiones: qué acepté, qué rechacé y por qué
#### Rechazado o corregido

| Propuesta de la IA | Decisión | Por qué |
|---|---|---|
| `paginate` ordena por `id` | **Rechazada.** El servicio filtra y ordena; `paginate` solo recorta y corta. | Una función genérica `Page[T]` no debe asumir que todo `T` tiene `id`. Acoplaba la lógica compartida a un detalle de los recursos actuales. |
| "Los valores límite no se repiten en tests" (convención propuesta para CLAUDE.md) | **Rechazada.** Los tests de límites verifican los valores literales (1, 20, 100). | Si los tests importan `MAX_SIZE`, una mutación de 100 a 1000 cambia también el valor esperado y el test sigue en verde. La regla habría hecho invisibles las mutaciones. |
| Helper de tests `_crear_reportes(client, cantidad)` | **Rechazada.** Renombrado a `_create_reports(client, count)` con `assert` de 201. | Rompía la convención 4 (identificadores en inglés). El `assert` hace que un fallo al crear datos se reporte en su origen. |
#### Aceptado

| Propuesta de la IA | Por qué la acepté |
|---|---|
| Modelo genérico `Page[T]` en `core/pagination.py` | Un solo modelo para ambos recursos, compatible con `response_model=` (convención 1 del repo). |
| `Query` sin `ge`/`le` en las rutas | Con `ge`/`le`, `size=500` daría 422 en lugar de recortarse a 100 (CA-03). |
| 422 nativo de FastAPI para valores no numéricos | Es el comportamiento estándar y no requiere código propio. |
| Constante `MIN_SIZE` (propuesta por la IA al revisar el esqueleto) | Deja ambos límites del rango con nombre y hace explícita la regla. |
| Propuestas para las ambigüedades 1-5 y 7-10 | Ver la tabla "Decisiones sobre ambigüedades" de la sección 1. |

#### Pendiente (detectado en la revisión, se atiende después)

| Hallazgo | Dónde se atiende |
|---|---|
| `paginate` usa `max(page, DEFAULT_PAGE)`: mezcla el valor por defecto con el mínimo. | Refactor del paso 4: introducir `MIN_PAGE`. |
| `test_list_users_devuelve_los_seed` pasa por casualidad (cuenta claves, no usuarios). | Iteración de tests (sección 3). |
| La variable `r` en el filtro de `list_reports` es una abreviatura (convención 4). Viene del código original. | Review del paso 5. |

## 3. Tests y cobertura
### Tests y edge cases
#### Iteración 4 · Corrección de los tests existentes
**Prompt:**
Corrige solo estos dos tests para que lean la respuesta paginada
{items, total, page, size}:

1. test_list_users_devuelve_los_seed: hoy pasa por casualidad porque
   len(response.json()) == 4 cuenta las claves del objeto. Debe verificar
   total == 4 y len(items) == 4.
2. test_list_reports_filtra_por_user_id: debe verificar total == 1,
   len(items) == 1 y que el único item tenga user_id == 1.

No agregues tests nuevos todavía. Al terminar corre pytest y ruff check .

**Cambios:**
- `test_list_users_devuelve_los_seed`: pasaba por casualidad (contaba las 4
  claves del objeto). Ahora verifica `total == 4` y `len(items) == 4`, así que
  falla si la respuesta vuelve a ser lista o si `total` está mal calculado.
- `test_list_reports_filtra_por_user_id`: ahora verifica `total == 1`,
  `len(items) == 1` y que el item sea del usuario 1 (CA-06 y CA-07).
- La IA renombró la variable `cuerpos` a `body`, alineándola con la
  convención 4 (identificadores en inglés).

**Resultado:** `16 passed`, `ruff check .` limpio.

**Commit:** `test: adapta tests de listas a la respuesta paginada`

#### Iteración 5 · Tests unitarios de `paginate`
**Prompt:**
Crea tests/test_pagination.py con tests unitarios de core.pagination.paginate.
Escríbelos desde los criterios, no desde el código:

- Estructura arrange-act-assert, con comentarios # Arrange, # Act, # Assert.
- Cada test con un docstring que cite su criterio, por ejemplo:
  """CA-03: size mayor a 100 se recorta a 100."""
- Nombres en español, siguiendo el estilo del repo:
  test_paginate_<condicion>_<resultado>.
- Los valores esperados van como literales (1, 20, 100), NO importes
  DEFAULT_SIZE, MIN_SIZE ni MAX_SIZE en los tests.
- Usa una lista simple de enteros como items; paginate es genérica.

Casos:
1. size=0 y size negativo → size 1 (CA-03).
2. size=100 se mantiene; size=101 y size=1000 → 100 (CA-03).
3. page=0 y page negativo → page 1 (CA-03).
4. Página 2 con size 10 sobre 25 items devuelve los items 11 a 20 (detecta
   errores en el cálculo del inicio del slice).
5. Última página parcial: página 3 con size 10 sobre 25 items devuelve 5 items
   y size sigue siendo 10 (CA-05).
6. Página fuera de rango → items vacío y total correcto (CA-08).
7. total cuenta todos los items, no solo los de la página (CA-06).
8. Lista vacía → items vacío, total 0.

No toques otros archivos. Al terminar corre pytest y ruff check .

**Resultado:** `tests/test_pagination.py` con 9 tests (14 ejecuciones con
`parametrize`). `30 passed`, `ruff check .` limpio.

(pega aquí la tabla de tests que te dio Claude Code)

**Revisión:**
- Los tests usan valores literales (1, 20, 100), no las constantes, como
  exige la convención corregida.
- El test de la página 2 verifica los valores exactos (11 a 20), no solo
  cuántos items hay, para detectar un error en el cálculo del inicio del slice.
- Confirmé las dos asignaciones de criterio que propuso la IA: el slice de
  la página 2 → CA-09 y la lista vacía → CA-08.
- CA-02 (valores por defecto) no se prueba aquí, porque los valores por
  defecto viven en las rutas, no en `paginate`. Se cubre en los tests de
  endpoints.
- La IA ofreció hacer las mutaciones ella misma; lo rechacé porque el reto
  pide mutaciones a mano.

**Commit:** `test: tests unitarios de paginate`

#### Iteración 6 · Tests de integración de los endpoints
**Prompt:**
Agrega tests de paginación para los endpoints, en tests/test_users.py y
tests/test_reports.py (un archivo por recurso, según CLAUDE.md). Escríbelos
desde los criterios, no desde el código:

- Arrange-act-assert con comentarios, docstring con el criterio (CA-XX),
  nombres con el formato test_<accion>_<condicion>_devuelve_<codigo>.
- Valores esperados como literales; no importes las constantes.
- Recuerda que users tiene 4 usuarios semilla: calcula los totales
  esperados contando con ellos.
- Reutiliza los helpers de payload que ya existen en cada archivo.

En ambos endpoints:
1. Sin parámetros → 200 con page 1 y size 20 (CA-01, CA-02).
2. size=500 → 200 con size 100, no 422 (CA-03).
3. size=0 → 200 con size 1 (CA-03).
4. page=abc, size=2.5 y page vacío → 422 (CA-04).
5. Página fuera de rango → 200, items vacío y total correcto (CA-08).
6. Recorrido completo con size=2: juntar los ids de todas las páginas y
   verificar que no se repiten, no faltan y están en orden ascendente (CA-09).

Solo en /reports:
7. Con 5 reportes del usuario 1 y 2 del usuario 2, user_id=1&size=2 →
   total 5, 2 items y todos del usuario 1 (CA-06, CA-07).
8. user_id de un usuario sin reportes → 200, items vacío y total 0 (CA-07).

No toques el código de la aplicación. Al terminar corre pytest y ruff check .
**Resultado:** 18 ejecuciones nuevas entre `test_users.py` y `test_reports.py`.
`48 passed`, `ruff check .` limpio.

**Revisión:**
- El test de `size=500` espera 200 con `size == 100`, no 422: valida el
  recorte de CA-03 a través de HTTP, confirmando que las rutas no tienen
  `ge`/`le`.
- Los recorridos completos comparan contra la lista exacta de ids
  (`[1, 2, 3, 4]` en users, `[1, 2, 3, 4, 5]` en reports), así que detectan
  repeticiones, saltos y orden incorrecto en una sola aserción (CA-09).
- Los totales de users cuentan los 4 usuarios semilla.
- CA-06 y CA-07 se prueban juntos: 5 reportes del usuario 1 y 2 del usuario
  2, con `user_id=1&size=2` → total 5, 2 items, todos del usuario 1.

**Rechazo:** la primera versión creó el helper `_crear_reportes(client,
cantidad, ...)`. Lo rechacé porque rompe la convención 4 de CLAUDE.md
(identificadores en inglés; solo los nombres de los tests van en español).
También pedí que el helper verifique que cada POST devuelva 201, para que un
fallo al crear datos se reporte en su origen y no como un total incorrecto
más adelante. La IA lo corrigió a `_create_reports(client, count, user_id=1)`.

**Commit:** `test: tests de paginación en GET /users y GET /reports`

### Reporte de cobertura
**Comando** (líneas y ramas, solo los paquetes que tocó la feature):
La cobertura muestra que reports/service.py línea 22 (el return de
get_report) no está cubierta: GET /reports/{report_id} no tiene test del
caso feliz, aunque la convención 5 de CLAUDE.md lo pide. Es un hueco
preexistente, no de la paginación.

Agrega en tests/test_reports.py un solo test:
test_get_report_existente_devuelve_200, que cree un reporte con
_create_reports, lo pida por su id y verifique 200, el id y el user_id.
Mismo estilo: arrange-act-assert y docstring. No toques nada más.
Corre pytest y ruff check .

**Primera medición (después de la iteración 6):**
```
core\pagination.py         14      0      0      0   100%
reports\routes.py          22      0      2      0   100%
reports\service.py         20      1      6      1    92%   22
users\routes.py            14      0      0      0   100%
users\service.py           16      0      4      0   100%
TOTAL                     180      1     20      1    99%
```

La línea 22 de `reports/service.py` era el `return` de `get_report`, que no
forma parte de la feature: `GET /reports/{report_id}` no tenía test del caso
feliz, aunque la convención 5 de CLAUDE.md lo pide. Era un hueco preexistente
(la línea base también marcaba 99%).

#### Iteración 7 · Cierre del hueco preexistente
**Prompt:**
```
(pega aquí el prompt del test de get_report)
```
Se agregó `test_get_report_existente_devuelve_200`. Usa `user_id=2` (no el
valor por defecto del helper) para demostrar que el dato viene del reporte
creado.

**Nota:** Claude Code sugirió verificar con `pytest --cov=.`, pero ese comando
mide todo el repo y no incluye `--cov-branch`. Mantuve el comando con ramas.

**Medición final:**
```
(pega aquí la tabla completa de la última medición)
49 passed
```

**Observación:** `core/pagination.py` marca 0 ramas porque `min()` y `max()`
no generan ramas para coverage, aunque internamente deciden el recorte. Un
100% de ramas no garantiza que los límites estén bien probados; por eso se
complementa con mutaciones a mano.

**Commit:** `test: caso feliz de GET /reports/{report_id} (hueco preexistente)`
### Mutaciones a mano
#### Mutación 1 · Límite máximo de size
**Cambio:** `core/pagination.py`: `MAX_SIZE = 100` → `MAX_SIZE = 1000`.

**Resultado:** **detectada**. 4 tests fallaron:
```
FAILED tests/test_pagination.py::test_paginate_size_mayor_a_100_se_recorta_a_100[101] - assert 101 == 100
FAILED tests/test_pagination.py::test_paginate_size_mayor_a_100_se_recorta_a_100[1000] - assert 1000 == 100
FAILED tests/test_reports.py::test_list_reports_size_mayor_a_100_devuelve_200_con_size_100 - assert 500 == 100
FAILED tests/test_users.py::test_list_users_size_mayor_a_100_devuelve_200_con_size_100 - assert 500 == 100
```

**Análisis:**
- La detectan tanto los tests unitarios como los de integración.
- El caso `size=101` detecta incluso un desplazamiento mínimo del límite.
- `test_paginate_size_100_se_mantiene` siguió pasando, como se esperaba:
  protege el otro lado del límite.
- Confirma la corrección hecha a la IA: si los tests importaran `MAX_SIZE`,
  esperarían 1000 y la mutación pasaría sin ser detectada.

**Reversión:** `git restore core/pagination.py` → `49 passed`.

#### Mutación 2 · Inicio del slice
**Cambio:** `core/pagination.py`: `start = (page - 1) * size` → `start = page * size`
(error de desplazamiento: la página 1 empieza donde debería empezar la 2).

**Resultado:** **detectada**. 15 tests fallaron:
FAILED tests/test_pagination.py::test_paginate_size_menor_a_1_se_recorta_a_1[0] - assert [2] == [1]
FAILED tests/test_pagination.py::test_paginate_size_menor_a_1_se_recorta_a_1[-1] - assert [2] == [1]
FAILED tests/test_pagination.py::test_paginate_size_menor_a_1_se_recorta_a_1[-50] - assert [2] == [1]
FAILED tests/test_pagination.py::test_paginate_size_100_se_mantiene - assert 50 == 100
FAILED tests/test_pagination.py::test_paginate_size_mayor_a_100_se_recorta_a_100[101] - assert 50 == 100
FAILED tests/test_pagination.py::test_paginate_size_mayor_a_100_se_recorta_a_100[1000] - assert 50 == 100
FAILED tests/test_pagination.py::test_paginate_page_menor_a_1_se_recorta_a_1[0] - assert [3, 4] == [1, 2]
FAILED tests/test_pagination.py::test_paginate_page_menor_a_1_se_recorta_a_1[-1] - assert [3, 4] == [1, 2]
FAILED tests/test_pagination.py::test_paginate_page_menor_a_1_se_recorta_a_1[-50] - assert [3, 4] == [1, 2]
FAILED tests/test_pagination.py::test_paginate_pagina_2_con_size_10_devuelve_items_11_a_20 - assert [21, 22, 23, 24, 25] == [11, 12, 13, 14, 15, 16, ...]
FAILED tests/test_pagination.py::test_paginate_ultima_pagina_parcial_devuelve_5_items_y_size_10 - assert [] == [21, 22, 23, 24, 25]
FAILED tests/test_reports.py::test_list_reports_filtra_por_user_id - assert 0 == 1
FAILED tests/test_reports.py::test_list_reports_recorrido_completo_devuelve_200_sin_repetir_ni_saltar - assert [3, 4, 5] == [1, 2, 3, 4, 5]
FAILED tests/test_users.py::test_list_users_devuelve_los_seed - assert 0 == 4
FAILED tests/test_users.py::test_list_users_recorrido_completo_devuelve_200_sin_repetir_ni_saltar - assert [3, 4] == [1, 2, 3, 4]

**Análisis:**
- `test_list_users_devuelve_los_seed` falló (`0 == 4`). En su versión
  original, que contaba las claves del objeto, habría pasado: la corrección
  de la iteración 4 hizo que este test detecte errores reales.
- El test de la página 2 compara valores exactos y señala directamente el
  desplazamiento (`[21, ...] == [11, ...]`).
- **Tests que sobrevivieron y revelan una debilidad:**
  `test_list_users_size_0_devuelve_200_con_size_1` y
  `test_list_reports_size_0_devuelve_200_con_size_1` siguieron pasando.
  Verifican `len(items) == 1` pero no *cuál* item: con la mutación
  devolvían el segundo registro en lugar del primero. Verifican cantidad,
  no contenido.
- Los tests de valores por defecto y de página fuera de rango también
  sobrevivieron, como era de esperar: no verifican el contenido de los
  items porque no es su propósito.

**Reversión:** `git restore core/pagination.py` → `49 passed`.

#### Iteración 8 · Fortalecer los tests que sobrevivieron a la mutación 2
**Prompt:**
```
Una mutación manual (start = page * size en paginate) reveló que
test_list_users_size_0_devuelve_200_con_size_1 y
test_list_reports_size_0_devuelve_200_con_size_1 siguen pasando con el
código roto: verifican len(items) == 1, pero no cuál item devuelven.

Fortalece solo esos dos tests: además de lo que ya verifican, que
comprueben que el único item es el primero por orden de id (id == 1).
No toques nada más. Corre pytest y ruff check .
```

**Cambio:** los dos tests de `size=0` ahora también verifican
`items[0]["id"] == 1`, además de la cantidad.

**Verificación:** volví a aplicar la mutación 2 a mano. Ahora fallan **17**
tests (antes 15), incluidos los dos fortalecidos:
```
FAILED tests/test_reports.py::test_list_reports_size_0_devuelve_200_con_size_1 - assert 2 == 1
FAILED tests/test_users.py::test_list_users_size_0_devuelve_200_con_size_1 - assert 2 == 1
```
Ciclo completo: la mutación reveló una debilidad, se corrigió el test y se
comprobó que la corrección detecta el error.

**Aceptado como menor:** Claude Code señaló que los tests de `size` mayor a
100 en los endpoints tampoco verifican qué items devuelven. Decidí no
cambiarlos: su propósito es verificar que la ruta recorta en lugar de
devolver 422, y el contenido de los items ya lo cubren los recorridos
completos y los tests unitarios de `paginate`.

**Nota:** la IA ofreció aplicar la mutación ella misma; la apliqué a mano.

**Commit:** `test: tests de size=0 verifican el item devuelto, no solo la cantidad`
## 4. Debugging y refactorización
### Bug
**Origen del bug:** durante el desarrollo no apareció ningún bug real (el
único test que falló tras la implementación era un fallo previsto por el
cambio de formato). Como contempla el reto, **introduje un bug a propósito**
para practicar el debugging asistido: en `list_reports`, filtrar por
`user_id` **después** de paginar en lugar de antes. Es un error realista en
paginación, que puede pasar por una "optimización" inocente.

```python
reports = sorted(repository.list_all(), key=lambda report: report.id)
result = paginate(reports, page, size)
if user_id is not None:
    result.items = [report for report in result.items if report.user_id == user_id]
return result
```

**Síntoma:**
```
FAILED tests/test_reports.py::test_list_reports_filtra_por_user_id - assert 2 == 1
FAILED tests/test_reports.py::test_list_reports_user_id_con_paginacion_devuelve_200_con_total_del_filtro - assert 7 == 5
FAILED tests/test_reports.py::test_list_reports_user_id_sin_reportes_devuelve_200_con_items_vacio - assert 3 == 0
```
Patrón: en los tres casos `total` es mayor al esperado, y solo fallan los
tests que combinan el filtro con la paginación.

**Prompt (hipótesis antes que fix):**
Tengo 3 tests fallando en tests/test_reports.py:

FAILED test_list_reports_filtra_por_user_id - assert 2 == 1
FAILED test_list_reports_user_id_con_paginacion_devuelve_200_con_total_del_filtro - assert 7 == 5
FAILED test_list_reports_user_id_sin_reportes_devuelve_200_con_items_vacio - assert 3 == 0

Detalle de uno de ellos:
(pega aquí el bloque completo del fallo)

Comportamiento esperado (CA-06 y CA-07): total cuenta solo los reportes
que cumplen el filtro por user_id, no todos.

Antes de proponer cualquier fix:
1. Dame 2 o 3 hipótesis de la causa, ordenadas por probabilidad.
2. Para cada una, dime cómo confirmarla o descartarla.
Diagnostica a partir del trace y del código actual, sin revisar el
historial de git. No modifiques ningún archivo todavía.

**Hipótesis de la IA:**
1. El filtro se aplica después de `paginate`, así que `total` cuenta todos
   los reportes (muy probable). Explicaba los tres números del trace.
2. `Page` permite reasignar `items` sin revalidar, lo que deja un objeto
   incoherente sin lanzar error (síntoma relacionado, no la causa).
3. Los tests están mal planteados (descartada: contradice CA-06 y CA-07).

**Confirmación:** ejecuté la prueba propuesta por la IA antes de aplicar el fix:
```
> python -c "... service.list_reports(1, 20, user_id=99) ..."
2 []
```
`total` = 2 (sin filtrar) e `items` vacío (filtrado): hipótesis 1 confirmada.

**Fix mínimo:** filtrar → ordenar → paginar, sin reasignar `result.items`.
`git diff` contra el último commit muestra que el fix restauró el código
original; el único cambio neto es `r` → `report`, que además resuelve el
pendiente de la convención 4.

**Test de regresión:** no hizo falta crear uno nuevo. Los tres tests que
detectaron el bug (CA-06 y CA-07) son los que protegen este caso.

**Resultado:** `49 passed`, `ruff check .` limpio.

**Limitación del ejercicio:** Claude Code reconoció que el archivo "no
coincidía con lo que había dejado", es decir, recordaba su propia versión
del código dentro de la sesión. Ante un bug real no tendría esa ventaja.
Para un diagnóstico más limpio habría convenido usar una sesión nueva o
`/clear` antes de presentar el trace.

**Commit:** `fix: list_reports filtra antes de paginar (ejercicio de debugging)`
### Refactor
**Code smell:** detecté al revisar el diff de la implementación (iteración 3)
que `paginate` usaba `max(page, DEFAULT_PAGE)`. Mezclaba dos conceptos: el
valor por defecto de `page` y el mínimo permitido. Hoy ambos valen 1, pero si
alguien cambiara `DEFAULT_PAGE`, el mínimo cambiaría sin querer.

**Prompt:**
Refactor (cambio de forma, no de comportamiento): en core/pagination.py,
paginate usa max(page, DEFAULT_PAGE), que mezcla el valor por defecto con
el mínimo permitido. Hoy ambos valen 1, pero son conceptos distintos.

1. Agrega la constante MIN_PAGE = 1 junto a las demás y úsala en paginate.
2. Ajusta el docstring de paginate para que mencione MIN_PAGE.
3. En CLAUDE.md, la convención de Paginación lista DEFAULT_PAGE,
   DEFAULT_SIZE y MAX_SIZE: agrega MIN_PAGE y MIN_SIZE, que también existe
   y no está documentada.

No toques los tests ni ningún otro archivo. Corre pytest y ruff check .

**Cambios:**
- `core/pagination.py`: nueva constante `MIN_PAGE = 1`; `paginate` recorta
  con `max(page, MIN_PAGE)`; el docstring la menciona.
- `CLAUDE.md`: la convención ahora lista las cinco constantes (`MIN_SIZE`
  existía desde la implementación pero no estaba documentada: otro desfase
  entre código y documentación). La IA agregó por su cuenta una regla
  explícita: el recorte usa `MIN_*`/`MAX_SIZE`, nunca los `DEFAULT_*`. La
  acepté porque convierte el code smell en una convención escrita.

**Tests como red de seguridad:**
```
Antes del refactor:  pytest -q → 49 passed
Después del refactor: pytest -q → 49 passed
```
Los tests no se modificaron. Como verifican valores literales (1, 20, 100) y
no las constantes, cualquier cambio accidental de comportamiento durante el
refactor los habría hecho fallar.

**Commit:** `refactor: separa MIN_PAGE de DEFAULT_PAGE en paginate`
## 5. Documentación y review
### Hallazgos del review
**Preparación:** usé `/clear` antes del review para que Claude Code revisara
la rama sin el contexto de haber escrito el código (lección del ejercicio
de debugging).

**Prompt:**
Revisa mi rama como si fuera un pull request ajeno. Compara contra la
rama base con: git diff solucion-clase4...reto-m2
Ignora EVIDENCIA.md: no es código.

Lee CLAUDE.md para conocer las convenciones del proyecto. La feature
agrega paginación a GET /users y GET /reports.

Revisa por categorías:
1. Correctitud
2. Seguridad
3. Manejo de errores
4. Consistencia con CLAUDE.md
5. Tests
6. Legibilidad y mantenibilidad

Para cada hallazgo indica: archivo y línea, severidad (alta, media, baja),
descripción y sugerencia. Si una categoría no tiene hallazgos, dilo
explícitamente. No modifiques ningún archivo.

**Resultado:** sin hallazgos de severidad alta. Seguridad y manejo de
errores, sin hallazgos. 13 hallazgos de severidad media o baja.

**Verificación de una afirmación de la IA:** el review dijo que no pudo
correr ruff "porque no está instalado". En realidad lo ejecutó fuera del
`.venv`. Ruff sí está instalado y pasa limpio.

**Clasificación:**

| # | Hallazgo | Severidad | Clasificación | Por qué |
|---|---|---|---|---|
| 1 | `page` enorme crea un entero grande | Baja | Aceptado como menor | Decidido en las ambigüedades: Python lo maneja y devuelve `items: []`. |
| 2 | `Sequence[T]` admite `str` | Baja | Aceptado como menor | Riesgo teórico; ningún llamador pasa texto. |
| 3 | Orden de parámetros en `list_reports` | Baja | Aceptado como menor | El único llamador es la ruta, que usa keywords. |
| 4 | Rename `r` → `report` mezclado con el fix | Baja | Aceptado como menor | Documentado en la evidencia del bug. |
| 5 | Nombres de tests en español | Baja | Falso positivo | Es la convención del repo. |
| 6 | Falta recorte de `page` por endpoint | Media | **Arreglado** | Mi propia convención en CLAUDE.md lo pide por endpoint. Se agregaron tests con `page=0` y `page=-5` en ambos recursos. |
| 7 | `size=500` solo verifica `size` | Media | Aceptado como menor | Mantengo la decisión de la iteración 8: el test unitario ya verifica `len(items) == 100`; repetirlo exigiría crear 101 registros sin cubrir una capa nueva. |
| 8 | Falta caso de última página completa | Baja | Aceptado como menor | Los tests de offset fijan valores exactos; la mutación 2 lo confirmó. |
| 9 | `_create_reports` definido después de usarse | Baja | **Arreglado** | Movido junto a `_payload`. |
| 10 | Tests asumen 4 usuarios semilla | Baja | Aceptado como menor | La semilla es dato fijo del proyecto y se declara en el Arrange. |
| 11 | `Query` repetido en ambas rutas | Baja | Aceptado como menor | Con dos recursos no se justifica una abstracción; se menciona en el README como extensión futura. |
| 12 | Sintaxis moderna `class Page[T]` | Baja | Falso positivo | Requiere Python ≥ 3.12; CLAUDE.md exige compatibilidad desde 3.10. |
| 13 | Los códigos CA-XX no se explican en el repo | Baja | **Arreglado en el README** | Se agrega la tabla de criterios al README. |

**Nota sobre el hallazgo 7:** el review lo marcó como severidad media, pero
ya lo había evaluado en la iteración 8. Mantuve la decisión con su
justificación en lugar de aceptar automáticamente la sugerencia.

**Correcciones:** `53 passed` (4 tests nuevos), `ruff check .` limpio.

**Commit:** `test: recorte de page por endpoint y helper antes de su uso (review)`
### Docstrings, README y CHANGELOG
#### Docstrings
`paginate`, `Page` y el módulo `core/pagination.py` tienen docstrings desde
el esqueleto. En esta iteración se agregaron a los dos servicios y las dos
rutas.

**Prompt:**
Agrega docstrings a las funciones clave de la feature que todavía no los
tienen. No cambies ningún comportamiento:

1. users/service.py: list_users
2. reports/service.py: list_reports
3. users/routes.py: la ruta GET /users
4. reports/routes.py: la ruta GET /reports

Escríbelos según lo que el código DEBE hacer según los criterios de
CLAUDE.md, no solo describiendo el código línea por línea:
- Servicios: qué filtran, que ordenan por id y que delegan el recorte en
  paginate.
- Rutas: parámetros (page, size y user_id en reports), valores por
  defecto, recorte sin error, 422 para valores no numéricos y forma de la
  respuesta. Recuerda que aparecen en /docs.

En español, mismo estilo que el docstring de paginate. Corre pytest y
.venv\Scripts\python.exe -m ruff check .

**Revisión (contra los criterios, no contra el código):**
- `list_reports` documenta que filtra y ordena **antes** de paginar y que
  `total` cuenta los reportes filtrados. Deja escrito el orden cuya
  inversión fue el bug de la sección 4.
- Los docstrings de las **rutas** aparecen en `/docs`, así que usan los
  valores literales (1, 20, 1..100) para quien consume la API. Los de los
  **servicios** usan las constantes (`MIN_PAGE`, `MAX_SIZE`) para quien
  mantiene el código.
- Ningún docstring contradice un criterio. Detalle menor: el de
  `GET /reports` no menciona que un `user_id` sin reportes da `total: 0`;
  se documenta en el README.

**Resultado:** `53 passed`, `ruff check .` limpio.

**Commit:** `docs: docstrings de servicios y rutas paginadas`
## Reflexión final