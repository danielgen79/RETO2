"""Paginación compartida por las listas de la API.

Toda lista paginada pasa por `paginate`. El servicio filtra y ordena por `id`
ascendente antes de llamar aquí: esta capa solo recorta y corta.
"""
from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_PAGE = 1
DEFAULT_SIZE = 20
MIN_SIZE = 1
MAX_SIZE = 100


class Page(BaseModel, Generic[T]):
    """Página de resultados tal como la devuelve la API."""

    items: list[T]
    total: int
    page: int
    size: int


def paginate(items: Sequence[T], page: int, size: int) -> Page[T]:
    """Devuelve la página `page` de `items`, con `page` y `size` ya recortados.

    Args:
        items: lista completa, ya filtrada y ordenada por el servicio.
        page: número de página pedido. Si es menor que 1 se recorta a 1.
        size: tamaño de página pedido. Se recorta al rango `MIN_SIZE`..`MAX_SIZE`.

    Returns:
        Un `Page` con los elementos de la página, `total` calculado sobre todos los
        `items` recibidos y los valores de `page` y `size` ya recortados. Una página
        fuera de rango devuelve `items` vacío con el `total` correcto.
    """
    page = max(page, DEFAULT_PAGE)
    size = min(max(size, MIN_SIZE), MAX_SIZE)
    start = (page - 1) * size
    return Page(
        items=list(items[start : start + size]),
        total=len(items),
        page=page,
        size=size,
    )
