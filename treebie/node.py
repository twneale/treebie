from __future__ import print_function

import re
import json
import uuid
import inspect
import operator
from collections import defaultdict

from hercules import (
        CachedAttr, CachedClassAttr, NoClobberDict,
        KeyClobberError, memoize_methodcalls, LoopInterface,
        iterdict_filter, DictFilterMixin)

from treebie.chainmap import ChainMap
from treebie.resolvers import (
    resolve_name,
    LazyImportResolver,
    LazyTypeCreator)
from treebie.exceptions import ConfigurationError


class NodeList(list, DictFilterMixin):
    '''A list subclass that exposes a LoopInterface when
    invoked as a context manager, and can also be iterated
    over in sorted order, given a dict key.

    with node.children.sorted_by('rank') as loop:
        for thing in loop.filter(disqualified=False):
            if loop.first:
                print thing, 'is first!'
            else:
                print thing, 'is the %dth loser' % loop.counter
    '''
    def __enter__(self):
        return LoopInterface(self)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def order_by(self, key):
        '''Sort kids by the specified dictionary key.
        '''
        return self.__class__(sorted(self, key=operator.itemgetter(key)))


class BaseNode(dict):
    '''A basic directed graph node optimized for mutability and
    contextual analysis.

    This node class differs from Networkx nodes, which are essentially
    a dictionary-based abstraction optimized for O(1) node lookup.
    '''
    # The groups of resolvers attempted (in order) for resolving
    # stringy node references.
    noderef_resolvers = (
        LazyImportResolver,
        LazyTypeCreator)

    @CachedAttr
    def children(self):
        return NodeList()

    # -----------------------------------------------------------------------
    # Custom __eq__ behavior.
    # -----------------------------------------------------------------------
    eq_attrs = ('children',)

    @CachedClassAttr
    def _eq_attrgetters(self):
        '''Functions that quickly get the attrs marked for
        consideration in determining equality on the class.
        '''
        return tuple(map(operator.attrgetter, self.eq_attrs))

    def __eq__(self, other):
        '''Defers to dict.__eq__, then compares attrs specified
        by subclasses.
        '''
        if not isinstance(other, BaseNode):
            return False
        if not super(BaseNode, self).__eq__(other):
            return False
        for getter in self._eq_attrgetters:
            if not getter(self) == getter(other):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, dict.__repr__(self))

    # -----------------------------------------------------------------------
    # Methods related to instance state.
    # -----------------------------------------------------------------------
    @CachedAttr
    def ctx(self):
        '''For values that are accessible to children
        and inherit from parents.

        Construction is lazy to avoid creating a chainmap
        for every node where it's an unused feature.

        Should be used primarily for contextually specific ephemera
        needed for graph traversal, rendering, and mutation.

        Doesn't get serialized.
        '''
        return ChainMap(inst=self)

    # -----------------------------------------------------------------------
    # Plumbing methods for resolve stringy node references.
    # -----------------------------------------------------------------------
    @CachedAttr
    def resolvers(self):
        return [cls() for cls in self.noderef_resolvers]

    @memoize_methodcalls
    def resolve_noderef(self, ref):
        '''Given a string, resolve it to a class definition. The
        various resolver methods may be slow, so the results of this
        function get memoized.
        '''
        if isinstance(ref, str):
            for resolver in self.resolvers:
                node = resolver.resolve(ref)
                if node is not None:
                    return node
        return ref

    # -----------------------------------------------------------------------
    # Low-level mutation methods. String references to types not allowed.
    # -----------------------------------------------------------------------
    def append(self, child, related=True):
        '''Related is false when you don't want the child to become
        part of the resulting data structure, as in the case of the
        start node.
        '''
        if related:
            child.parent = self
            self.children.append(child)
        return child

    def insert(self, index, child):
        '''Insert a child node a specific index.
        '''
        child.parent = self
        self.children.insert(index, child)
        return child

    def index(self):
        '''Return the index of this node in its parent's children
        list.
        '''
        parent = self.parent
        if parent is not None:
            return parent.children.index(self)

    def detatch(self):
        '''Remove this node from parent.
        '''
        self.parent.remove(self)
        del self.parent
        return self
    detach = detatch

    def remove(self, child):
        'Um, should this return something? Not sure.'
        self.children.remove(child)

    # -----------------------------------------------------------------------
    # High-level mutation methods. String references to types allowed.
    # -----------------------------------------------------------------------
    def clone(self, *args, **kwargs):
        new = self.__class__(self, *args, **kwargs)
        new.children = list(self.children)
        if hasattr(self, 'parent'):
            new.parent = self.parent
        return new

    def ascend(self, cls_or_name=None, related=True, *args, **kwargs):
        '''Create a new parent node. Set it as the
        parent of this node. Return the parent.
        '''
        cls_or_name = cls_or_name or self.__class__.__name__
        cls = self.resolve_noderef(cls_or_name)
        parent = cls(**kwargs)
        parent.tokens.extend(args)
        parent.append(self, related)
        return parent

    def descend(self, cls_or_name=None, *args, **kwargs):
        '''Create a new node, set it as a child of this node and return it.
        '''
        cls_or_name = cls_or_name or self.__class__.__name__
        cls = self.resolve_noderef(cls_or_name)
        child = cls(**kwargs)
        if hasattr(child, 'tokens'):
            child.tokens.extend(args)
        return self.append(child)

    def descend_path(self, *cls_or_name_seq):
        '''Descend along the specifed path.
        '''
        this = self
        for cls_or_name in cls_or_name_seq:
            this = this.descend(cls_or_name)
        return this

    def swap(self, cls_or_name=None, *args, **kwargs):
        '''Swap cls(*args, **kwargs) for this node and make this node
        it's child.
        '''
        cls_or_name = cls_or_name or self.__class__.__name__
        cls = self.resolve_noderef(cls_or_name)
        new_parent = self.parent.descend(cls, *args, **kwargs)
        self.parent.remove(self)
        new_parent.append(self)
        return new_parent

    # -----------------------------------------------------------------------
    # Readability functions.
    # -----------------------------------------------------------------------
    def pprint(self, offset=0):
        print(offset * ' ', '- ', self)
        for child in self.children:
            child.pprint(offset + 2)

    def pformat(self, offset=0, buf=None):
        buf = buf or []
        buf.extend([offset * ' ', '- ', repr(self), '\n'])
        for child in self.children:
            child.pformat(offset + 2, buf)
        return ''.join(buf)

    #------------------------------------------------------------------------
    # Querying methods.
    #------------------------------------------------------------------------
    def getroot(self):
        this = self
        while hasattr(this, 'parent'):
            this = this.parent
        return this

    def depth_first(self):
        yield self
        for child in self.children:
            for node in child.depth_first():
                yield node

    def has_siblings(self):
        parent = getattr(self, 'parent', None)
        if parent is None:
            return
        return len(parent.children) > 1

    def following_siblings(self):
        parent = getattr(self, 'parent', None)
        if parent is None:
            return
        return iter(parent.children[self.index()])

    def preceding_siblings(self):
        '''Iterate over preceding siblings from nearest to farthest.
        '''
        parent = getattr(self, 'parent', None)
        if parent is None:
            return
        return reversed(parent.children[:self.index()])

    def preceding_sibling(self):
        try:
            return next(self.preceding_siblings())
        except StopIteration:
            return

    def ancestors(self):
        this = self
        while True:
            try:
                parent = this.parent
            except AttributeError:
                return
            else:
                yield parent
            this = parent

    def get_nodekey(self):
        '''This method enables subclasses to customize the
        behavior of ``find`` and ``find_one``. The default
        implementation uses the name of the class.
        '''
        return self.__class__.__name__

    @iterdict_filter
    def find(self, nodekey=None):
        '''Nodekey must be a string.
        '''
        for node in self.depth_first():
            if nodekey is not None:
                if node.get_nodekey() == nodekey:
                    yield node
                else:
                    continue
            else:
                yield node

    def find_one(self, nodekey):
        '''Find the only child matching the criteria.
        '''
        for node in self.find(nodekey):
            return node

    #------------------------------------------------------------------------
    # Serialization methods.
    #------------------------------------------------------------------------
    def _children_to_data(children):
        return [kid.to_data() for kid in children]

    @classmethod
    def fqname(cls):
        return '%s.%s' % (cls.__module__, cls.__name__)

    _serialization_meta = (
        dict(alias='type', attr='fqname'),
        dict(attr='children', to_data=_children_to_data),
        )

    def to_data(self):
        '''Render out this object as a json-serializable dictionary.
        '''
        data = dict(data=dict(self))
        serialization_meta = getattr(self, 'serialization_meta', [])
        for meta in self._serialization_meta + tuple(serialization_meta):
            attr = meta['attr']
            alias = meta.get('alias', attr)
            to_data = meta.get('to_data')
            value = getattr(self, attr)
            if callable(value):
                value = value()
            if to_data is not None:
                value = to_data(value)
            data[alias] = value
        return data

    @classmethod
    def fromdata(cls, data, default_node_cls=None, nodespace=None):
        # Figure out what node_cls to use.
        if default_node_cls is None:
            type_ = data.get('type')
            if type_ is not None:
                node_cls = resolve_name(str(type_))
            else:
                node_cls = cls
        else:
            node_cls = default_node_cls

        node = node_cls(data['data'])

        # Add the children.
        children = []
        for child in data.get('children', []):
            child = cls.fromdata(child)
            node.append(child)

        # Add any other attrs marked for inclusion by the class def.
        for meta in cls._serialization_meta + tuple(cls.serialization_meta):
            meta = dict(meta)
            if meta.get('alias') == 'type':
                continue
            if meta['attr'] == 'children':
                continue
            fromdata = meta.get('fromdata')

            attr = meta['attr']
            alias = meta.get('alias', attr)
            val = data[alias]
            if fromdata is not None:
                val = fromdata(val)
            object.__setattr__(node, attr, val)

        # Postdeserialize hook, just in case.
        post_deserialize = getattr(node_cls, 'post_deserialize', None)
        if post_deserialize is not None:
            post_deserialize(node)

        return node

    @classmethod
    def from_fp(cls, fp):
        '''Load from an open file protocol object.
        '''
        data = json.load(fp)
        return cls.fromdata(data)

    @classmethod
    def load(cls, filename):
        with open(filename) as f:
            return self.from_fp(f)

    #------------------------------------------------------------------------
    # Random utils.
    #------------------------------------------------------------------------
    @CachedAttr
    def uuid(self):
        '''Just a convenience for quickly generating uuid4's. The built-in
        ``id`` function is probably more idiomatic for most purposes.
        '''
        return str(uuid.uuid4())


def new_basenode(*bases):
    '''Create a new base node type with its own distinct nodespace.
    This provides a way to reuse node names without name conflicts in the
    metaclass cache.
    '''
    return type('Node', bases, {})


Node = new_basenode(BaseNode)


