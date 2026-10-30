from app import app


def test_hello_saluda():
    r = app.test_client().get("/hello?name=Duoc")
    assert r.status_code == 200
    assert b"Hello, Duoc!" in r.data


def test_hello_escapa_html():
    r = app.test_client().get("/hello?name=<script>alert(1)</script>")
    assert b"<script>" not in r.data


def test_health():
    r = app.test_client().get("/health")
    assert r.get_json() == {"status": "ok"}
