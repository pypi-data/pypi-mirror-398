from bnusys.sparse import SparseCOOMatrix


def test_from_dense_and_to_dense():
    dense = [
        [0, 0, 3],
        [1, 0, 0],
    ]
    A = SparseCOOMatrix.from_dense(dense)
    assert A.shape == (2, 3)
    assert A.to_dense() == dense


def test_matvec():
    dense = [
        [0, 2],
        [3, 0],
    ]
    A = SparseCOOMatrix.from_dense(dense)
    # y = A x  where x = [10, 1]
    # y[0] = 0*10 + 2*1 = 2
    # y[1] = 3*10 + 0*1 = 30
    y = A.matvec([10, 1])
    assert y == [2, 30]


print('测试结束')