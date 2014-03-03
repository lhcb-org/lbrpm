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
import optparse
import re
import sys
from string import Template

log = logging.getLogger()
log.setLevel(logging.INFO)

#CONTAINER_LIST = [ "pytools", "pygraphics", "pyanalysis"]
#LCGNAME = "LCG"
#IGNORE_PKG = [ "yoda", "herwig++", "lhapdf6", "sherpa", "soqt", "pygsi",
#               "CORAL", "rivet", "COOL", "crmc", "professor", "RELAX", "rivet2", "qwt",
#               "agile", "hepmcanalysis", "minuit", "mctester", "hydjet++", "ROOT", "LCGCMT" ]

CONTAINER_LIST = [  ]
LCGNAME = "LCG"
IGNORE_PKG = [ "numpy", "setuptools", "lhapdfsets", "sip" ]


# Class representing a RPM
###############################################################################
class Rpm(object):
    """ Base class representing a RPM used to generate all the data related """
    def __init__(self, lcgcmt_version, name, version, config, dirname, hash, hat = None):
        self.lcgcmt_version = lcgcmt_version
        self.name = name
        self.version = version
        self.config = config
        self.hat = hat
        self.dirname = dirname
        self.hash = hash
        self.namehash = name + "-" + hash
        self.deps = list()
        self.dict = None
        self.getRPMName = self.getHashRPMName
        self.isMetaRPM = False
        self.namewithhat = os.path.join(*self.dirname.split(os.sep)[:-2])

    def getLCGRPMName(self):
        """ returns the RPM name, including the LCG version """
        pre = self.name
        if self.hat != None:
            pre = self.hat + "_" + self.name

        post = (self.version + "_" + self.config).replace("-", "_")
        return LCGNAME + "_" + self.lcgcmt_version + "_" + pre + "_" + post
    
    def getHashRPMName(self):
        """ Get the name of the RPM including the unique hash"""
        pre = self.namehash
        if self.hat != None:
            pre = self.hat + "_" + self.namehash
        post = (self.version + "_" + self.config).replace("-", "_")
        return pre + "_" + post

    def getRPMVersion(self):
        return "1.0.0"

    def getSourcePathWithLCG(self):
        ''' Location in the LCG Install area '''
        #return os.path.join(LCGNAME +"_" + self.lcgcmt_version, self.dirname , self.version, self.config)
        return os.path.join(LCGNAME +"_" + self.lcgcmt_version, self.dirname)

    def getSourcePath(self):
        ''' Location in the LCG Install area '''
        return self.dirname

    def getTargetPath(self):
        ''' Location to which is should go after install '''
        return os.path.join(self.namewithhat, self.version + "-" + self.hash, self.config)

    def getTargetLCGCMTPath(self):
        ''' Location to which is should go iafter install '''
        return os.path.join(LCGNAME +"_" + self.lcgcmt_version, self.namewithhat, self.version)

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

    def getInstallCommands(self, lcg_path):
        """ Prepares the list of installation command used to prepare the package """
        spec =  "mkdir -p ${RPM_BUILD_ROOT}%s/%s\n" % (lcg_path,  self.getTargetPath())
        spec += "rsync -ar %%{LCGCMTROOT}/%s/* ${RPM_BUILD_ROOT}%s/%s\n" % \
            (self.getSourcePath(), lcg_path, self.getTargetPath())
        return spec

    def getFiles(self, lcg_path):
        """ Prepares the files part for the SPEC for this package """
        rpm_files = "\n%%files -n  %s\n" % (self.getRPMName())
        rpm_files += "%defattr(-,root,root)\n"
        rpm_files += "%s/%s\n" % (lcg_path, self.getTargetPath())
        rpm_files += "\n"
        return rpm_files

    def prepareRPMPackage(self):
        """ Prepare the package entry of this package to be
        inserted in the global SPEC file """
        rpm_packages = Template("""
%package -n $n
Version:$v
Group:LCG
Summary: LCG $n $v
AutoReqProv: no
""").substitute(n=self.getRPMName(), v=self.getRPMVersion(), )
        # Now adding the list of Provides for this package
        rpm_packages += "Provides: %s = %s\n" % (self.name, self.version)

        # Now adding the list of requirements
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


