# swift-matrix

A tiny, dependency-free matrix library for Python.

## Install

```bash
pip install swift-matrix
```

## Quick start

```python
from matricks import Matrix, trace, det2

a = Matrix.from_list([[1, 2], [3, 4]])
b = Matrix.identity(2)

print(a + b)         # element-wise
print(a * 2)         # scalar
print(a * b)         # matrix multiply
print(a.T())         # transpose

print(trace(a))      # 5
print(det2(a))       # -2
```

## Features

* Immutable Matrix (hashable, safe to share)
* Element-wise +, -, unary - 
* Scalar multiply 
* Matrix multiply (a * b)
* Transpose T()
* Small helpers: trace, det2 
* Pytest tests

## License

MIT