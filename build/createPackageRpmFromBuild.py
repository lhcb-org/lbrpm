#!/usr/bin/env python
"""
Command to convert a LHCb project tar ball in a RPM file
"""

import logging
import os
import subprocess
import sys
import RpmHelpers
import BuildDirHelpers

__RCSID__ = "$Id"

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

local_directory = os.path.dirname(__file__).strip()
os.environ['PATH'] =  os.pathsep.join([os.environ['PATH'], local_directory])

# Util method to prepare the command
################################################################################
def addDefine(param, val):
    """ Util method to add a define statement"""
    if val == None or val == '':
        val = '""'
    return " --define '%s %s' " % (param, val)


# Checking arguments
################################################################################
def usage():
    """ Display help"""
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

# Getting the release dir
releasedir = args[0]
(prefix, tmpproject, hat, package, version) = BuildDirHelpers.parsePackageBuildDirName(releasedir)

log.info("Processing <%s><%s><%s><%s>" % (tmpproject, hat, package, version))

project = tmpproject.upper()
orig_project = tmpproject
orig_package = package

versiondir = os.path.join(project, orig_package)
if hat != None:
    orig_package = package
    package = hat + "_" + orig_package
    versiondir = os.path.join(project, hat, orig_package)

buildarea = options.buildarea
release = options.release
RpmHelpers.checkBuildAra(buildarea)
log.info("Using build area: %s" % buildarea)

# Setting version
################################################################################
(lhcb_maj_version, lhcb_min_version, lhcb_patch_version) = RpmHelpers.parseVersion(version)
(maj_version, min_version, patch_version) = RpmHelpers.parseVersion(version)

cmd = "rpmbuild -v"
cmd += addDefine("releasedir", releasedir)
cmd += addDefine("build_area", buildarea)
cmd += addDefine("project", project)
cmd += addDefine("hat", hat)
cmd += addDefine("package", package)
cmd += addDefine("alias1", package.upper().replace("_", "/"))
cmd += addDefine("alias2", orig_package.upper())
cmd += addDefine("lbversion", version)
cmd += addDefine("maj_version", maj_version)
cmd += addDefine("min_version", min_version)
cmd += addDefine("patch_version", patch_version)
cmd += addDefine("release", release)
cmd += addDefine("versiondir", versiondir)
cmd += " -bb " + os.path.join(local_directory, "LHCb_BuiltDataPackage.spectemplate")

log.info("Running: %s" % cmd)
rc = subprocess.call(cmd, shell=True)