# Class representing a RPM containing the links to the installed version
###############################################################################
class RpmLink(Rpm):
    """ Base class representing a RPM used to generate all the data related
    XXX To be implemented """
    
    def __init__(self, lcgcmt_version, name, version, config, dirname, hash, hat = None):
        self.realName = name
        super(RpmLink, self).__init__(lcgcmt_version, name, version, config, dirname, hash, hat)
        self.getRPMName = self.getLCGRPMName

    def getInstallCommands(self, lcg_path):
        """ Prepares the list of installation command used to prepare the package """
        linkpath = "${RPM_BUILD_ROOT}%s/%s" %  (lcg_path,  self.getTargetLCGCMTPath())
        rpm_common = "mkdir -p %s\n" % linkpath
        updircount = 3 + self.namewithhat.count("/")
        updir = []
        for i in range(updircount):
            updir.append('..')
        rpm_common += "cd %s &&  ln -s %s/%s\n" % (linkpath, "/".join(updir),  self.getTargetPath())
        return rpm_common

    def getFiles(self, lcg_path):
        """ Prepares the files part for the SPEC for this package """
        rpm_files = "\n%%files -n  %s\n" % (self.getRPMName())
        rpm_files += "%defattr(-,root,root)\n"
        rpm_files += "%s/%s\n" % (lcg_path, os.path.join(self.getTargetLCGCMTPath(), self.config))
        rpm_files += "\n"
        return rpm_files

    def prepareRPMPackage(self):
        """ Prepare the package entry of this package to be
        inserted in the global SPEC file """
        rpm_packages = Template("""
%package -n $n
Version:$v
Group:LCG
Summary: LCG $n $v
AutoReqProv: no
""").substitute(n=self.getRPMName(), v=self.getRPMVersion(), )
        # Now adding the list of Provides for this package
        rpm_packages += "Requires: %s\n" % self.getHashRPMName()
        # Now adding the list of requirements
        for d in self.dependencies:
            # First checking the data
            if dict == None:
                raise Exception("%s %s Looking up dependency %s but no dictionary available" % (self.getRPMName(), self.getRPMVersion(), d))
            # Looking up the rpm itself
            drpm = self.dict[d]
            if drpm == None:
                raise Exception("%s %s Looking up dependency %s but not in dictionary" % (self.getRPMName(), self.getRPMVersion(), d))
            rpm_packages += "Requires: %s\n" % drpm.getLCGRPMName()
        return rpm_packages


# Class representing a RPM containing all the links to the installed version
###############################################################################
class LCGRpm(object):
    """ Base class representing a RPM containing the installed version of LCG with all links
    to installed packages """
    def __init__(self, lcgcmt_version, config):
        self.lcgcmt_version = lcgcmt_version
        self.name = "LCG"
        self.config = config
        self.deps = list()
        self.dict = None
        self.isMetaRPM = True
        
    def getRPMName(self):
        pre = self.name + "Link"
        post = (self.lcgcmt_version + "_" + self.config).replace("-", "_")
        return pre + "_" + post

    def getRPMVersion(self):
        return "1.0.0"

    def getTargetPath(self):
        ''' Location to which is should go after install '''
        return self.name + '_' + self.lcgcmt_version

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
Summary: LCG $n $v
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
def loadLCGMetaData(filename):
    """ Load the JSON file and check the basic structure """
    # First loading the JSON
    with open(filename) as inputfile:
        inputdata = inputfile.readlines()

    packages = {}
    for line in inputdata:
        if re.match("^\s*PLATFORM:", line) or re.match("^\s*VERSION:", line):
            continue
        
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
        (name, hash, version, dirname, deps) = line.split(";")
        name = name.strip()
        hash = hash.strip()
        version = version.strip()
        dirname = dirname.strip()
        namehash = name + "-" + hash
        #log.debug((namehash, name, version, hash, dirname, deps))
        pdata = {}
        pdata['name'] = name
        pdata['namehash'] = namehash
        pdata['hash'] = hash
        pdata['version'] = version
        pdata['dirname'] = dirname
        pdata['dependencies'] = [ e.strip() for e in deps.strip().split(",") if e != "" ]
        packages[name] = pdata
        log.debug(pdata)
        
    data = {}
    data['packages'] = packages

    return  data

