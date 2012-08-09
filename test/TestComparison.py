'''
Created on Jul 23, 2012
@author: Ben Couturier
'''
import unittest
from DependencyManager import Provides, Requires

class TestComparison(unittest.TestCase):

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
        p1 = Provides(name, "1.0.9.B", "2")
        p2 = Provides(name, "1.0.9.A", "1")
        p3 = Provides(name, "1.0.0", "1")
        p4 = Provides(name, "1.0.10.A", "1")

        allvers = [p4, p1, p2, p3]
        sortedvers = sorted(allvers)
        print sortedvers
        self.assertEqual(sortedvers[0], p3)
        self.assertEqual(sortedvers[1], p2)
        self.assertEqual(sortedvers[2], p1)
        self.assertEqual(sortedvers[3], p4)


    def testMatchEqual(self):
        name = "TestPackage"
        version1 = "1.0.1"
        version2 = "1.2.0"
        release = "2"
        release2 = "3"

        # Checking equality
        p1 = Provides(name, version1, release)
        r = Requires(name, version1, release, 0, "EQ", None)
        self.assertTrue(r.provideMatches(p1), "%s should match %s" % (p1, r))

        # Checking release mismatch
        p2 = Provides(name, version1, release2)
        self.assertFalse(r.provideMatches(p2), "%s should not match %s" % (p2, r))

        # Checking version mismatch
        p3 = Provides(name, version2, release)
        self.assertFalse(r.provideMatches(p3), "%s should not match %s" % (p3, r))

        # Checking version mismatch
        p4 = Provides(name + "Toto", version1, release)
        self.assertFalse(r.provideMatches(p4), "%s should not match %s" % (p4, r))

    def testGreater(self):
        name = "TestPackage"
        version1 = "1.0.1"
        version2 = "1.2.0"
        version3 = "1.3.5"

        release = "2"

        # Checking simple comparison
        p1 = Provides(name, version1, release)
        p2 = Provides(name, version2, release)
        p3 = Provides(name, version3, release)

        ctor = "GT"
        r = Requires(name, version2, release, 0, ctor, None)

        self.assertFalse(r.provideMatches(p1), "%s not %s %s" % (p1, ctor, r))
        self.assertFalse(r.provideMatches(p2), "%s not %s %s" % (p2, ctor, r))
        self.assertTrue(r.provideMatches(p3), "%s %s %s" % (p3, ctor, r))

        ctor = "GE"
        r = Requires(name, version2, release, 0, ctor, None)
        self.assertFalse(r.provideMatches(p1), "%s not %s %s" % (p1, ctor, r))
        self.assertTrue(r.provideMatches(p2), "%s %s %s" % (p2, ctor, r))
        self.assertTrue(r.provideMatches(p3), "%s %s %s" % (p3, ctor, r))

    def testLower(self):
        name = "TestPackage"
        version1 = "1.0.1"
        version2 = "1.2.0"
        version3 = "1.3.5"

        release = "2"

        # Checking simple comparison
        p1 = Provides(name, version1, release)
        p2 = Provides(name, version2, release)
        p3 = Provides(name, version3, release)

        ctor = "LT"
        r = Requires(name, version2, release, 0, ctor, None)

        self.assertTrue(r.provideMatches(p1), "%s %s %s" % (p1, ctor, r))
        self.assertFalse(r.provideMatches(p2), "%s not %s %s" % (p2, ctor, r))
        self.assertFalse(r.provideMatches(p3), "%s not %s %s" % (p3, ctor, r))

        ctor = "LE"
        r = Requires(name, version2, release, 0, ctor, None)
        self.assertTrue(r.provideMatches(p1), "%s %s %s" % (p1, ctor, r))
        self.assertTrue(r.provideMatches(p2), "%s %s %s" % (p2, ctor, r))
        self.assertFalse(r.provideMatches(p3), "%s not %s %s" % (p3, ctor, r))

    def testRequireWithNoVersion(self):
        name = "TestPackage"
        version1 = "1.0.1"
        release = "2"

        # Checking simple comparison
        p1 = Provides(name, version1, release)

        r = Requires(name, None, None)

        self.assertTrue(r.provideMatches(p1))

    def testDifferentName(self):
        name = "TestPackage"
        version1 = "1.0.1"
        release = "2"

        # Checking simple comparison
        p1 = Provides(name, version1, release)

        r = Requires(name + "Toto", None, None)

        self.assertFalse(r.provideMatches(p1))

    def testOrderDifferentName(self):
        name = "TestPackage"
        version1 = "1.0.1"
        release = "2"

        # Checking simple comparison
        p1 = Provides(name, version1, release)
        p2 = Provides(name+"z",version1, release)
        self.assertTrue(p1 < p2)


if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestComparison.testProvidesComparisonAlpha']
    unittest.main()