'''
Created on Aug 6, 2012

@author: Ben Couturier
'''
import os
import unittest
from lb_install import InstallProjectClient, LbInstallClient


class Test(unittest.TestCase):


    def setUp(self):
        import tempfile
        self.siteroot=tempfile.mkdtemp()
        filename = os.path.join(os.path.dirname(__file__), "testyumrepo")
        self.repourl = "file://%s" % filename

    def tearDown(self):
        pass

    def testConfigCreation(self):
        args = ["--root=%s" % self.siteroot, "--repo=%s" % self.repourl, "list"]
        client = LbInstallClient(args)
        rc =  client.main()
        self.assertEquals(rc, 0)
        ia = client.installArea
        for path in [ ia.yumconf, ia.yumrepolhcb, ia.yumrepolcg]:
            self.assertTrue(os.path.exists(path))
        for path in ["contrib/CMT/v1r20p20090520/",
                     "lhcb/LBSCRIPTS/LBSCRIPTS_v7r1/",
                     "lhcb/COMPAT/COMPAT_v1r10/"]:
            self.assertTrue(os.path.exists(os.path.join(self.siteroot, path)))


    def testConfigListPackage(self):
        from cStringIO import StringIO
        import sys
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        args = ["--root=%s" % self.siteroot, "--repo=%s" % self.repourl, "list", "castor"]
        client = LbInstallClient(args)
        rc =  client.main()
        self.assertEquals(rc, 0)

        sys.stdout = old_stdout
        result = mystdout.getvalue().splitlines()
        self.assertEquals(result[0], "castor_2.1.9_9_x86_64_slc5_gcc43_opt-1.0.0-1")
        self.assertEquals(result[1], "Total Matching: 1")

    def testConfigInstallrpm(self):
        args = ["--root=%s" % self.siteroot, "--repo=%s" % self.repourl, "-d",  "install", "castor_2.1.9_9_x86_64_slc5_gcc43_opt"]
        client = LbInstallClient(args)
        rc =  client.main()
        self.assertEquals(rc, 0)
        for path in [ "lcg/external/castor/2.1.9-9/x86_64-slc5-gcc43-opt"]:
            self.assertTrue(os.path.exists(os.path.join(self.siteroot, path)))

    def testConfigInstallProjectInstall(self):
        args = ["--root=%s" % self.siteroot, "--repo=%s" % self.repourl, "Brunel", "v43r1p1"]
        client = InstallProjectClient(args)
        rc =  client.main()
        self.assertEquals(rc, 0)
        for path in [ "lhcb/BRUNEL/BRUNEL_v43r1p1"]:
            self.assertTrue(os.path.exists(os.path.join(self.siteroot, path)))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testOptions']
    unittest.main()