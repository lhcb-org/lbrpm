#!/usr/bin/env python
"""
Script to create the LCGCMT RPM Spec file based on the JSON configuration produced by the build itself.
It printouts a spec file, which can be redirected to a file.

To produce the rpm themselves:
rpm -bb <specfile>


"""
import json
import os
import sys
from string import Template

# Class representing a RPM
###############################################################################
class Rpm(object):
    """ Base class representing a RPM used to generate all the data related """
    def __init__(self, lcgcmt_version, name, version, config, hat = None):
        self.lcgcmt_version = lcgcmt_version
        self.name = name
        self.version = version
        self.config = config
        self.hat = hat
        self.deps = list()
        self.dict = None

    def getRPMName(self):
        pre = self.name
        if self.hat != None:
            pre = self.hat + "_" + self.name

        post = (self.version + "_" + self.config).replace("-", "_")
        return "LCGCMT_" + self.lcgcmt_version + "_" + pre + "_" + post

    def getRPMVersion(self):
        return "1.0.0"

    def getDiskPath(self):
        return os.path.join("LCGCMT_" + self.lcgcmt_version, self.name, self.version, self.config)


    def __str__(self):
        strg = "RPM: %s-%s\n" % (self.getRPMName(), self.getRPMVersion())
        return strg

    def prepareRPMDescription(self):
        """ Prepare the description of this package to be
        inserted in the global SPEC file """
        rpm_desc = """
%%description -n  %s
%s %s
""" % (self.getRPMName(), self.getRPMName(), self.getRPMVersion())
        return rpm_desc

    def prepareRPMPackage(self):
        """ Prepare the package entry of this package to be
        inserted in the global SPEC file """
        rpm_packages = Template("""
%package -n $n
Version:$v
Group:LCG
Summary: LCGCMT $n $v
AutoReqProv: no
""").substitute(n=self.getRPMName(), v=self.getRPMVersion(), )
        for d in self.dependencies:
            # First checking the data
            if dict == None:
                raise Exception("%s %s Looking up dependency %s but no dictionary available" % (self.getRPMName(), self.getRPMVersion(), d))
            # Looking up the rpm itself
            drpm = self.dict[d]
            if drpm == None:
                raise Exception("%s %s Looking up dependency %s but not in dictionary" % (self.getRPMName(), self.getRPMVersion(), d))
            rpm_packages += "Requires: %s\n" % drpm.getRPMName()
        return rpm_packages



# Directory configuration
###############################################################################
def loadLCGCMTJSON(filename):
    """ Load the JSON file and check the basic structure """
    # First loading the JSON
    with open(filename) as json_file:
    #    data = json.load(json_file)
        data = eval(json_file.read())

    # Now checking that it has at least
    required = ['packages', 'description']
    for r in required:
        if r not in data.keys():
            raise Exception("Missing entry %s in JSON file", r)

    version = data['description']['version']
    platform = data['description']['platform']

    if version == None or platform == None:
        raise Exception("Missing data in JSON: version:%s, Platform: %s" % (version, platform))

    return (version, platform, data)

def prepareRPMDict(data):
    """ Extract a list of RPM Objects based on the LCGCMT packages """
    lcgcmt_version = data["description"]["version"]
    platform = data["description"]["platform"]
    rpmDict= dict()
    packagesMap = data['packages']
    for k, d in packagesMap.items():
        name = d["dest_name"]
        version = d["version"]
        if not name:
            print >> sys.stderr,  "Missing name for key: %s" % k
            name = k
        print >> sys.stderr, "Adding package " + name + " " + version
        r = Rpm(lcgcmt_version, name, version , platform)
        r.dependencies = list(d["dependencies"])
        r.dict = rpmDict
        rpmDict[k] = r
    return rpmDict

# Class to build the SPEC itself
#############################################################

