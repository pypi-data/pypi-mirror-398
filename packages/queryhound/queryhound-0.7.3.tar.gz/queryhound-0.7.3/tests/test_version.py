def test_version_exposed():
    import queryhound
    assert hasattr(queryhound, '__version__')
    assert isinstance(queryhound.__version__, str)
    assert len(queryhound.__version__) > 0
