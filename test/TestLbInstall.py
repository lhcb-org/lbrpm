'''
Created on Aug 6, 2012

@author: Ben Couturier
'''
import os
import unittest
from lb_install import InstallProjectClient, LbInstallClient


class Test(unittest.TestCase):


    def testOptsBinary(self):
        parser = InstallProjectClient().parser
        opts, args = parser.parse_args(["--binary=xbin"]) #@UnusedVariable
        self.assertEquals(opts.binary, "xbin")

    def testOptsBinaryShort(self):
        parser = InstallProjectClient().parser
        opts, args = parser.parse_args(["-b"]) #@UnusedVariable
        self.assertTrue(opts.useCMTCONFIG)

    def testArgParsing(self):
        parser = InstallProjectClient().parser
        opts, args = parser.parse_args(["-b", "-d", "x", "titi", "toto"]) #@UnusedVariable
        self.assertTrue(opts.useCMTCONFIG)

    def testLbInstallClientBadCmd(self):
        client = LbInstallClient(["lbinstallcmd", "rpm", "testrpm"], True)
        rc = client.main()
        self.assertEquals(rc, 1)

    def testLbInstallClientRpm(self):
        client = LbInstallClient(["rpm", "-ivh", "testrpm"], True)
        rc = client.main()
        self.assertEquals(rc, 0)
        self.assertEquals(client.runMethod, "rpm")
        self.assertEquals(client.runArgs[0], "-ivh")
        self.assertEquals(client.runArgs[1], "testrpm")

    def testLbInstallClientList(self):
        client = LbInstallClient(["list", "BRUNEL"], True)
        rc = client.main()
        self.assertEquals(rc, 0)
        self.assertEquals(client.runMethod, "listpackages")
        self.assertEquals(client.runArgs[0], "BRUNEL")

    def testLbInstallClientInstallRpm(self):
        client = LbInstallClient(["install", "BRUNEL"], True)
        rc = client.main()
        self.assertEquals(rc, 0)
        self.assertEquals(client.runMethod, "installRpm")
        self.assertEquals(client.runArgs[0], "BRUNEL")

    def testInstallProjectClientBin(self):
        os.environ['CMTCONFIG'] = "MYCONFIG"
        client = InstallProjectClient(["-b", "BRUNEL"], True)
        rc = client.main()
        self.assertEquals(rc, 0)
        self.assertEquals(client.runMethod, "install")
        self.assertEquals(client.runArgs[0], "BRUNEL")
        self.assertEquals(client.runArgs[1], None)
        self.assertEquals(client.runArgs[2], "MYCONFIG")

    def testInstallProjectClientBadBin(self):
        del os.environ['CMTCONFIG']
        client = InstallProjectClient(["-b", "BRUNEL"], True)
        rc = client.main()
        self.assertEquals(rc, 1)
        # Should fail as env var isn't set

    def testInstallProjectClientCmdlineBin(self):
        os.environ['CMTCONFIG'] = "MYCONFIG"
        client = InstallProjectClient(["--binary=TOTO", "BRUNEL"], True)
        rc = client.main()
        self.assertEquals(rc, 0)
        self.assertEquals(client.runMethod, "install")
        self.assertEquals(client.runArgs[0], "BRUNEL")
        self.assertEquals(client.runArgs[1], None)
        self.assertEquals(client.runArgs[2], "TOTO")

    def testInstallProjectClientFullLine(self):
        os.environ['CMTCONFIG'] = "MYCONFIG"
        client = InstallProjectClient(["--binary=TOTO", "BRUNEL", "vXrY"], True)
        rc = client.main()
        self.assertEquals(rc, 0)
        self.assertEquals(client.runMethod, "install")
        self.assertEquals(client.runArgs[0], "BRUNEL")
        self.assertEquals(client.runArgs[1], "vXrY")
        self.assertEquals(client.runArgs[2], "TOTO")

    def testInstallProjectClientNobin(self):
        os.environ['CMTCONFIG'] = "MYCONFIG"
        client = InstallProjectClient(["BRUNEL", "vXrY"], True)
        rc = client.main()
        self.assertEquals(rc, 0)
        self.assertEquals(client.runMethod, "install")
        self.assertEquals(client.runArgs[0], "BRUNEL")
        self.assertEquals(client.runArgs[1], "vXrY")
        self.assertEquals(client.runArgs[2], None)

        print client.runArgs



    def testConfigCreation(self):
        import tempfile
        import shutil
        tmpdir = tempfile.mkdtemp()
        # XXX

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testOptions']
    unittest.main()