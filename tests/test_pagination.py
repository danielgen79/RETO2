"""Tests unitarios de `core.pagination.paginate`.

Los valores esperados son literales del criterio (1, 20, 100), no las constantes del
módulo, para que un cambio accidental de las constantes haga fallar el test.
`paginate` es genérica: se prueba con una lista simple de enteros.
"""
import pytest

from core.pagination import paginate


@pytest.mark.parametrize("size", [0, -1, -50])
def test_paginate_size_menor_a_1_se_recorta_a_1(size: int) -> None:
    """CA-03: size menor a 1 se recorta a 1."""
    # Arrange
    items = [1, 2, 3]

    # Act
    result = paginate(items, page=1, size=size)

    # Assert
    assert result.size == 1
    assert result.items == [1]


def test_paginate_size_100_se_mantiene() -> None:
    """CA-03: size igual a 100 es válido y no se recorta."""
    # Arrange
    items = list(range(1, 151))

    # Act
    result = paginate(items, page=1, size=100)

    # Assert
    assert result.size == 100
    assert len(result.items) == 100


@pytest.mark.parametrize("size", [101, 1000])
def test_paginate_size_mayor_a_100_se_recorta_a_100(size: int) -> None:
    """CA-03: size mayor a 100 se recorta a 100."""
    # Arrange
    items = list(range(1, 151))

    # Act
    result = paginate(items, page=1, size=size)

    # Assert
    assert result.size == 100
    assert len(result.items) == 100


@pytest.mark.parametrize("page", [0, -1, -50])
def test_paginate_page_menor_a_1_se_recorta_a_1(page: int) -> None:
    """CA-03: page menor a 1 se recorta a 1."""
    # Arrange
    items = [1, 2, 3, 4, 5]

    # Act
    result = paginate(items, page=page, size=2)

    # Assert
    assert result.page == 1
    assert result.items == [1, 2]


def test_paginate_pagina_2_con_size_10_devuelve_items_11_a_20() -> None:
    """CA-09: el inicio del slice es (page - 1) * size, sin repetir ni saltar items."""
    # Arrange
    items = list(range(1, 26))

    # Act
    result = paginate(items, page=2, size=10)

    # Assert
    assert result.items == list(range(11, 21))


def test_paginate_ultima_pagina_parcial_devuelve_5_items_y_size_10() -> None:
    """CA-05: la última página parcial trae menos items, pero size sigue siendo el pedido."""
    # Arrange
    items = list(range(1, 26))

    # Act
    result = paginate(items, page=3, size=10)

    # Assert
    assert result.items == [21, 22, 23, 24, 25]
    assert result.size == 10
    assert result.page == 3


def test_paginate_pagina_fuera_de_rango_devuelve_items_vacio_y_total_correcto() -> None:
    """CA-08: una página fuera de rango devuelve items vacío y el total correcto."""
    # Arrange
    items = list(range(1, 26))

    # Act
    result = paginate(items, page=99, size=10)

    # Assert
    assert result.items == []
    assert result.total == 25


def test_paginate_total_cuenta_todos_los_items_no_solo_los_de_la_pagina() -> None:
    """CA-06: total cuenta todos los items recibidos, no solo los de la página."""
    # Arrange
    items = list(range(1, 26))

    # Act
    result = paginate(items, page=1, size=10)

    # Assert
    assert len(result.items) == 10
    assert result.total == 25


def test_paginate_lista_vacia_devuelve_items_vacio_y_total_0() -> None:
    """CA-08: una lista vacía devuelve items vacío y total 0."""
    # Arrange
    items: list[int] = []

    # Act
    result = paginate(items, page=1, size=10)

    # Assert
    assert result.items == []
    assert result.total == 0
