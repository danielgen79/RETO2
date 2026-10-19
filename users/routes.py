"""Rutas HTTP del recurso `users`.

Patrón de referencia para nuevas rutas:
  - un `APIRouter` con `prefix` y `tags`
  - `response_model=` siempre; nunca devolver `dict` crudos
  - la función delega en `service.py` y no contiene lógica de negocio
  - los errores los levanta `service.py` con `core.errors`
"""
from fastapi import APIRouter, Query, status

from core.pagination import DEFAULT_PAGE, DEFAULT_SIZE, Page
from users import service
from users.schemas import User, UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[User])
def list_users(
    page: int = Query(default=DEFAULT_PAGE),
    size: int = Query(default=DEFAULT_SIZE),
) -> Page[User]:
    """Lista los usuarios paginados, ordenados por `id` ascendente.

    - `page`: número de página (por defecto 1). Un valor menor que 1 se recorta a 1.
    - `size`: elementos por página (por defecto 20). Se recorta al rango 1..100.

    El recorte no es un error. Un valor no numérico responde 422. La respuesta es
    `{items, total, page, size}` con `page` y `size` ya recortados; una página fuera
    de rango devuelve `items` vacío con el `total` correcto.
    """
    return service.list_users(page=page, size=size)


@router.get("/{user_id}", response_model=User)
def get_user(user_id: int) -> User:
    return service.get_user(user_id)


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate) -> User:
    return service.create_user(data)
