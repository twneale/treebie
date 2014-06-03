import os
import sys
import inspect
import logging

from hercules import CachedAttr, CachedClassAttr, DictSetTemporary

from treebie.exceptions import AmbiguousNodeNameError


logger = logging.getLogger('treebie')

def resolve_name(name):
    module_name, _, name = name.rpartition('.')
    if not module_name:
        return
    try:
        module = __import__(module_name, globals(), locals(), [name], 0)
    except ImportError:
        return
    try:
        return getattr(module, name)
    except:
        return


class NodeRefResolver(object):
    '''Each resolver class has a resolve method that will try
    to resolve a string name to an actual node class.
    '''
    __slots__ = ()

    base_type = 'treebie.Node'

    def resolve(self, name):
        raise NotImplementedError()

    @CachedAttr
    def _base_type(cls):
        '''Circular import avoidance hack.
        '''
        return resolve_name(cls.base_type)


class LazyImportResolver(NodeRefResolver):
    '''This resolver tries to import type reference strings
    like 'mypackage.mymodule.MyClass'. The idea is provide functionality
    similar to django's url patterns and celery's task names.
    '''
    def resolve(self, name):
        return resolve_name(name)


class LazyTypeCreator(NodeRefResolver):
    '''This resolver creates missing types (but warns when it does).
    '''
    @CachedClassAttr
    def module(cls):
        return sys.modules[cls._base_type.__class__.__module__]

    def resolve(self, name, logger=logger):

        # Find the module of the caller.
        f = inspect.currentframe()
        for _ in range(4):
            f = f.f_back
        module_name = f.f_globals['__name__']
        module = sys.modules[module_name]

        logger.debug('Automatically creating undefined class %r.' % name)

        # Create the new class in that module.
        template = '{0} = type(\'{0}\', (LazyNodeBaseType,), dict())'
        template = template.format(name)
        set_temp = DictSetTemporary
        with set_temp(f.f_globals) as _globals:
            _globals.update(LazyNodeBaseType=self._base_type)
            exec(template, f.f_globals)
            cls = _globals.get(name)
        return cls


class LazySyntaxTypeCreator(LazyTypeCreator):
    '''Sometime's I even amaze myself with my halfassery.
    '''
    base_type = 'treebie.syntaxnode.SyntaxNode'