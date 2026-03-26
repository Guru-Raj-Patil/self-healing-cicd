import app

def test_status():
    assert app.get_status() == "OK"