# Reading LCGCMT version and platform from file
###############################################################################
def loadLCGCMTVersionPlatform(filename):
    """ Load the JSON file and check the basic structure """
    # First loading the JSON
    with open(filename) as inputfile:
        inputdata = inputfile.readlines()

    platform = None
    version = None
    for line in inputdata:
        m = re.match("^\s*PLATFORM:\s*([a-zA-Z0-9_\-]*)", line)
        if m != None:
            platform = m.group(1)

        m = re.match("^\s*VERSION:\s*([a-zA-Z0-9_\-]*)", line)
        if m != None:
            version = m.group(1)

        if version != None and platform != None:
            break
    log.debug("Platform: %s, Version: %s" % (platform, version))
    return (platform, version)

# Remove container and clean dependencies
###############################################################################
def fixLCGCMTData(data):
    """ Convert the file to something useable by LCGCMT users """

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
            if len([ip for ip in IGNORE_PKG if d.startswith(ip)]) > 0:
                continue
            newdeps.append(d)

        # Copying and fixing deps
        newpack = copy.deepcopy(pack)
        newpack['dependencies'] = newdeps
        newpackages[newpack['name']] = newpack

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
        r = Rpm(lcgcmt_version, name, version , platform, dirname, d['hash'])
        r.dependencies = list(d["dependencies"])
        r.dict = rpmDict
        rpmDict[k] = r

        log.debug("Adding link package " + name + " " + version + " type:" + deptype)
        l = RpmLink(lcgcmt_version, name, version , platform, dirname, d['hash'])
        l.dependencies = list(d["dependencies"])
        l.dict = rpmDict
        rpmDict[l.name + "link" ] = l

    log.debug("All packages added")

    # Adding meta package with links
    # deps = packagesMap.keys()
    # r = LCGRpm(lcgcmt_version, platform) 
    # r.dependencies = deps
    # r.dict = rpmDict
    # rpmDict['LCGCMTLINK'] = r
    return rpmDict

# Class to build the SPEC itself
#############################################################
class RpmSpec(object):
    """ Class presenting the whole LCG spec """
    def __init__(self, version, platform, filename, lcg_dir, rpmroot, packageType, mainLCGFilename):
        """ Initialize with the list of RPMs """
        self.lcgcmt_version = version
        self.lcgcmt_cmtconfig = platform
        self.lcg_prefix = lcg_dir
        # Externals or generators
        self.packageType = packageType
        # Same info as boolean, easier to deal with later on...
        self.isMainLCG = (packageType == "externals")

        # Now loading the stuff
        tmpdata = loadLCGMetaData(filename)
        self.rpmToBuild = tmpdata["packages"].keys()
        if not self.isMainLCG:
            # Then load it too
            log.info("Load Main LCG file: %s",  mainLCGFilename)
            lcgdata = loadLCGMetaData(mainLCGFilename)
            lcgpack = lcgdata["packages"]

            # Merging the two metadata fiels to check the dependencies
            for p in lcgpack.values():
                tmpdata["packages"][p["name"]] = p
            
        self.data = fixLCGCMTData(tmpdata)
        self.rpmDict = prepareRPMDict(self.data, self.lcgcmt_version,
                                      self.lcgcmt_cmtconfig)

        # Limit the list to the original list
        self.rpmList = [ v for v in self.rpmDict.values() if v.name in self.rpmToBuild]
        
        #topdir = "/scratch/z5/rpmbuild"
        #tmpdir = "/scratch/z5/tmpbuild"
        #rpmtmp = "/scratch/z5/tmp"
        #myroot = "/home/opt/build"

        myroot =  rpmroot
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

        self.buildroot = os.path.join(self.tmpdir, "LCGCMT-%s-%s-buildroot" % \
                                      (self.lcgcmt_version, self.lcgcmt_cmtconfig))
        if not os.path.exists(self.buildroot):
            os.makedirs(self.buildroot)

        self.externaldir = os.path.join(self.buildroot, "opt", "lhcb", "lcg", "external")
        self.appreleasesdir = os.path.join(self.buildroot, "opt", "lhcb", "lcg", "app", "releases")

    def getLCGPath(self):
        """ Path for the installed files on the target system """
        return "/opt/lcg"

    def getHeader(self):
        """ Build the SPEC Header """
        # Ugly, should do this better
        projectName = "LGC"
        if type == "generators":
            projectName = "LCG_generators"
            
        rpm_header = Template("""
%define project $projectName
%define lbversion $rpmver
%define cmtconfig $rpmconfig
%define LCGCMTROOT $lcg_prefix

%define cmtconfig_rpm %( echo %{cmtconfig} | tr '-' '_' )
%define rpmversion %{lbversion}_%{cmtconfig_rpm}

%define _topdir $topdir
%define tmpdir $tmpdir
%define _tmppath $rpmtmp
%define debug_package %{nil}
%global __os_install_post /usr/lib/rpm/check-buildroot

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
Prefix: /opt
Provides: /bin/sh

""").substitute(rpmver=self.lcgcmt_version, rpmconfig=self.lcgcmt_cmtconfig, \
                topdir=self.topdir, tmpdir=self.tmpdir, rpmtmp=self.rpmtmp,
                lcg_prefix=self.lcg_prefix, projectName=projectName)
        return rpm_header

