from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_q1_2026_statement_over_http():
    response = client.get("/income-statement", params={"start": "2026-01-01", "end": "2026-03-31"})
    assert response.status_code == 200
    body = response.json()
    assert body["company"] == "Northwind Coffee Roasters"
    assert body["start"] == "2026-01-01"
    assert body["end"] == "2026-03-31"
    assert body["sections"]["other_income"]["lines"] == [
        {"account": "7000", "name": "Interest Income", "amount": "42.18"}
    ]
    assert body["subtotals"] == {
        "gross_profit": "23577.75",
        "operating_income": "-44522.32",
        "net_income": "-44480.14",
    }


def test_amounts_are_strings_not_floats():
    # Floats would lose exactness; this fails if the route loses its return type.
    body = client.get("/income-statement", params={"start": "2026-01-01", "end": "2026-03-31"}).json()
    assert body["sections"]["revenue"]["total"] == "37850.50"
    assert body["sections"]["revenue"]["lines"][0]["amount"] == "35650.75"


def test_empty_range_shows_zero_totals():
    body = client.get("/income-statement", params={"start": "2030-01-01", "end": "2030-12-31"}).json()
    assert body["sections"]["revenue"] == {"label": "Revenue", "total": "0.00", "lines": []}
    assert body["subtotals"]["net_income"] == "0.00"


def test_start_after_end_is_422():
    response = client.get("/income-statement", params={"start": "2026-03-31", "end": "2026-01-01"})
    assert response.status_code == 422


def test_bad_date_is_422():
    response = client.get("/income-statement", params={"start": "2026-02-30", "end": "2026-03-31"})
    assert response.status_code == 422


def test_missing_date_is_422():
    response = client.get("/income-statement", params={"start": "2026-01-01"})
    assert response.status_code == 422
