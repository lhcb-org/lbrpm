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

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

local_directory = os.path.dirname(__file__).strip()
os.environ['PATH'] =  os.pathsep.join([os.environ['PATH'], local_directory])

# Util method to prepare the build area
################################################################################
def checkBuildAra(ba):

    if not os.path.exists(ba):
        os.makedirs(ba)

    basdirs = [ 'rpmbuild', 'tmpbuild', 'tmp' ]
    for s in basdirs:
        tmp = os.path.join(ba, s)
        if not os.path.exists(tmp):
            os.makedirs(tmp)

    rpmbuild =  os.path.join(ba, 'rpmbuild')
    sdirs = [ 'SOURCES', 'RPMS', 'BUILD', 'SRPMS' ]
    for s in sdirs:
        tmp = os.path.join(rpmbuild, s)
        if not os.path.exists(tmp):
            os.makedirs(tmp)

# Checking arguments
################################################################################
def usage():
    print >> sys.stderr, "Usage: %s project version" % sys.argv[0]
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


maxarg = len(args)
if  maxarg < 2:
    print >> sys.stderr, "Missing arguments!"
    usage()

# We allow the hat and package name to be passed separated by
# spaces, this makes scripts invoking simpler in some cases
project = args[0].upper()
orig_project = args[0]
version = args[1]
cmtconfig = ''

if len(args) > 2:
    cmtconfig = args[2]

useVersion = options.useVersion

# Forcing for LbScripts
log.info("Creating RPM for <%s> <%s>" % (project, version))


buildarea = options.buildarea
release = options.release
checkBuildAra(buildarea)
log.info("Using build area: %s" % buildarea)

# Parsing version
################################################################################

maj_version = 1
min_version = 0
patch_version = 0

(lhcb_maj_version, lhcb_min_version, lhcb_patch_version) = RpmHelpers.parseVersion(version)

if useVersion:
    m = re.match("v([\d]+)r([\d]+)$", version)
    if m != None:
        maj_version = m.group(1)
        min_version = m.group(2)
    else:
        # Checking whether the version matches vXrYpZ in that case
        m = re.match("v([\d]+)r([\d]+)p([\d]+)", version)
        if m != None:
            maj_version = m.group(1)
            min_version = m.group(2)
            patch_version = m.group(3)
        else:
            log.error("Version %s does not match format vXrY pr vXryPZ" % version)


# Now preparing rpmbuild command
################################################################################
def addDefine(param, val):
    if val == None or val == '':
        val = '""'
    return " --define '%s %s' " % (param, val)

cmd = "rpmbuild -v"
cmd += addDefine("build_area", buildarea)
cmd += addDefine("project", project)
cmd += addDefine("orig_project", orig_project)
cmd += addDefine("lbversion", version)
cmd += addDefine("release", release)
cmd += addDefine("maj_version", maj_version)
cmd += addDefine("min_version", min_version)
cmd += addDefine("patch_version", patch_version)
cmd += addDefine("packarch", "noarch")
cmd += addDefine("lhcb_maj_version", lhcb_maj_version)
cmd += addDefine("lhcb_min_version", lhcb_min_version)
cmd += addDefine("lhcb_patch_version", lhcb_patch_version)

cmd += " -bb " + os.path.join(local_directory, "LHCb_SourceProject.spectemplate")

log.info("Running: %s" % cmd)
rc = subprocess.call(cmd, shell=True)
sys.exit(rc)