# RPM requiremenst for the whole package
#############################################################

    def getRequires(self):
        rpm_requires = ""
        for name in set([ r.getLCGRPMName() for r in  self.rpmList]):
            rpm_requires += "Requires: %s\n" % name
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
            if r.isMetaRPM:
                continue
            rpm_common += r.getInstallCommands(self.getLCGPath())
            if not os.path.exists(os.path.join(self.lcg_prefix, r.getSourcePath() )):
                log.debug("MISSING: " + os.path.join(self.lcg_prefix, r.getSourcePath() ))

        # rpm_common += "\n# Building the LCGCMT directory with links\n"         
        # for r in self.rpmList:
        #     if r.isMetaRPM:
        #         continue
        #     linkpath = "${RPM_BUILD_ROOT}%s/%s" %  (self.getLCGPath(),  r.getTargetLCGCMTPath())
        #     rpm_common += "mkdir -p %s\n" % linkpath
        #     updircount = 3 + r.namewithhat.count("/")
        #     updir = []
        #     for i in range(updircount):
        #         updir.append('..')
        #     rpm_common += "cd %s &&  ln -s %s/%s\n" % (linkpath, "/".join(updir),  r.getTargetPath())
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
            rpm_files += r.getFiles(self.getLCGPath())
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


# Main method
#############################################################
def getLCGParamsFromFileName(filename):
    """ Parse the filename to extract LCG information"""
    log.debug("Processing file %s" % filename)
    lcg_dir = os.path.realpath(os.path.dirname(filename))
    filename =  os.path.basename(filename)
    log.debug("LCG dir: %s" % lcg_dir)
    log.debug("Filename: %s" % filename)

    import re
    type = None
    cmtconfig = None
    m = re.match("^LCG_([a-zA-Z0-9]+)_(.*).txt$", filename)
    if m != None:
        type = m.group(1)
        cmtconfig = m.group(2)
        log.debug("Type: %s" % type)
        log.debug("platform: %s" % cmtconfig)

    # Trying to derive version from parent filename
    parentdirname =  os.path.basename(lcg_dir)
    version = None
    m2 = re.match("^LCG_(.*)$", parentdirname)
    if m2 != None:
        version = m2.group(1)
        log.debug("version: %s" % version)

    return (lcg_dir, filename, type, cmtconfig, version)


