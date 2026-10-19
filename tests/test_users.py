"""Tests del recurso `users`.

Estilo de referencia para nuevos tests:
  - un test por caso, con nombre descriptivo en español
  - arrange / act / assert separados por una línea en blanco
  - se comprueba el status code y lo mínimo del cuerpo que da confianza
"""
import pytest
from fastapi.testclient import TestClient


def test_list_users_devuelve_los_seed(client: TestClient) -> None:
    response = client.get("/users")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4


def test_get_user_existente_devuelve_200(client: TestClient) -> None:
    response = client.get("/users/1")

    assert response.status_code == 200
    assert response.json()["email"] == "ada@example.com"


def test_get_user_inexistente_devuelve_404(client: TestClient) -> None:
    response = client.get("/users/999")

    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"]


def test_create_user_devuelve_201_y_el_usuario(client: TestClient) -> None:
    payload = {"name": "Margaret Hamilton", "email": "margaret@example.com"}

    response = client.post("/users", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 5
    assert body["name"] == "Margaret Hamilton"


def test_create_user_email_duplicado_devuelve_409(client: TestClient) -> None:
    payload = {"name": "Otra Ada", "email": "ada@example.com"}

    response = client.post("/users", json=payload)

    assert response.status_code == 409


def test_create_user_email_invalido_devuelve_422(client: TestClient) -> None:
    payload = {"name": "Sin Email", "email": "no-es-un-email"}

    response = client.post("/users", json=payload)

    assert response.status_code == 422


def test_list_users_sin_parametros_devuelve_200_con_page_1_y_size_20(
    client: TestClient,
) -> None:
    """CA-01, CA-02: sin page ni size se usan los valores por defecto 1 y 20."""
    # Arrange: 4 usuarios semilla

    # Act
    response = client.get("/users")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["size"] == 20
    assert body["total"] == 4


def test_list_users_size_mayor_a_100_devuelve_200_con_size_100(client: TestClient) -> None:
    """CA-03: size=500 se recorta a 100 y no es un error."""
    # Arrange: 4 usuarios semilla

    # Act
    response = client.get("/users", params={"size": 500})

    # Assert
    assert response.status_code == 200
    assert response.json()["size"] == 100


def test_list_users_size_0_devuelve_200_con_size_1(client: TestClient) -> None:
    """CA-03: size=0 se recorta a 1 y no es un error."""
    # Arrange: 4 usuarios semilla

    # Act
    response = client.get("/users", params={"size": 0})

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["size"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == 1


@pytest.mark.parametrize("page", [0, -5])
def test_list_users_page_menor_a_1_devuelve_200_con_page_1(client: TestClient, page: int) -> None:
    """CA-03: page=0 y page=-5 se recortan a 1 y no son un error."""
    # Arrange: 4 usuarios semilla

    # Act
    response = client.get("/users", params={"page": page})

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["items"][0]["id"] == 1


@pytest.mark.parametrize(
    "params",
    [{"page": "abc"}, {"size": "2.5"}, {"page": ""}],
    ids=["page-abc", "size-decimal", "page-vacio"],
)
def test_list_users_valor_no_numerico_devuelve_422(client: TestClient, params: dict) -> None:
    """CA-04: un page o size no numérico (o vacío) da 422."""
    # Arrange: 4 usuarios semilla

    # Act
    response = client.get("/users", params=params)

    # Assert
    assert response.status_code == 422


def test_list_users_pagina_fuera_de_rango_devuelve_200_con_items_vacio(
    client: TestClient,
) -> None:
    """CA-08: una página fuera de rango devuelve items vacío y el total correcto."""
    # Arrange: 4 usuarios semilla

    # Act
    response = client.get("/users", params={"page": 99})

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 4


def test_list_users_recorrido_completo_devuelve_200_sin_repetir_ni_saltar(
    client: TestClient,
) -> None:
    """CA-09: recorrer todas las páginas no repite ni salta usuarios, en orden por id."""
    # Arrange: 4 usuarios semilla, size=2 → 2 páginas

    # Act
    ids = []
    for page in (1, 2):
        response = client.get("/users", params={"page": page, "size": 2})
        assert response.status_code == 200
        ids.extend(user["id"] for user in response.json()["items"])

    # Assert
    assert ids == [1, 2, 3, 4]
