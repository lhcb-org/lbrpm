"""
Utility module, to filter/copy data from a release directory
"""

import logging
import os
import re

log = logging.getLogger()


def filterBuildDir(builddir, cmtconfig):
    """ Returns a list of all the files of interest for the chosen CMTCONFIG
    in the InstallArea of the directory """

    # Preparing the paths and checking their existence...
    rpath = os.path.realpath(builddir)
    installareadir = os.path.join(rpath, "InstallArea")
    confdir = os.path.join(installareadir, cmtconfig)
    if not os.path.exists(confdir):
        raise Exception("Could not find InstallArea/${CMTCONFIG} dir")

    # Now iterating on all subdirs of the config directory
    filelist = []
    for (dirpath, dirnames, filenames) in os.walk(confdir): #@UnusedVariable
        log.info("processing directory %s" %dirpath)
        for f in filenames:
            fullname = os.path.join(dirpath, f)
            if os.path.islink(fullname):
                filelist.append(fullname)
                filelist.append(os.path.realpath(fullname))
            else:
                filelist.append(fullname)

    return filelist


def parseBuildDirName(builddir):
    """ Split the build directory to extract project name """
    # First making sure we have a normalized path
    rpath = os.path.realpath(builddir)

    # Checking the length
    if len(rpath.split(os.sep)) < 2:
        raise Exception("Build dir must contain the PROJECT/PROJECT_VERSION part")

    # Getting the 2 levels above
    (tmp, version) = os.path.split(rpath)
    (prefix, project) = os.path.split(tmp)

    return (prefix, project, version)

# parse the params from the package structure:
# $LHCBRELEASES/PARAM/ParamFiles/v8r7
# $LHCBRELEASES/DBASE/Det/SQLDDDB/v7r6

def parsePackageBuildDirName(builddir):
    """ Split the build directory to extract project name """
    # First making sure we have a normalized path
    rpath = os.path.realpath(builddir)

    # Getting the 2 levels above
    (tmp, version) = os.path.split(rpath)
    (tmp, package) = os.path.split(tmp)
    hat = None
    (prefix, project) = os.path.split(tmp)
    if project not in ['DBASE', 'PARAM']:
        hat = project
        (prefix, project) = os.path.split(prefix)


    return (prefix, project, hat, package, version)


def listBuiltConfigs(builddir):
    """ List all CMTCONFIGS built in the release area """
    # First making sure we have a normalized path
    rpath = os.path.realpath(builddir)
    installareadir = os.path.join(rpath, "InstallArea")

    allconfigs = [f for f in os.listdir(installareadir)]
    return allconfigs


def findCMTRequirementFiles(builddir):
    """ Find all requirement files """

    # First making sure we have a normalized path
    rpath = os.path.realpath(builddir)

    filelist = []
    for (dirpath, dirnames, filenames) in os.walk(rpath):
        # twisted logic here: once we have found a cmt directory
        # we can avoid recursing the siblings as we are in a package.
        # EXCEPT in the to[p directory where there is
        # cmt/project.cmt....
        log.debug("Processing %s" % dirpath)
        if "cmt" in dirnames and dirpath != rpath:
            dirnames[:] = [ "cmt" ]
        else:
            for f in filenames:
                if f == "requirements":
                    filelist.append(os.path.join(dirpath, f))

    return filelist

def findCMTRequiredProjects(builddir):
    """ Find all requirement files """

    # First making sure we have a normalized path
    rpath = os.path.realpath(builddir)

    projectcmtname = os.path.join(rpath, "cmt", "project.cmt")

    allprojects = []
    f = open(projectcmtname, "r")
    for l in f.readlines():
        m = re.match("\s*use\s+([\w_]+)\s+([\w_\*]+)\s*", l)
        if m!= None:
            allprojects.append((m.group(1), m.group(2)))
    return allprojects

def findCMTRequiredPackages(builddir):
    """ Find all requirement files """

    # First making sure we have a normalized path
    rpath = os.path.realpath(builddir)

    filelist = findCMTRequirementFiles(rpath)
    allpackages = []
    for filename in filelist:
        log.info("Processing requirement file: %s" % filename)
        f = open(filename, "r")
        for l in f.readlines():
            m = re.match("\s*use\s+([\w_]+)\s+([\w_\*]+)\s*", l)
            if m!= None:
                allpackages.append((m.group(1), m.group(2)))
    return allpackages
