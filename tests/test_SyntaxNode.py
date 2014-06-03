import unittest

from treebie.syntaxnode import SyntaxNode as Node


class TestDictFeatures:

    def test_eq(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)

        n2 = Node(a=1, b=2, c=3)
        n2.descend('Test1', x=1, y=2, z=3)
        assert n1 == n2

    def test_ne(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)
        n2 = Node(a=1, b=2, c=3)
        n2.descend('Test1', x=1, y=2, z=4)
        assert n1 != n2

    def test_clone_eq(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)
        assert n1 == n1.clone()

    def test_clone_ne(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)
        n2 = n1.clone(cow='moo')
        assert n1 != n2


class TestSyntaxHelpers:

    def test_popstate(self):
        '''Popstate is just a helper that returns the target's parent.
        '''
        parent = Node()
        child = parent.descend('Child1')
        assert child.popstate() is parent

    def test_extend(self):
        node = Node()
        assert not node.tokens
        items = [(1, 2, 3), (4, 5, 6)]
        node.tokens.extend(items)
        assert node.tokens == items

    def test_first(self):
        items = [(1, 2, 3), (4, 5, 6)]
        node = Node().descend('Child1', *items)
        assert node.first() == items[0]
