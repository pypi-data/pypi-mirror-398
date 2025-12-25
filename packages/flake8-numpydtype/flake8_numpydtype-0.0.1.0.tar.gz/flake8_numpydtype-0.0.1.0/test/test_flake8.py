from sys import version_info
from pytest import mark
from ast import parse
from flake8_numpydtype.checker import NumpyDTypeChecker

def test_positive_bool():
    tree = parse('''
import numpy
numpy.bool_
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_positive_int():
    tree = parse('''
import numpy
numpy.int_
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_positive_intp():
    tree = parse('''
import numpy
numpy.intp
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_positive_uint():
    tree = parse('''
import numpy
numpy.uint
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_positive_float():
    tree = parse('''
import numpy
numpy.float64
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_positive_complex():
    tree = parse('''
import numpy
numpy.complex128
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_positive_object():
    tree = parse('''
import numpy
numpy.object_
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_positive_module():
    # numpy not being toplevel is out of scope.
    tree = parse('''
import sys
if sys.version_info[0]>=3:
    import builtins
else:
    import __builtin__ as builtins

class A(object):
    class numpy(object):
        bool = builtins.bool

A.numpy.bool
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 0

def test_importas():
    tree = parse('''
import numpy as np
np.bool
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 1
    assert violations[0][2].startswith('NPT010 ')

def test_array():
    tree = parse('''
import numpy
numpy.array([1], dtype=numpy.int)
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 1
    assert violations[0][2].startswith('NPT010 ')

def test_variable():
    tree = parse('''
import numpy
numpy.float(3)
''')
    violations = list(NumpyDTypeChecker(tree).run())
    assert len(violations) == 1
    assert violations[0][2].startswith('NPT010 ')
