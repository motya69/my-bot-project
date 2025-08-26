from bot.validators import is_tire_size, is_pcd, is_number, is_year, is_nonempty

def test_is_tire_size_ok():
    assert is_tire_size("205/55 R16")
    assert is_tire_size("195/65R15")

def test_is_tire_size_bad():
    assert not is_tire_size("205/55R")
    assert not is_tire_size("abc")

def test_is_pcd_ok():
    assert is_pcd("5x112")
    assert is_pcd("5X114.3")
    assert is_pcd(" 5 x 100 ")

def test_is_pcd_bad():
    assert not is_pcd("5-112")
    assert not is_pcd("x114.3")

def test_is_number():
    assert is_number("7.5")
    assert is_number("60,1")
    assert not is_number("abc")

def test_is_year():
    assert is_year("2018")
    assert not is_year("2077")
    assert not is_year("19a0")

def test_is_nonempty():
    assert is_nonempty("ok")
    assert not is_nonempty("   ")
