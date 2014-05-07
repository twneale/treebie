import inspect
from collections import defaultdict

from hercules import CachedAttr, NoClobberDict, Stream
from hercules.tokentype import Token

from treebie.node import Node
from treebie.resolvers import (
    LazyImportResolver,
    LazySyntaxTypeCreator)


class ParseError(Exception):
    pass


class _NodeMeta(type):

    @classmethod
    def get_base_attrs(meta, bases):
        '''Aggregate registered handlers from the node's base
        classes into the instance's dict.
        '''
        attrs = {}
        get_attr_dict = lambda cls: dict(inspect.getmembers(cls))
        for base_attrs in map(get_attr_dict, bases):
            attrs.update(base_attrs)
        return attrs

    @classmethod
    def get_sorted_attrs(meta, attrs):
        '''Sort the items if an order is given.
        '''
        items = list(attrs.items())
        order = attrs.get('order')
        if order is not None:
            def sorter(item, order=order):
                attr, val = item
                if attr in order:
                    return order.index(attr)
                else:
                    return -1
            items.sort(key=sorter)
        return items

    @classmethod
    def compile_dispatch_data(meta, items):
        dispatch_data = defaultdict(NoClobberDict)
        for _, method in items:
            disp = getattr(method, '_disp', None)
            if disp is None:
                continue
            for dispatcher, signature_dict in disp.items():
                for signature, method in signature_dict.items():
                    dispatch_data[dispatcher][signature] = method
        return dispatch_data

    @classmethod
    def prepare(meta, dispatch_data):
        '''Delegate further preparation of dispatch data to the
        dispatchers used on this class.
        '''
        res = {}
        for dispatcher, signature_dict in dispatch_data.items():
            res[dispatcher] = dispatcher.prepare(signature_dict)
        return res

    def __new__(meta, name, bases, attrs):
        # Merge all handlers registered on base classes into
        # this instance.
        _attrs = dict(attrs)
        _attrs.update(meta.get_base_attrs(bases))

        # Get them into the order specified on the class, if any.
        items = meta.get_sorted_attrs(_attrs)

        # Aggregate all the handlers defined on this class.
        dispatch_data = meta.compile_dispatch_data(items)
        dispatch_data = meta.prepare(dispatch_data)

        # Update the class with the dispatch data.
        attrs.update(_dispatch_data=dispatch_data)
        cls = type.__new__(meta, name, bases, attrs)

        return cls


class SyntaxNode(Node, metaclass=_NodeMeta):

    eq_attrs = ('children', 'tokens', '__class__.__name__',)

    noderef_resolvers = (
        LazyImportResolver,
        LazySyntaxTypeCreator)

    @CachedAttr
    def tokens(self):
        return []

    def __repr__(self):
        return '%s(tokens=%s)' % (self.__class__.__name__, self.tokens)

    #------------------------------------------------------------------------
    # Parsing and dispatch methods.
    #------------------------------------------------------------------------
    def popstate(self):
        '''Just for readability and clarity about what it means
        to return the parent.'''
        return self.parent

    def resolve(self, itemstream):
        '''Try to resolve the incoming stream against the functions
        defined on the class instance.
        '''
        for dispatcher, dispatch_data in self._dispatch_data.items():
            match = dispatcher.dispatch(itemstream, dispatch_data)
            if match is None:
                continue
            method, matched_items = match
            if method is not None:
                return method(self, *matched_items)

        # Itemstream is exhausted.
        if not itemstream:
            raise StopIteration()

        # Propagate up this node's parent.
        parent = getattr(self, 'parent', None)
        if parent is not None:
            return parent.resolve(itemstream)
        else:
            msg = 'No function defined on %r for %s ...'
            i = itemstream.i
            stream = list(itemstream._stream)[i:i+10]
            # self.getroot().pprint()
            raise ParseError(msg % (self, stream))

    @classmethod
    def parse(cls_or_inst, itemiter, **options):
        '''Supply a user-defined start class.
        '''
        itemstream = Stream(itemiter)

        if callable(cls_or_inst):
            node = cls_or_inst()
        else:
            node = cls_or_inst

        while 1:
            try:
                if options.get('debug'):
                    print('%r <-- %r' % (node, itemstream))
                    node.getroot().pprint()
                node = node.resolve(itemstream)
            except StopIteration:
                break
        return node.getroot()

    # -----------------------------------------------------------------------
    # Readability functions.
    # -----------------------------------------------------------------------
    def extend(self, items):
        self.tokens.extend(items)
        return self

    def first(self):
        return self.tokens[0]

    def first_token(self):
        return self.tokens[0].token

    def first_text(self):
        if self.tokens:
            return self.tokens[0].text
        else:
            # XXX: such crap
            return ''

    #------------------------------------------------------------------------
    # Serialization methods.
    #------------------------------------------------------------------------
    @staticmethod
    def _tokens_as_data(self, tokens):
        _tokens = []
        for (pos, token, text) in tokens:
            _tokens.append((pos, token.as_json(), text))
        return tokens

    def _tokens_from_data(self, tokens):
        _tokens = []
        for pos, token, text in tokens:
            _tokens.append((pos, Token.fromstring(token), text))
        return _tokens

    as_data_attrs = (
        dict(attr='__class__.__name__', alias='type'),
        dict(attr='children'),
        dict(
            attr='tokens',
            to_data=_tokens_as_data,
            fromdata=_tokens_from_data),
        )
