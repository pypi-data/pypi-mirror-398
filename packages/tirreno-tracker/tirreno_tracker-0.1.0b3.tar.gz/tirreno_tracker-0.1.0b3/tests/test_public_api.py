def test_public_api_surface():
    import importlib
    import os
    PKG = os.getenv("PKG", "tirreno_tracker")
    pkg = importlib.import_module(PKG)

    assert hasattr(pkg, "Tracker")
    assert hasattr(pkg, "Event")
    assert hasattr(pkg, "Payload")
    assert isinstance(pkg.__version__, str)
