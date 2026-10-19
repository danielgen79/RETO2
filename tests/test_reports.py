"""Tests del recurso `reports`."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from reports import repository as reports_repository


def _payload(user_id: int = 1, title: str = "Incidencia", body: str = "algo pasó") -> dict:
    return {"user_id": user_id, "title": title, "body": body}


def test_create_report_devuelve_201(client: TestClient) -> None:
    response = client.post("/reports", json=_payload())

    assert response.status_code == 201
    assert response.json()["title"] == "Incidencia"


def test_create_report_body_muy_largo_devuelve_422(client: TestClient) -> None:
    response = client.post("/reports", json=_payload(body="x" * 600))

    assert response.status_code == 422


def test_get_report_inexistente_devuelve_404(client: TestClient) -> None:
    response = client.get("/reports/999")

    assert response.status_code == 404


def test_get_report_existente_devuelve_200(client: TestClient) -> None:
    """Caso feliz de GET /reports/{report_id}: devuelve el reporte pedido."""
    # Arrange
    _create_reports(client, 1, user_id=2)

    # Act
    response = client.get("/reports/1")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["user_id"] == 2


def test_list_reports_filtra_por_user_id(client: TestClient) -> None:
    client.post("/reports", json=_payload(user_id=1, title="de user 1"))
    client.post("/reports", json=_payload(user_id=2, title="de user 2"))

    response = client.get("/reports", params={"user_id": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["user_id"] == 1


def _create_reports(client: TestClient, count: int, user_id: int = 1) -> None:
    for i in range(count):
        response = client.post("/reports", json=_payload(user_id=user_id, title=f"reporte {i}"))
        assert response.status_code == 201


def test_list_reports_sin_parametros_devuelve_200_con_page_1_y_size_20(
    client: TestClient,
) -> None:
    """CA-01, CA-02: sin page ni size se usan los valores por defecto 1 y 20."""
    # Arrange
    _create_reports(client, 3)

    # Act
    response = client.get("/reports")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["size"] == 20
    assert body["total"] == 3


def test_list_reports_size_mayor_a_100_devuelve_200_con_size_100(client: TestClient) -> None:
    """CA-03: size=500 se recorta a 100 y no es un error."""
    # Arrange
    _create_reports(client, 3)

    # Act
    response = client.get("/reports", params={"size": 500})

    # Assert
    assert response.status_code == 200
    assert response.json()["size"] == 100


def test_list_reports_size_0_devuelve_200_con_size_1(client: TestClient) -> None:
    """CA-03: size=0 se recorta a 1 y no es un error."""
    # Arrange
    _create_reports(client, 3)

    # Act
    response = client.get("/reports", params={"size": 0})

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["size"] == 1
    assert len(body["items"]) == 1


@pytest.mark.parametrize(
    "params",
    [{"page": "abc"}, {"size": "2.5"}, {"page": ""}],
    ids=["page-abc", "size-decimal", "page-vacio"],
)
def test_list_reports_valor_no_numerico_devuelve_422(client: TestClient, params: dict) -> None:
    """CA-04: un page o size no numérico (o vacío) da 422."""
    # Arrange
    _create_reports(client, 3)

    # Act
    response = client.get("/reports", params=params)

    # Assert
    assert response.status_code == 422


def test_list_reports_pagina_fuera_de_rango_devuelve_200_con_items_vacio(
    client: TestClient,
) -> None:
    """CA-08: una página fuera de rango devuelve items vacío y el total correcto."""
    # Arrange
    _create_reports(client, 3)

    # Act
    response = client.get("/reports", params={"page": 99})

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 3


def test_list_reports_recorrido_completo_devuelve_200_sin_repetir_ni_saltar(
    client: TestClient,
) -> None:
    """CA-09: recorrer todas las páginas no repite ni salta reportes, en orden por id."""
    # Arrange: 5 reportes, size=2 → 3 páginas
    _create_reports(client, 5)

    # Act
    ids = []
    for page in (1, 2, 3):
        response = client.get("/reports", params={"page": page, "size": 2})
        assert response.status_code == 200
        ids.extend(report["id"] for report in response.json()["items"])

    # Assert
    assert ids == [1, 2, 3, 4, 5]


def test_list_reports_user_id_con_paginacion_devuelve_200_con_total_del_filtro(
    client: TestClient,
) -> None:
    """CA-06, CA-07: user_id se combina con la paginación y total cuenta todo el filtro."""
    # Arrange
    _create_reports(client, 5, user_id=1)
    _create_reports(client, 2, user_id=2)

    # Act
    response = client.get("/reports", params={"user_id": 1, "size": 2})

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert all(report["user_id"] == 1 for report in body["items"])


def test_list_reports_user_id_sin_reportes_devuelve_200_con_items_vacio(
    client: TestClient,
) -> None:
    """CA-07: un user_id sin reportes devuelve items vacío y total 0."""
    # Arrange
    _create_reports(client, 3, user_id=1)

    # Act
    response = client.get("/reports", params={"user_id": 99})

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_ids_unicos_bajo_concurrencia() -> None:
    """Crear 30 reportes en paralelo debe producir 30 ids distintos."""
    reports_repository.reset()
    n = 30

    with ThreadPoolExecutor(max_workers=n) as pool:
        futuros = [
            pool.submit(reports_repository.add, user_id=1, title=f"r{i}", body="")
            for i in range(n)
        ]
        creados = [f.result() for f in futuros]

    ids = {r.id for r in creados}
    assert len(ids) == n, f"se esperaban {n} ids únicos, hubo {n - len(ids)} colisiones"
