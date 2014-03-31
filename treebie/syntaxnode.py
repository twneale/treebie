from tater.core.tokentype import Token



class BaseSyntaxNode(BaseNode):

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
            raise ParseError(msg % (self, stream))

    @classmethod
    def parse(cls_or_inst, itemiter, **options):
        '''Supply a user-defined start class.
        '''
        itemstream = ItemStream(itemiter)

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
    def extend(self, *items):
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

    #------------------------------------------------------------------------
    # Serialization methods.
    #------------------------------------------------------------------------
    @classmethod
    def fromdata(cls, data, namespace=None):
        '''
        namespace: is a dict containing all the required
        ast nodes to reconstitute this object.

        json_data: is the nested dict structure.
        '''
        if namespace is None:
            class NameSpace(dict):
                def __missing__(self, cls_name):
                    # This can probably be replaced by recent code to gerenate
                    # ananymous types.
                    cls = type(str(cls_name), (Node,), {})
                    self[cls_name] = cls
                    return cls
            namespace = NameSpace()

        node_cls = namespace[data['type']]
        items = []
        for pos, token, text in data['tokens']:
            items.append((pos, Token.fromstring(token), text))
        node = node_cls(*items)
        children = []
        for child in data.get('children', []):
            child = cls.fromdata(child, namespace)
            child.parent = node
            children.append(child)
        node.children = children
        if 'ctx' in data:
            node.ctx.update(data['ctx'])
        if 'local_ctx' in data:
            node._local_ctx = data['local_ctx']

        return node

SyntaxNode = new_basenode(BaseSyntaxNode)
