import app

def test_status():
    assert app.get_status() == "BROKEN_BY_AI"