class RpmSpec(object):

    def __init__(self, jsonFile):
        """ Initialize with the list of RPMs """
        (self.lcgcmt_version, self.lcgcmt_cmtconfig, self.data) = loadLCGCMTJSON(jsonFile)
        self.rpmDict = prepareRPMDict(self.data)
        self.rpmList = self.rpmDict.values()

        #topdir = "/scratch/z5/rpmbuild"
        #tmpdir = "/scratch/z5/tmpbuild"
        #rpmtmp = "/scratch/z5/tmp"

        myroot = "/tmp"
        self.topdir = "%s/rpmbuild" % myroot
        self.tmpdir = "%s/tmpbuild" % myroot
        self.rpmtmp = "%s/tmp" % myroot

        self.srcdir = os.path.join(self.topdir, "SOURCES")
        self.rpmsdir =  os.path.join(self.topdir, "RPMS")
        self.srpmsdir =  os.path.join(self.topdir, "SRPMS")
        self.builddir =  os.path.join(self.topdir, "BUILD")

        for d in [self.srcdir, self.rpmsdir, self.srpmsdir, self.builddir]:
            if not os.path.exists(d):
                os.makedirs(d)


        self.buildroot = os.path.join(self.tmpdir, "LCGCMT-%s-%s-buildroot" % (self.lcgcmt_version, self.lcgcmt_cmtconfig))
        if not os.path.exists(self.buildroot):
            os.makedirs(self.buildroot)

        self.externaldir = os.path.join(self.buildroot, "opt", "lhcb", "lcg", "external")
        self.appreleasesdir = os.path.join(self.buildroot, "opt", "lhcb", "lcg", "app", "releases")

    def getLCGPath(self):
        """ Path for the installed files on the target system """
        return "/opt/lcg"

    def getHeader(self):
        """ Build the SPEC Header """
        rpm_header = Template("""
%define project LCGCMT
%define lbversion $rpmver
%define cmtconfig $rpmconfig
%define LCGCMTROOT /afs/cern.ch/sw/lcg/experimental/

%define cmtconfig_rpm %( echo %{cmtconfig} | tr '-' '_' )
%define rpmversion %{lbversion}_%{cmtconfig_rpm}

%define _topdir $topdir
%define tmpdir $tmpdir
%define _tmppath $rpmtmp
%define debug_package %{nil}

Name: %{project}_%{rpmversion}
Version: 1.0.0
Release: 1
Vendor: LHCb
Summary: %{project}
License: GPL
Group: LCG
Source0: %{url}
BuildRoot: %{tmpdir}/%{project}-%{lbversion}-%{cmtconfig}-buildroot
BuildArch: noarch
AutoReqProv: no
Prefix: /opt/lhcb
Provides: /bin/sh

""").substitute(rpmver=self.lcgcmt_version, rpmconfig=self.lcgcmt_cmtconfig, \
                topdir=self.topdir, tmpdir=self.tmpdir, rpmtmp=self.rpmtmp)
        return rpm_header

# RPM requiremenst for the whole package
#############################################################

    def getRequires(self):
        rpm_requires = ""
        #for r in rpmList:
        #    rpm_requires += "Requires: %s\n" % (r.getRPMName())
        return rpm_requires

# RPM Package section
#############################################################

    def getPackages(self):
        rpm_packages = ""
        for r in self.rpmList:
            rpm_packages += r.prepareRPMPackage()
        return rpm_packages

# RPM Description section
#############################################################

    def getDescriptions(self):
        rpm_desc = """
%description
%{project} %{lbversion}

"""
        for r in self.rpmList:
            rpm_desc += r.prepareRPMDescription()
        return rpm_desc

# RPM Common section with build
#############################################################

    def getCommon(self):
        rpm_common = """
%prep

%build

%install

cd %_topdir/SOURCES

[ -d ${RPM_BUILD_ROOT} ] && rm -rf ${RPM_BUILD_ROOT}

/bin/mkdir -p ${RPM_BUILD_ROOT}/opt/lhcb/lcg
if [ $? -ne 0 ]; then
  exit $?
fi

cd ${RPM_BUILD_ROOT}/opt/lhcb/lcg
"""
        for r in self.rpmList:
            path = r.getDiskPath()
            rpm_common += "mkdir -p ${RPM_BUILD_ROOT}/%s/%s\n" % (self.getLCGPath(),  path)
            rpm_common += "rsync -ar %%{LCGCMTROOT}/%s/%s/%s/* ${RPM_BUILD_ROOT}%s/%s\n" % (r.name, r.version, r.config, self.getLCGPath(), path)

        rpm_common += """

%post

%postun

%clean
"""
        return rpm_common

# RPM Files section
#############################################################

    def getFiles(self):
        rpm_files = """
%files

"""
        for r in self.rpmList:
            rpm_files += "\n%%files -n  %s\n" % (r.getRPMName())
            rpm_files += "%defattr(-,root,root)\n"
            rpm_files += "%s/%s\n" % (self.getLCGPath(), r.getDiskPath())
        rpm_files += "\n"
        return rpm_files

# RPM Trailer
#############################################################

    def getTrailer(self):
        rpm_trailer = """
%define date    %(echo `LC_ALL="C" date +"%a %b %d %Y"`)

%changelog

* %{date} User <ben.couturier..rcern.ch>
- first Version
"""
        return rpm_trailer


# Get the whole spec...
#############################################################

    def getSpec(self):
        """ Concatenate all the fragments """

        rpm_global = self.getHeader() \
        + self.getRequires() \
        + self.getPackages() \
        + self.getDescriptions() \
        + self.getCommon() \
        + self.getFiles() \
        + self.getTrailer()

        return rpm_global


if __name__ == '__main__':
    #json_filename = "/afs/cern.ch/user/h/hegner/public/dependencies.json"
    json_filename = "dependencies.json"
    spec = RpmSpec(json_filename)
    print spec.getSpec()

