from ..src.matricks import Matrix, det2, trace

def test_det2():
    m = Matrix.from_list([[1, 2], [3, 4]])
    assert det2(m) == -2

def test_trace():
    m = Matrix.from_list([[1, 2], [3, 4]])
    assert trace(m) == 5