# Get Main LCG file name
#############################################################
def getMainLCGFileName(filename, version, platform):
    """ For generators, find main LCG file name,
    called LCG_externals_<platform>.txt"""
    lcg_dir = os.path.realpath(os.path.dirname(filename))
    return os.path.join(lcg_dir, "LCG_externals_%s.txt" % platform)


# Main method
#############################################################
def usage(cmd):
    """ Prints out how to use the script... """
    cmd = os.path.basename(cmd)
    return """\n%(cmd)s [options] LCG_description_filename

    Prepare the SPEC file for a LCG release

    """ % { "cmd" : cmd }

# Main method
#############################################################
if __name__ == '__main__':
    # Setting logging 
    logging.basicConfig(stream=sys.stderr)

    # Parsing options
    parser = optparse.OptionParser(sys.argv[0])
    parser.add_option('-d', '--debug',
                      dest="debug",
                      default=False,
                      action="store_true",
                      help="Show debug information")
    parser.add_option('-v', '--version',
                      dest="version",
                      default=None,
                      action="store",
                      help="Force LCG version")
    parser.add_option('-p', '--platform',
                      dest="platform",
                      default=None,
                      action="store",
                      help="Force platform")
    parser.add_option('-l', '--lcgdir',
                      dest="lcgdir",
                      default=None,
                      action="store",
                      help="Force LCG dir if different from the one containing the config file")
    parser.add_option('-b', '--buildroot',
                      dest="buildroot",
                      default="/tmp",
                      action="store",
                      help="Force build root")
    parser.add_option('-g', '--generators',
                      dest="generators",
                      default=False,
                      action="store_true",
                      help="Build generators instead of LCG")
    parser.add_option('-o', '--output',
                      dest="output",
                      default = None,
                      action="store",
                      help="File name for the generated specfile [default output to stdout]")
    parser.add_option('-m', '--mainLCGFile',
                      dest="mainLCGFile",
                      default=None,
                      action="store",
                      help="Specify the main LCG file, when building the generators")

    opts, args = parser.parse_args(sys.argv)

    if len(args) != 2:
        parser.error("Please specify at least the file name")

    if opts.debug:
        log.setLevel(logging.DEBUG)
        
    input_filename = args[1]
    if not os.path.exists(input_filename):
        print "File: %s does NOT exist" % input_filename
        sys.exit(1)

    # Parsing info from filename
    (fileLCGDir, filename, filenameType, filenamePlatform, filenameVersion) = getLCGParamsFromFileName(input_filename)
    (filePlatform, fileVersion) = loadLCGCMTVersionPlatform(input_filename)

    # The build root (default /tmp)
    rpmroot = opts.buildroot

    # Now selecting the parameters, either from options or from the parameters passed
    # Options override what was derived from the file name
    lcg_dir = fileLCGDir
    if opts.lcgdir != None:
        lcg_dir = opts.lcgdir

    types = ["externals", "generators" ]
    type = "externals"
    if filenameType != None and filenameType in types:
        type = filenameType
    if opts.generators:
        type = "generators"

    platform = filenamePlatform
    if filePlatform != None:
        platform = filePlatform
    if opts.platform != None:
        platform = opts.platform

    version = filenameVersion
    if fileVersion != None:
        version = fileVersion
    if opts.version != None:
        version = opts.version

    log.info("Processing %s" % input_filename)
    log.info("LCG Version: %s" % version)
    log.info("Platform: %s" % platform)
    log.info("Package type: %s" % type)
    log.info("LCG dir: %s" % lcg_dir)
    log.info("Build root: %s" % rpmroot)

    # Check if we build the externals or generators
    mainLCGFileName = None
    if type != "externals":
        if opts.mainLCGFile:
            mainLCGFileName = opts.mainLCGFile
        else:
            mainLCGFileName = getMainLCGFileName(input_filename, version, platform)
        
    
    spec = RpmSpec(version, platform, input_filename, lcg_dir, rpmroot, type, mainLCGFileName)

    if opts.output:
        with open(opts.output, "w") as outputfile:
            outputfile.write(spec.getSpec())
    else:
        print spec.getSpec()

