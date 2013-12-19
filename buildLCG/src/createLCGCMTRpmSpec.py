#!/usr/bin/env python
"""
Script to create the LCGCMT RPM Spec file based on the JSON configuration produced by the build itself.
It printouts a spec file, which can be redirected to a file.

To produce the rpm themselves:
rpm -bb <specfile>


"""
import copy
import logging
import os
import re
import sys
from string import Template

log = logging.getLogger()
log.setLevel(logging.DEBUG)

CONTAINER_LIST = [ "pytools", "pygraphics", "pyanalysis"]
LCGNAME = "LCG"
IGNORE_PKG = [ "yoda", "herwig++" ]

# Class representing a RPM
###############################################################################
class Rpm(object):
    """ Base class representing a RPM used to generate all the data related """
    def __init__(self, lcgcmt_version, name, version, config, dirname, hat = None):
        self.lcgcmt_version = lcgcmt_version
        self.name = name
        self.version = version
        self.config = config
        self.hat = hat
        self.dirname = dirname
        self.deps = list()
        self.dict = None

    def getRPMName(self):
        pre = self.name
        if self.hat != None:
            pre = self.hat + "_" + self.name

        post = (self.version + "_" + self.config).replace("-", "_")
        return LCGNAME + "-" + self.lcgcmt_version + "_" + pre + "_" + post

    def getRPMVersion(self):
        return "1.0.0"

    def getDiskPath(self):
        return os.path.join(LCGNAME +"-" + self.lcgcmt_version, self.dirname , self.version, self.config)

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
    with open(filename) as inputfile:
        inputdata = inputfile.readlines()

    packages = {}
    for line in inputdata:
        # Parse the file
        # Ignore commments
        if re.match("^\s*#", line):
            logging.debug("Found comment: %s" % line)
            continue
        # Look for specific compiler line
        if re.match("^\s*COMPILER", line):
            logging.debug("Found COMPILER: %s" % line)
            continue
        # Parse proper line
        # name-hash; package name; version; hash; full directory name; comma separated dependencies
        (namehash, name, version, hash, dirname, deps) = line.split(";")
        #log.debug((namehash, name, version, hash, dirname, deps))
        pdata = {}
        pdata['name'] = name
        pdata['namehash'] = namehash
        pdata['hash'] = hash
        pdata['version'] = version
        pdata['dirname'] = dirname
        pdata['dependencies'] = [ e for e in deps.strip().split(",") if e != "" ]
        packages[namehash] = pdata
        log.debug(pdata)
        
    data = {}
    data['packages'] = packages

    return  data

# Remove container and clean dependencies
###############################################################################
def fixLCGCMTData(data):
    """ Convert the file to something usebale by LCGCMT users """

    packages = data["packages"]

    # Check which directories are used several times
    # usecount = dict()
    # for k in packages.values():
    #     dirname = k['dirname']
    #     usecount[dirname] = usecount.get(dirname, 0) + 1
    # for k in  usecount.keys():
    #     print "%s   -> %d" % (k, usecount[k])
    # containers = [ k for k in usecount.keys() if usecount[k] > 1 ]
    # print containers

    newpackages = dict()
    for pack in packages.values():
        name = pack["name"]
        version = pack["version"]
        dirname = pack["dirname"]

        # Ignoring packages contained in a container
        if (name != dirname and dirname in CONTAINER_LIST) \
               or name in IGNORE_PKG:
            log.debug("Ignoring package " + name + " " + version + " in " + dirname)
            continue
        
        # Now filtering the dependencies
        log.debug("Filtering deps for " + name + " " + version + " in " + dirname)
        deps =  pack["dependencies"]
        newdeps = []
        for d in deps:
            log.debug("Identifying dependency: %s" % d)
            dpack = packages[d]
            if dpack['dirname'] in CONTAINER_LIST:
                continue
            if len([ip for ip in IGNORE_PKG if d.startswith(ip)]) > 0:
                continue
            newdeps.append(d)

        # Copying and fixing deps
        newpack = copy.deepcopy(pack)
        newpack['dependencies'] = newdeps
        newpackages[newpack['namehash']] = newpack

    newdata = dict()
    newdata['packages'] = newpackages
    log.debug("Finished fixing the dependencies")
    return newdata
        
def prepareRPMDict(data, lcgcmt_version, platform):
    """ Extract a list of RPM Objects based on the LCGCMT packages """
    rpmDict= dict()
    packagesMap = data['packages']
    for k, d in packagesMap.items():
        name = d["name"]
        version = d["version"]
        dirname = d["dirname"]
        if not name:
            log.error("Missing name for key: %s" % k)
            name = k
        # Doublechecking...
        deptype = "NORMAL"
        if name != dirname \
           and dirname in CONTAINER_LIST:
            #log.debug("Ignoring package " + name + " " + version + " in " + dirname)
            deptype = "SUBDEP"
        log.debug("Adding package " + name + " " + version + " type:" + deptype)
        r = Rpm(lcgcmt_version, name, version , platform, dirname)
        r.dependencies = list(d["dependencies"])
        r.dict = rpmDict
        rpmDict[k] = r
    log.debug("All packages added")
    return rpmDict

# Class to build the SPEC itself
#############################################################

class RpmSpec(object):

    def __init__(self, version, platform, filename):
        """ Initialize with the list of RPMs """
        self.lcgcmt_version = version
        self.lcgcmt_cmtconfig = platform
        tmpdata = loadLCGCMTJSON(filename)
        self.data = fixLCGCMTData(tmpdata)
        self.rpmDict = prepareRPMDict(self.data, self.lcgcmt_version,
                                      self.lcgcmt_cmtconfig)
        self.rpmList = self.rpmDict.values()

        #topdir = "/scratch/z5/rpmbuild"
        #tmpdir = "/scratch/z5/tmpbuild"
        #rpmtmp = "/scratch/z5/tmp"

        myroot = "/home/opt/build"
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
            rpm_common += "rsync -ar %%{LCGCMTROOT}/%s/* ${RPM_BUILD_ROOT}%s/%s\n" % (path, self.getLCGPath(), path)

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
    logging.basicConfig(stream=sys.stderr)
    version = sys.argv[1]
    platform = sys.argv[2]
    input_filename = sys.argv[3]
    log.debug("processing %s" % input_filename)
    spec = RpmSpec(version, platform, input_filename)
    print spec.getSpec()

