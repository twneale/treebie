import pytest

from treebie import Node
from treebie.chainmap import ChainMap
from treebie.exceptions import ChainMapUsageError


class TestChainMap:

    def test__init__(self):
        node = Node()
        node.ctx['a'] = 1
        child = node.descend('Child')
        newmap = ChainMap(inst=child)
        assert newmap['a'] == 1

    def test__get__(self):
        node = Node()
        assert node.ctx.inst is node
        assert node.ctx._inst is node

    def test_inst_error(self):
        with pytest.raises(ChainMapUsageError):
            inst = ChainMap().inst

    def test_maps(self):
        parent = Node()
        child = parent.descend('Child')
        assert list(child.ctx.maps) == [child.ctx.map] + list(parent.ctx.maps)

    def test_root(self):
        parent = Node()
        assert parent.ctx is parent.ctx.root

        ancestor = parent.descend_path("Child", "Grandchild")
        assert parent.ctx is ancestor.ctx.root

    def test__delitem__(self):
        parent = Node()
        child = parent.descend('Child')
        parent.ctx['a'] = 1
        del parent.ctx['a']

    def test__len__(self):
        parent = Node()
        child = parent.descend('Child')
        parent.ctx['a'] = 1
        child.ctx['b'] = 2
        assert len(child.ctx) is 2

    def test__iter__(self):
        parent = Node()
        child = parent.descend('Child')
        parent.ctx['a'] = 1
        child.ctx['b'] = 2
        assert list(child.ctx) == list(child.ctx.map) + list(parent.ctx)

    def test__contains__(self):
        parent = Node()
        child = parent.descend('Child')
        parent.ctx['a'] = 1
        child.ctx['b'] = 2

        assert 'a' in parent.ctx
        assert 'a' in child.ctx
        assert 'b' in child.ctx
        assert 'b' not in parent.ctx

    def test__repr__(self):
        parent = Node()
        child = parent.descend('Child')
        parent.ctx['a'] = 1
        child.ctx['b'] = 2
        assert repr(child.ctx) == "{'b': 2} -> {'a': 1}"
