def test_import_cli():
    import importlib
    m = importlib.import_module('queryhound.cli')
    assert hasattr(m, 'run')
