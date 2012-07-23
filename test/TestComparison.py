'''
Created on Jul 23, 2012

@author: Ben Couturier
'''
import unittest
from DependencyManager import Provides

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testProvidesComparison(self):
        name = "TestPackage"
        p1 = Provides(name, "1.0.1", "2")
        p2 = Provides(name, "1.0.1", "1")
        p3 = Provides(name, "1.0.0", "1")

        allvers = [p1, p2, p3]
        sortedvers = sorted(allvers)
        self.assertEqual(sortedvers[0], p3)
        self.assertEqual(sortedvers[1], p2)
        self.assertEqual(sortedvers[2], p1)

    def testProvidesComparisonNoRelease(self):
        name = "TestPackage"
        p1 = Provides(name, "1.0.1", None)
        p2 = Provides(name, "1.0.1", "1")
        p3 = Provides(name, "1.0.0", "1")

        allvers = [p1, p2, p3]
        sortedvers = sorted(allvers)

        self.assertEqual(sortedvers[0], p3)
        self.assertEqual(sortedvers[1], p1)
        self.assertEqual(sortedvers[2], p2)

    def testProvidesComparisonAlpha(self):
        name = "TestPackage"
        p1 = Provides(name, "1.0.1.B", "2")
        p2 = Provides(name, "1.0.1.A", "1")
        p3 = Provides(name, "1.0.0", "1")

        allvers = [p1, p2, p3]
        sortedvers = sorted(allvers)
        print sortedvers
        self.assertEqual(sortedvers[0], p3)
        self.assertEqual(sortedvers[1], p2)
        self.assertEqual(sortedvers[2], p1)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testProvidesComparison']
    unittest.main()