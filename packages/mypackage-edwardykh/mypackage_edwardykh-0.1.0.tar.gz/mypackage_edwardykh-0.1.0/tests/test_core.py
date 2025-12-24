import pytest
from mypackage import add, divide

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0

def test_divide():
    assert divide(4, 2) == 2.0
    with pytest.raises(ValueError, match="除数不能为0"):
        divide(1, 0)