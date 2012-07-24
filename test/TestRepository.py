'''
Created on Jul 23, 2012
@author: Ben Couturier
'''
import unittest
import xml.dom.minidom
from DependencyManager import Provides, Requires, Package, Repository

class TestRepository(unittest.TestCase):

    def setUp(self):
        # The repository is leaded directly from the XML at the end of this file
        self.repository = Repository()
        dom = xml.dom.minidom.parseString(repoxml)
        self.repository.loadYumMetadataDOM(dom)

    def tearDown(self):
        pass

    def testRepository(self):
        self.assertEqual(len(self.repository.mPackages["TestPackage"]), 3)

    def testPackageMatching(self):
        r = Requires("TestPackage", "1.0.0", "1", None, "EQ", None)
        p = self.repository.findPackageMatchingRequire(r)
        self.assertNotEqual(p, None)
        self.assertEqual(p.version, "1.0.0")

    def testPackageByNameWithRelease(self):
        p = self.repository.findPackageByName("TP2", "1.2.5", "1")
        self.assertNotEqual(p, None)
        self.assertEqual(p.version, "1.2.5")
        self.assertEqual(p.release, "1")

    def testPackageByNameWithoutRelease(self):
        p = self.repository.findPackageByName("TP2", "1.2.5", None)
        self.assertNotEqual(p, None)
        self.assertEqual(p.version, "1.2.5")
        self.assertEqual(p.release, "2")

    def testPackageByNameWithoutVersion(self):
        p = self.repository.findPackageByName("TP2", None, None)
        self.assertNotEqual(p, None)
        self.assertEqual(p.version, "1.2.5")
        self.assertEqual(p.release, "2")


    def testDependencyGreater(self):
        p = self.repository.findPackageByName("TP2", None, None)
        self.assertNotEqual(p, None)
        self.assertEqual(p.version, "1.2.5")
        self.assertEqual(p.release, "2")

        alldeps = p.getDependencies()
        self.assertEqual(1, len(alldeps))
        self.assertEqual(alldeps[0].name, "TestPackage")
        self.assertEqual(alldeps[0].version, "1.3.7")


    def testDependencyEqual(self):
        p = self.repository.findPackageByName("TP3", None, None)
        self.assertNotEqual(p, None)
        self.assertEqual(p.version, "1.18.22")
        self.assertEqual(p.release, "2")

        alldeps = p.getDependencies()
        alldeps = p.getDependencies()
        self.assertEqual(1, len(alldeps))
        self.assertEqual(alldeps[0].name, "TestPackage")
        self.assertEqual(alldeps[0].version, "1.2.5")

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

       <package type="rpm">
                <name>TP2</name>
                <arch>noarch</arch>
                <version epoch="0" ver="1.2.5" rel="1" />
                <checksum type="sha" pkgid="YES">23a7fad30c1f9e5a237fcf3894e62b6c2b6779a2
                </checksum>
                <summary>TP2</summary>
                <description>TP2</description>
                <packager />
                <url />
                <time file="1335446371" build="1335446369" />
                <size package="2033329" installed="12266535" archive="12418076" />
                <location href="TP2-1.2.5-1.noarch.rpm" />
                <format>
                        <rpm:license>GPL</rpm:license>
                        <rpm:vendor>LHCb</rpm:vendor>
                        <rpm:group>LHCb</rpm:group>
                        <rpm:buildhost>pclhcb95.cern.ch</rpm:buildhost>
                        <rpm:sourcerpm>TP2-1.2.5-1.src.rpm</rpm:sourcerpm>
                        <rpm:header-range start="280" end="92341" />
                        <rpm:provides>
                                <rpm:entry name="/bin/sh" />
                                <rpm:entry name="TP2" flags="EQ" epoch="0" ver="1.2.5"
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
                <name>TP2</name>
                <arch>noarch</arch>
                <version epoch="0" ver="1.2.5" rel="2" />
                <checksum type="sha" pkgid="YES">23a7fad30c1f9e5a237fcf3894e62b6c2b6779a2
                </checksum>
                <summary>TP2</summary>
                <description>TP2</description>
                <packager />
                <url />
                <time file="1335446371" build="1335446369" />
                <size package="2033329" installed="12266535" archive="12418076" />
                <location href="TP2-1.2.5-2.noarch.rpm" />
                <format>
                        <rpm:license>GPL</rpm:license>
                        <rpm:vendor>LHCb</rpm:vendor>
                        <rpm:group>LHCb</rpm:group>
                        <rpm:buildhost>pclhcb95.cern.ch</rpm:buildhost>
                        <rpm:sourcerpm>TP2-1.2.5-2.src.rpm</rpm:sourcerpm>
                        <rpm:header-range start="280" end="92341" />
                        <rpm:provides>
                                <rpm:entry name="/bin/sh" />
                                <rpm:entry name="TP2" flags="EQ" epoch="0" ver="1.2.5"
                                        rel="2" />
                        </rpm:provides>
                        <rpm:requires>
                                <rpm:entry name="TestPackage" flags="GE"
                                        epoch="0" ver="1.2.5" />
                                <rpm:entry name="rpmlib(CompressedFileNames)" flags="LE"
                                        epoch="0" ver="3.0.4" rel="1" pre="1" />
                                <rpm:entry name="/bin/sh" pre="1" />
                                <rpm:entry name="rpmlib(PayloadFilesHavePrefix)" flags="LE"
                                        epoch="0" ver="4.0" rel="1" pre="1" />
                        </rpm:requires>
                </format>
        </package>
       <package type="rpm">
                <name>TP3</name>
                <arch>noarch</arch>
                <version epoch="0" ver="1.18.22" rel="2" />
                <checksum type="sha" pkgid="YES">23a7fad30c1f9e5a237fcf3894e62b6c2b6779a2
                </checksum>
                <summary>TP3</summary>
                <description>TP3</description>
                <packager />
                <url />
                <time file="1335446371" build="1335446369" />
                <size package="2033329" installed="12266535" archive="12418076" />
                <location href="TP2-1.18.22-2.noarch.rpm" />
                <format>
                        <rpm:license>GPL</rpm:license>
                        <rpm:vendor>LHCb</rpm:vendor>
                        <rpm:group>LHCb</rpm:group>
                        <rpm:buildhost>pclhcb95.cern.ch</rpm:buildhost>
                        <rpm:sourcerpm>TP3-1.18.22-2.src.rpm</rpm:sourcerpm>
                        <rpm:header-range start="280" end="92341" />
                        <rpm:provides>
                                <rpm:entry name="/bin/sh" />
                                <rpm:entry name="TP3" flags="EQ" epoch="0" ver="1.18.22"
                                        rel="2" />
                        </rpm:provides>
                        <rpm:requires>
                                <rpm:entry name="TestPackage" flags="EQ"
                                        epoch="0" ver="1.2.5" />
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