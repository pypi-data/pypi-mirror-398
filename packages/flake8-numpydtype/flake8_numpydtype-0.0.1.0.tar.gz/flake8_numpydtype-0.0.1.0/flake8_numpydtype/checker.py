from .version import __version__
from ast import walk, Name, Attribute

CHECKLIST = {
    # https://numpy.org/devdocs/release/1.20.0-notes.html#deprecations
    'np.bool': 'bool',
    'numpy.bool': 'bool',
    'np.int': 'int',
    'numpy.int': 'int',
    'np.float': 'float',
    'numpy.float': 'float',
    'np.complex': 'complex',
    'numpy.complex': 'complex',
    'np.object': 'object',
    'numpy.object': 'object',
    'np.str': 'str',
    'numpy.str': 'str',

    # the deprecation happened in 1.20 (and 1.16 is the final version supporting py2). we can assume this targets py3.
    'np.long': 'int',
    'numpy.long': 'int',
    'np.unicode': 'str',
    'numpy.unicode': 'str',

    # https://numpy.org/devdocs/release/1.24.0-notes.html#deprecations
    'np.bool8': 'np.bool_',
    'numpy.bool8': 'numpy.bool_',
    'np.int0': 'np.intp',
    'numpy.int0': 'numpy.intp',
    'np.uint0': 'np.uintp',
    'numpy.uint0': 'numpy.uintp',
    'np.object0': 'np.object_',
    'numpy.object0': 'numpy.object_',
    'np.str0': 'np.str_',
    'numpy.str0': 'numpy.str_',
    'np.bytes0': 'np.bytes_',
    'numpy.bytes0': 'numpy.bytes_',
    'np.void0': 'np.void',
    'numpy.void0': 'numpy.void',

    # https://numpy.org/devdocs/numpy_2_0_migration_guide.html#main-namespace
    'np.cfloat': 'np.complex128',
    'numpy.cfloat': 'numpy.complex128',
    'np.clongfloat': 'np.clongdouble',
    'numpy.clongfloat': 'numpy.clongdouble',
    'np.complex_': 'np.complex128',
    'numpy.complex_': 'numpy.complex128',
    'np.float_': 'np.float64',
    'numpy.float_': 'numpy.float64',
    'np.longcomplex': 'np.clongdouble',
    'numpy.longcomplex': 'numpy.clongdouble',
    'np.longfloat': 'np.longdouble',
    'numpy.longfloat': 'numpy.longdouble',
    'np.singlecomplex': 'np.complex64',
    'numpy.singlecomplex': 'numpy.complex64',
    'np.string_': 'np.bytes_',
    'numpy.string_': 'numpy.bytes_',
    'np.unicode_': 'np.str_',
    'numpy.unicode_': 'numpy.str_',
}

class NumpyDTypeChecker(object):
    name = 'flake8_numpydtype'
    version = __version__

    def __init__(self, tree):
        self.tree = tree

    def run(self):
        for node in walk(self.tree):
            if not isinstance(node, Attribute):
                continue
            varName = ''
            value = node
            while isinstance(value, Attribute):
                varName = '.' + value.attr + varName
                value = value.value
            if isinstance(value, Name):
                varName = value.id + varName
            else:
                continue  # the value has some thing callable or subscription
            if varName in CHECKLIST:
                yield node.lineno, node.col_offset, 'NPT010 %s needs to be migrated to %s' % (varName, CHECKLIST[varName]), type(self)
