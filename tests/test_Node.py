import unittest

from treebie import Node


class TestDictFeatures(unittest.TestCase):

    def test_eq(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)

        n2 = Node(a=1, b=2, c=3)
        n2.descend('Test1', x=1, y=2, z=3)
        # self.assertEqual(n1, n2)

    def test_ne(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)
        n2 = Node(a=1, b=2, c=3)
        n2.descend('Test1', x=1, y=2, z=4)
        self.assertNotEqual(n1, n2)

    def test_clone_eq(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)
        self.assertEqual(n1, n1.clone())

    def test_clone_ne(self):
        n1 = Node(a=1, b=2, c=3)
        n1.descend('Test1', x=1, y=2, z=3)
        n2 = n1.clone(cow='moo')
        self.assertNotEqual(n1, n2)
