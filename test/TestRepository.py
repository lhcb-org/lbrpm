'''
Created on Jul 23, 2012
@author: Ben Couturier
'''
import unittest
import xml.dom.minidom
from DependencyManager import Provides, Requires, Package, Repository

class TestRepository(unittest.TestCase):

    def setUp(self):
        self.repository = Repository()
        dom = xml.dom.minidom.parseString(repoxml)
        self.repository.loadYumMetadataDOM(dom)
 
    def tearDown(self):
        pass

    def testRepository(self):
        self.assertEqual(len(self.repository.mPackages["TestPackage"]), 3)
        r = Requires("TestPackage", "1.0.0", "1", None, "EQ", None)
        p = self.repository.findPackageMatchingRequire(r)
        self.assertNotEqual(p, None)
        self.assertEqual(p.version, "1.0.0")
        
        
repoxml = """<?xml version="1.0" encoding="UTF-8"?>
<metadata xmlns="http://linux.duke.edu/metadata/common"
        xmlns:rpm="http://linux.duke.edu/metadata/rpm" packages="177">
        <package type="rpm">
                <name>TestPackage</name>
                <arch>noarch</arch>
                <version epoch="0" ver="1.0.0" rel="1" />
                <checksum type="sha" pkgid="YES">23a7fad30c1f9e5a237fcf3894e62b6c2b6779a2
                </checksum>
                <summary>TestPackage</summary>
                <description>TestPackage</description>
                <packager />
                <url />
                <time file="1335446371" build="1335446369" />
                <size package="2033329" installed="12266535" archive="12418076" />
                <location href="TestPackage-1.0.0-1.noarch.rpm" />
                <format>
                        <rpm:license>GPL</rpm:license>
                        <rpm:vendor>LHCb</rpm:vendor>
                        <rpm:group>LHCb</rpm:group>
                        <rpm:buildhost>pclhcb95.cern.ch</rpm:buildhost>
                        <rpm:sourcerpm>TestPackage-1.0.0-1.src.rpm</rpm:sourcerpm>
                        <rpm:header-range start="280" end="92341" />
                        <rpm:provides>
                                <rpm:entry name="/bin/sh" />
                                <rpm:entry name="TestPackage" flags="EQ" epoch="0" ver="1.0.0"
                                        rel="1" />
                        </rpm:provides>
                        <rpm:requires>
                                <rpm:entry name="rpmlib(CompressedFileNames)" flags="LE"
                                        epoch="0" ver="3.0.4" rel="1" pre="1" />
                                <rpm:entry name="/bin/sh" pre="1" />
                                <rpm:entry name="rpmlib(PayloadFilesHavePrefix)" flags="LE"
                                        epoch="0" ver="4.0" rel="1" pre="1" />
                        </rpm:requires>
                </format>
        </package>
        
        <package type="rpm">
                <name>TestPackage</name>
                <arch>noarch</arch>
                <version epoch="0" ver="1.2.5" rel="1" />
                <checksum type="sha" pkgid="YES">23a7fad30c1f9e5a237fcf3894e62b6c2b6779a2
                </checksum>
                <summary>TestPackage</summary>
                <description>TestPackage</description>
                <packager />
                <url />
                <time file="1335446371" build="1335446369" />
                <size package="2033329" installed="12266535" archive="12418076" />
                <location href="TestPackage-1.2.5-1.noarch.rpm" />
                <format>
                        <rpm:license>GPL</rpm:license>
                        <rpm:vendor>LHCb</rpm:vendor>
                        <rpm:group>LHCb</rpm:group>
                        <rpm:buildhost>pclhcb95.cern.ch</rpm:buildhost>
                        <rpm:sourcerpm>TestPackage-1.2.5-1.src.rpm</rpm:sourcerpm>
                        <rpm:header-range start="280" end="92341" />
                        <rpm:provides>
                                <rpm:entry name="/bin/sh" />
                                <rpm:entry name="TestPackage" flags="EQ" epoch="0" ver="1.2.5"
                                        rel="1" />
                        </rpm:provides>
                        <rpm:requires>
                                <rpm:entry name="rpmlib(CompressedFileNames)" flags="LE"
                                        epoch="0" ver="3.0.4" rel="1" pre="1" />
                                <rpm:entry name="/bin/sh" pre="1" />
                                <rpm:entry name="rpmlib(PayloadFilesHavePrefix)" flags="LE"
                                        epoch="0" ver="4.0" rel="1" pre="1" />
                        </rpm:requires>
                </format>
        </package>

        <package type="rpm">
                <name>TestPackage</name>
                <arch>noarch</arch>
                <version epoch="0" ver="1.3.7" rel="1" />
                <checksum type="sha" pkgid="YES">23a7fad30c1f9e5a237fcf3894e62b6c2b6779a2
                </checksum>
                <summary>TestPackage</summary>
                <description>TestPackage</description>
                <packager />
                <url />
                <time file="1335446371" build="1335446369" />
                <size package="2033329" installed="12266535" archive="12418076" />
                <location href="TestPackage-1.3.7-1.noarch.rpm" />
                <format>
                        <rpm:license>GPL</rpm:license>
                        <rpm:vendor>LHCb</rpm:vendor>
                        <rpm:group>LHCb</rpm:group>
                        <rpm:buildhost>pclhcb95.cern.ch</rpm:buildhost>
                        <rpm:sourcerpm>TestPackage-1.3.7-1.src.rpm</rpm:sourcerpm>
                        <rpm:header-range start="280" end="92341" />
                        <rpm:provides>
                                <rpm:entry name="/bin/sh" />
                                <rpm:entry name="TestPackage" flags="EQ" epoch="0" ver="1.3.7"
                                        rel="1" />
                        </rpm:provides>
                        <rpm:requires>
                                <rpm:entry name="rpmlib(CompressedFileNames)" flags="LE"
                                        epoch="0" ver="3.0.4" rel="1" pre="1" />
                                <rpm:entry name="/bin/sh" pre="1" />
                                <rpm:entry name="rpmlib(PayloadFilesHavePrefix)" flags="LE"
                                        epoch="0" ver="4.0" rel="1" pre="1" />
                        </rpm:requires>
                </format>
        </package>


</metadata>
"""


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testProvidesComparison']
    unittest.main()