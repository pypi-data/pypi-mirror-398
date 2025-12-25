import my_test_tuxpkg_project


def test_version():
    """Test that version is properly defined"""
    assert type(my_test_tuxpkg_project.__version__) is str
    assert len(my_test_tuxpkg_project.__version__) > 0
