def test_import():
    import appwindows
    assert appwindows is not None
    assert hasattr(appwindows, 'get_finder')