"""
Integration test suite for ThesisFlow Web Server.
Verifies all REST API endpoints, static assets, and HTML rendering using Flask test_client.
"""

import pytest
from server import app


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "ThesisFlow" in html
    assert "color-scheme" in html


def test_system_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert "counts" in data
    assert data["counts"]["papers"] >= 1
    assert data["counts"]["constants"] >= 10


def test_list_papers(client):
    response = client.get("/api/papers")
    assert response.status_code == 200
    papers = response.get_json()
    assert isinstance(papers, list)
    assert len(papers) >= 1
    assert "title" in papers[0]


def test_list_equations(client):
    response = client.get("/api/equations")
    assert response.status_code == 200
    eqs = response.get_json()
    assert isinstance(eqs, list)
    assert len(eqs) >= 1
    assert "latex" in eqs[0]


def test_list_constants(client):
    response = client.get("/api/constants")
    assert response.status_code == 200
    consts = response.get_json()
    assert len(consts) >= 10
    symbols = [c["symbol"] for c in consts]
    assert "c" in symbols
    assert "h" in symbols


def test_playground_evaluate(client):
    payload = {
        "latex": "E = m * c**2",
        "independent_var": "m",
        "min_val": 0.1,
        "max_val": 10.0,
        "fixed_params": {"m": 1.0, "c": 3e8},
        "target_dep_var": "E",
        "num_points": 50
    }
    response = client.post("/api/playground/evaluate", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["x"]) == 50
    assert len(data["y"]) == 50
    assert data["operating_point_y"] is not None


def test_code_generation(client):
    payload = {
        "latex": "F = m * a",
        "dependent_var": "F",
        "independent_vars": ["m", "a"],
        "equation_name": "calc_force"
    }
    response = client.post("/api/equations/code", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "pure_python" in data["code"]
    assert "numpy" in data["code"]


def test_markdown_report_export(client):
    papers = client.get("/api/papers").get_json()
    first_id = papers[0]["id"]
    response = client.get(f"/api/reports/paper/{first_id}/markdown")
    assert response.status_code == 200
    text = response.data.decode("utf-8")
    assert "ThesisFlow Research Dossier" in text
