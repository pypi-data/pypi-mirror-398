import builtins
import functools
import logging
import sys
import types

__all__ = ('__version__',)

__version__ = '1.0.1'

COPY_SYMBOL_NAMES = (
    '__builtins__',
    '__cached__',
    '__file__',
    '__loader__',
    '__package__',
    '__path__',
    '__spec__',
)

logger = logging.getLogger('symbol-export')

exported_packages = set()
exported_modules = {}
original_modules = {}
original_import = __import__


def isprivatename(name):
    return len(name) > 2 and name.startswith('__') and not name.endswith('__')


def isprotectedname(name):
    return len(name) > 1 and name.startswith('_') and not name.startswith('__')


def isdundername(name: str):
    return len(name) > 4 and name.startswith('__') and name.endswith('__')


def ispublicname(name):
    return not ((isprivatename(name) or isprotectedname(name)) and not isdundername(name))


def isexportedname(module_name):
    if '.' in module_name:
        module_name = module_name.split('.', 1)[0]
    return module_name in exported_packages


def iscapsuledname(module_name):
    return '.' in module_name and module_name.split('.', 1)[0] in exported_packages


def public_symbols(module):
    # Public symbols are determined following the Library interface rules.
    # https://typing.python.org/en/latest/spec/distributing.html#library-interface-public-and-private-symbols
    if hasattr(module, '__all__'):
        return tuple(module.__all__)
    return tuple(name for name in dir(module) if ispublicname(name))


@functools.wraps(original_import)
def import_module(name, globals=None, locals=None, fromlist=(), level=0):
    module = original_import(name, globals, locals, fromlist, level)
    logger.debug('imported %r with name=%r fromlist=%r', module.__name__, name, fromlist)
    module_name = module.__name__
    # when `import __symbol_export__`
    if module_name == __name__:
        register_export_package()
        return module
    # determine if is an registered package member
    if not isexportedname(module_name):
        return module
    return build_capsule(module)


def update_capsule_members(module, exported_module):
    publics = public_symbols(module)
    for symbol in dir(module):
        value = getattr(module, symbol)
        imported_module = False
        if isinstance(value, types.ModuleType) and iscapsuledname(value.__name__):
            if value.__name__ in module.__name__:
                imported_module = True
            value = build_capsule(value)
        if not (imported_module or (symbol in publics)):
            continue
        setattr(exported_module, symbol, value)


def build_capsule(module: types.ModuleType):
    module_name = module.__name__
    exported_module = None

    if iscapsuledname(module_name) or module_name == __name__:
        original_modules[module_name] = module
        exported_module = exported_modules.get(module_name)
        if exported_module is None:
            logger.info('build capsule for %r', module_name)
            exported_module = types.ModuleType(module_name, module.__doc__)
            exported_vars = vars(exported_module)
            if hasattr(module, '__all__'):
                exported_vars['__all__'] = public_symbols(module)
            for symbol in COPY_SYMBOL_NAMES:
                if not hasattr(module, symbol):
                    continue
                exported_vars[symbol] = getattr(module, symbol)
        sys.modules[module_name] = exported_modules[module_name] = exported_module

    if exported_module is None:
        exported_module = module

    update_capsule_members(module, exported_module)

    return exported_module


def imported_from():
    frame = sys._getframe(1)
    while frame:
        co_name = frame.f_code.co_name
        co_filename = frame.f_code.co_filename
        if co_name != '<module>' or co_filename == __file__:
            frame = frame.f_back
            continue
        return frame.f_globals['__name__']
    raise RuntimeError('The origin of the import cannot be found.')


def register_export_package():
    module_name = imported_from()
    module = sys.modules[module_name]
    if not (bool(module.__package__) and hasattr(module, '__path__')):
        raise RuntimeError(
            'This module can only be imported from a package \'__init__.py\' '
            'to define the public interface of submodules of that package.'
        )
    if module_name == '__main__':
        return
    exported_packages.add(module_name)
    logger.debug('registered package %r', module_name)


if __name__ != '__main__':
    exported_packages.add(imported_from())
    build_capsule(sys.modules[__name__])
    register_export_package()
    logger.debug('end import %r', __name__)

builtins.__import__ = import_module
