import pytest

MODULE_MEMBERS = (
    '__builtins__',
    '__cached__',
    '__doc__',
    '__file__',
    '__loader__',
    '__name__',
    '__package__',
    '__spec__',
)
PACKAGE_MEMBERS = MODULE_MEMBERS + ('__path__',)

INIT_MODULES = ('alldunder', 'byname')

EXPORT_MEMBERS = MODULE_MEMBERS + ('__all__', '__version__',)
INIT_MEMBERS = PACKAGE_MEMBERS + ('__symbol_export__', '__version__', '_A', 'B')
ALLDUNDER_MEMBERS = MODULE_MEMBERS + ('__all__', '_public_function', '_PublicClass')
BYNAME_MEMBERS = MODULE_MEMBERS + ('public_module', 'public_var', 'public_function', 'PublicClass')


def test_symbolexport_symbols():
    import sample_package

    members = dir(sample_package.__symbol_export__)
    others = set(members).difference(EXPORT_MEMBERS)
    assert not others, others


def test_init_symbols():
    import sample_package

    members = dir(sample_package)
    others = set(members).difference(INIT_MEMBERS)
    assert not others, others


def test_alldunder_symbols():
    import sample_package.alldunder

    assert 'alldunder' in dir(sample_package), 'submodule must be public'

    members = dir(sample_package.alldunder)
    others = set(members).difference(ALLDUNDER_MEMBERS)
    assert not others, 'some symbols must be private'


def test_alldunder_illegal_fromimport():
    with pytest.raises(ImportError):
        from sample_package.alldunder import PrivateClass


def test_alldunder_symbol_not_accessible():
    from sample_package import alldunder

    with pytest.raises(AttributeError):
        alldunder.private_function


def test_byname_symbols():
    import sample_package.byname

    assert 'byname' in dir(sample_package), 'submodule must be public'

    members = dir(sample_package.byname)
    others = set(members).difference(BYNAME_MEMBERS)
    assert not others, 'some symbols must be private'


def test_byname_illegal_fromimport():
    with pytest.raises(ImportError):
        from sample_package.byname import _private_function


def test_byname_symbol_not_accessible():
    from sample_package import byname

    with pytest.raises(AttributeError):
        byname._private_var


def test_import_from_non_package():
    with pytest.raises(RuntimeError):
        import sample_module


def test_double_import_is_safe():
    for _ in range(2):
        import sample_package

        members = dir(sample_package)
        others = set(members).difference(INIT_MEMBERS + INIT_MODULES)
        assert not others, others


def test_module_identity_preserved():
    import sample_package
    import sys

    assert sys.modules["sample_package"] is sample_package
