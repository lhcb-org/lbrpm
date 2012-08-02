'''
Created on Aug 1, 2012

@author: Ben Couturier
'''
import unittest
import BuildDirHelpers

class Test(unittest.TestCase):
    """ Various tests for the BuildDirHelpers """

    def testSimple(self):
        builddir = "/afs/cern.ch/lhcb/software/releases/REC/REC_v14r1p1"
        (prefix, project, version) = BuildDirHelpers.parseBuildDirName(builddir)


        self.assertEquals(prefix, "/afs/cern.ch/lhcb/software/releases")
        self.assertEquals(project, "REC")
        self.assertEquals(version, "REC_v14r1p1")


    def testDotsinDir(self):
        builddir = "/afs/cern.ch/lhcb/software/releases/REC/REC_v14r1p1/../REC_v14r1p1"
        (prefix, project, version) = BuildDirHelpers.parseBuildDirName(builddir)

        self.assertEquals(prefix, "/afs/cern.ch/lhcb/software/releases")
        self.assertEquals(project, "REC")
        self.assertEquals(version, "REC_v14r1p1")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()