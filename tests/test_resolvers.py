import unittest

from treebie import Node


class ExampleNode(Node):
    pass


class TestLazyTypeCreation(unittest.TestCase):

    def test_correct_module(self):
        '''Assert dynamically created types get created in
        the calling scope.
        '''
        name = 'Cow'
        newtype = Node().descend(name)
        self.assertEqual(newtype.__class__.__module__, __name__)

    def test_correct_scope(self):
        '''Dynamically create nodes should be in the global scope.
        '''
        name = 'Cow'
        newtype = Node().descend(name)
        self.assertIn(name, globals())
        self.assertNotIn(name, locals())


class TestLazyImport(unittest.TestCase):

    def test_import_works(self):
        '''Verify that the resolved name points to this module's TestNode.
        '''
        name = 'ExampleNode'
        newtype = Node().descend(name)
        self.assertIs(type(newtype), ExampleNode)
