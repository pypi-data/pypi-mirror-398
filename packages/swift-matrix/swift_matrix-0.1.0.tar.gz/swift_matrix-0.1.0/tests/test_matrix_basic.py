from ..src.matricks import Matrix

def test_shape_and_transpose():
    m = Matrix.from_list([[1, 2, 3], [4, 5, 6]])
    assert m.shape == (2, 3)
    t = m.T()
    assert t.shape == (3, 2)
    assert t.to_list() == [[1, 4], [2, 5], [3, 6]]

def test_add_and_scalar_mul():
    a = Matrix.from_list([[1, 2], [3, 4]])
    b = Matrix.from_list([[10, 20], [30, 40]])
    assert (a + b).to_list() == [[11, 22], [33, 44]]
    assert (a * 2).to_list() == [[2, 4], [6, 8]]

def test_matmul():
    a = Matrix.from_list([[1, 2, 3], [4, 5, 6]])
    b = Matrix.from_list([[7, 8], [9, 10], [11, 12]])
    assert (a * b).to_list() == [[58, 64], [139, 154]]
