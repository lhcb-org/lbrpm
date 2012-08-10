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

    def testParseRelDirPackageNoHat(self):
        builddir = "/afs/cern.ch/lhcb/software/releases/PARAM/ParamFiles/v8r7"
        (prefix, project, hat, package, version) = BuildDirHelpers.parsePackageBuildDirName(builddir)

        self.assertEquals(prefix, "/afs/cern.ch/lhcb/software/releases")
        self.assertEquals(project, "PARAM")
        self.assertEquals(hat, None)
        self.assertEquals(package, "ParamFiles")
        self.assertEquals(version, "v8r7")

    def testParseRelDirPackageHat(self):
        builddir = "/afs/cern.ch/lhcb/software/releases/DBASE/Det/SQLDDDB/v7r6"
        (prefix, project, hat, package, version) = BuildDirHelpers.parsePackageBuildDirName(builddir)

        self.assertEquals(prefix, "/afs/cern.ch/lhcb/software/releases")
        self.assertEquals(project, "DBASE")
        self.assertEquals(hat, "Det")
        self.assertEquals(package, "SQLDDDB")
        self.assertEquals(version, "v7r6")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()