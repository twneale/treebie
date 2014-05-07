import pickle
from operator import itemgetter
from functools import wraps
from collections import defaultdict

from hercules.trie import Trie
from hercules import SetDefault, NoClobberDict, KeyClobberError
from hercules.tokentype import string_to_tokentype


class DispatchUserError(Exception):
    '''Raised when user invokes a dispatcher incorrectly.
    '''


class DuplicateHandlerFound(Exception):
    '''Raised when someone does something silly, like
    dispatch two conlicting handlers to process the same
    stream input.
    '''


class Dispatcher(object):
    '''Implements the base functionality for dispatcher types.
    The node instances delegate their dispatch functions to
    subclasses of Dispatcher.
    '''
    __slots__ = tuple()

    def __call__(self, *args, **kwargs):
        return self._make_decorator(*args, **kwargs)

    def _make_decorator(self, *args, **kwargs):
        def decorator(method):
            self.register(method, args, kwargs)
            return method
        return decorator

    loads = pickle.loads

    def register(self, method, args, kwargs):
        '''Given a single decorated handler function,
        prepare it for the node __new__ method.
        '''
        default = defaultdict(NoClobberDict)
        with SetDefault(method, '_disp', default) as registry:
            key = pickle.dumps((args, kwargs))
            try:
                registry[self][key] = method
            except KeyClobberError:
                other_method = registry[type(self)][key]
                msg = (
                    "Can't register %r: previously registered handler %r "
                    "found for input signature %r.")
                args = (method, other_method, (args, kwargs))
                raise DuplicateHandlerFound(msg % args)

    def prepare(self, dispatch_data):
        '''Given all the registered handlers for this
        dispatcher instance, return any data required
        by the dispatch method. It gets stored on the
        node on which the handlers are defined.

        Can be overridden to provide more efficiency,
        simplicity, etc.
        '''
        raise NotImplementedError()

    def dispatch(self, itemstream, dispatch_data):
        '''Provides the logic for dispatching the itemstream
        to a handler function, given the dispatch_data created at
        import time.
        '''
        raise NotImplementedError()


class TokentypeSequence(Dispatcher):
    '''A basic dispatcher that matches sequences of tokentypes
    in the itemstream against a state machine in order to resolve
    to stream to a handler method in each state.
    '''
    def prepare(self, dispatch_data):
        trie = Trie()
        for signature, method in dispatch_data.items():
            tokenseq, kwargs = self.loads(signature)
            trie.add(tokenseq, method)
        return trie

    def dispatch(self, itemstream, dispatch_data, second=itemgetter(1)):
        '''Try to find a handler that matches the signatures registered
        to this dispatcher instance.
        '''
        match = dispatch_data.scan(itemstream)
        if match:
            return match.value(), match.group()


class TokenSubtypes(Dispatcher):
    '''Will match at most one subtype of the given token type.
    '''
    def prepare(self, dispatch_data):
        str2token = string_to_tokentype
        data = {}
        for signature, method in dispatch_data.items():
            args, kwargs = self.loads(signature)
            if 1 < len(args):
                msg = ('The %s dispatcher only accepts one '
                       'token as an argument; got %d')
                cls_name = self.__class__.__name__
                raise DispatchUserError(msg % (cls_name, len(args)))

            token = args[0]
            data[str2token(token)] = method
        return data


    def dispatch(self, itemstream, dispatch_data, str2token=string_to_tokentype):
        item = itemstream.this()
        item_token = str2token(item.token)
        for match_token, method in dispatch_data.items():
            if item_token in match_token:
                return method, [next(itemstream)]
        return

matches_subtypes = token_subtypes = TokenSubtypes()
matches = tokenseq = TokentypeSequence()