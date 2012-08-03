#!/usr/bin/env python
"""
Command to convert a LHCb project tar ball in a RPM file
"""

import logging
import os
import re
import subprocess
import sys
import RpmHelpers
import BuildDirHelpers
from LbConfiguration.Package import getPackage

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

local_directory = os.path.dirname(__file__).strip()
os.environ['PATH'] =  os.pathsep.join([os.environ['PATH'], local_directory])

# Util method to prepare the command
################################################################################
def addDefine(param, val):
    if val == None or val == '':
        val = '""'
    return " --define '%s %s' " % (param, val)


# Checking arguments
################################################################################
def usage():
    print >> sys.stderr, "Usage: %s releasedir" % sys.argv[0]
    sys.exit(2)

from optparse import OptionParser
parser = OptionParser()
parser.add_option("--versioned", dest="useVersion", action="store_true",
                  help="Parse version and set it in the RPM instead of using it in the name",
                  metavar="VERSION", default = False)
parser.add_option("--buildarea", dest="buildarea", action="store",
                  help="Location where the RPM is build",
                  default = "/tmp/buildarea")
parser.add_option("--release", dest="release", action="store",
                  help="Release number",
                  default = "0")

(options, args) = parser.parse_args()

if  len(args) < 1:
    print >> sys.stderr, "Missing arguments!"
    usage()

# We allow the hat and package name to be passed separated by
# spaces, this makes scripts invoking simpler in some cases
releasedir = args[0]

(prefix, tmpproject, pversion) = BuildDirHelpers.parseBuildDirName(releasedir)
version = pversion.replace(tmpproject + "_", "")

log.info("Processing <%s> <%s>" % (tmpproject, version))

project = tmpproject.upper()
orig_project = tmpproject
useVersion = options.useVersion

# Forcing for LbScripts
if project.upper() == "LBSCRIPTS":
    useVersion = True

buildarea = options.buildarea
release = options.release
RpmHelpers.checkBuildAra(buildarea)
log.info("Using build area: %s" % buildarea)



# Setting version
################################################################################
maj_version = 1
min_version = 0
patch_version = 0

if useVersion:
    (maj_version, min_version, patch_version) = RpmHelpers.parseVersion(version)

allconfigs = BuildDirHelpers.listBuiltConfigs(releasedir)
log.info("Found following CMTCONFIGS built: %s" % ",".join(allconfigs))
allconfigs = ["x86_64-slc5-gcc43-opt"]

for cmtconfig in allconfigs:


    cmd = "rpmbuild -v"
    cmd += addDefine("releasedir", releasedir)
    cmd += addDefine("build_area", buildarea)
    cmd += addDefine("project", project)
    cmd += addDefine("orig_project", orig_project)
    cmd += addDefine("lbversion", version)
    cmd += addDefine("release", release)
    cmd += addDefine("orig_config", cmtconfig)
    if cmtconfig != '':
        cmd += addDefine("config", "_" + cmtconfig)
    else:
        cmd += addDefine("config",  cmtconfig)
    cmd += addDefine("maj_version", maj_version)
    cmd += addDefine("min_version", min_version)
    cmd += addDefine("patch_version", patch_version)
    cmd += addDefine("packarch", "noarch")

    cmd += " -bb " + os.path.join(local_directory, "LHCb_BuiltProject.spectemplate")

    log.info("Running: %s" % cmd)
    rc = subprocess.call(cmd, shell=True)
    #sys.exit(rc)



