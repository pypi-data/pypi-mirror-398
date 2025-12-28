from idioma.utils import get_flag


def test_get_flag():
    """Test get_flag function return Ukraine flag"""
    assert get_flag('uk') == '🇺🇦'
